"""Compare cv2 vs ffmpeg-pipe backends across realistic access patterns.

Metrics per run:
    wall_s          - time.perf_counter delta
    cpu_self_s      - resource.getrusage(RUSAGE_SELF)  utime+stime delta
    cpu_child_s     - resource.getrusage(RUSAGE_CHILDREN) utime+stime delta
    peak_rss_mb     - highest observed RSS during the run, self + all children
    frames          - frames actually returned by the backend
    fps             - frames / wall_s

CPU-child is essential for the ffmpeg backend: the decoder runs in a
subprocess, so its work would be invisible if we only measured RUSAGE_SELF.

peak_rss_mb is sampled from /proc/{pid}/status at 10ms intervals by a
background thread. ru_maxrss can't be used here because it's a
high-water mark of the process, so it stays flat after the first run
that touched ffmpeg and understates memory in later runs.

Each scenario runs REPEATS times; we report the median of wall_s and the
max of peak_rss_mb, plus min/max wall_s so the spread is visible.

Scenarios exercise the same paths that VideoWriter uses:
    sequential      - read every frame in order (dominant case: rendering)
    strided         - read every 3rd frame (speed>1 subclip)
    reverse         - read frames in reverse (worst case for ffmpeg-pipe)
    random_seek     - 200 random accesses (worst case for both)
    near_sequential - +1..+4 forward jumps (uses the small-jump fast path)

The AV1 fixture is expected to fail for the cv2 backend on systems without
AV1 hardware acceleration. That failure is reported, not treated as an
error - it's the whole point of the comparison.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import random
import resource
import statistics
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backends import BACKENDS  # noqa: E402

HERE = Path(__file__).resolve().parent
FIXTURES_DIR = HERE / "fixtures"
OUTPUT_DIR = HERE / "output"

REPEATS = 2
RANDOM_ACCESSES = 100
NEAR_SEQ_ACCESSES = 100


@dataclass
class RunResult:
    wall_s: float
    cpu_self_s: float
    cpu_child_s: float
    peak_rss_mb: float
    frames: int
    valid: bool  # False if decoded frames look empty (all zeros)


@dataclass
class ScenarioResult:
    scenario: str
    backend: str
    codec: str
    runs: list[RunResult] = field(default_factory=list)

    @property
    def median_wall_s(self) -> float:
        return statistics.median(r.wall_s for r in self.runs)

    @property
    def min_wall_s(self) -> float:
        return min(r.wall_s for r in self.runs)

    @property
    def max_wall_s(self) -> float:
        return max(r.wall_s for r in self.runs)

    @property
    def median_cpu_total_s(self) -> float:
        return statistics.median(r.cpu_self_s + r.cpu_child_s for r in self.runs)

    @property
    def peak_rss_mb(self) -> float:
        return max(r.peak_rss_mb for r in self.runs)

    @property
    def median_fps(self) -> float:
        return statistics.median(r.frames / r.wall_s if r.wall_s > 0 else 0.0 for r in self.runs)

    @property
    def all_valid(self) -> bool:
        return all(r.valid for r in self.runs)


# ---- scenarios -------------------------------------------------------------

def scenario_sequential(backend) -> tuple[int, bool]:
    n = backend.total_frames
    valid = False
    for i in range(n):
        frame = backend.get_frame(i)
        if not valid and frame.any():
            valid = True
    return n, valid


def scenario_strided(backend) -> tuple[int, bool]:
    n = backend.total_frames
    indices = list(range(0, n, 3))
    valid = False
    for i in indices:
        frame = backend.get_frame(i)
        if not valid and frame.any():
            valid = True
    return len(indices), valid


def scenario_reverse(backend) -> tuple[int, bool]:
    n = backend.total_frames
    valid = False
    for i in range(n - 1, -1, -1):
        frame = backend.get_frame(i)
        if not valid and frame.any():
            valid = True
    return n, valid


def scenario_random_seek(backend) -> tuple[int, bool]:
    n = backend.total_frames
    rng = random.Random(1234)  # deterministic across runs
    indices = [rng.randrange(n) for _ in range(RANDOM_ACCESSES)]
    valid = False
    for i in indices:
        frame = backend.get_frame(i)
        if not valid and frame.any():
            valid = True
    return len(indices), valid


def scenario_near_sequential(backend) -> tuple[int, bool]:
    n = backend.total_frames
    rng = random.Random(4321)
    idx = 0
    indices = []
    for _ in range(NEAR_SEQ_ACCESSES):
        idx = min(n - 1, idx + rng.randint(1, 4))
        indices.append(idx)
        if idx >= n - 1:
            idx = 0
    valid = False
    for i in indices:
        frame = backend.get_frame(i)
        if not valid and frame.any():
            valid = True
    return len(indices), valid


SCENARIOS = {
    "sequential":      scenario_sequential,
    "strided":         scenario_strided,
    "reverse":         scenario_reverse,
    "random_seek":     scenario_random_seek,
    "near_sequential": scenario_near_sequential,
}


# ---- measurement -----------------------------------------------------------

def _cpu_totals() -> tuple[float, float]:
    """Return (cpu_self_s, cpu_child_s) at the moment of the call."""
    s = resource.getrusage(resource.RUSAGE_SELF)
    c = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (s.ru_utime + s.ru_stime, c.ru_utime + c.ru_stime)


def _rss_kib(pid: int) -> int:
    """Read VmRSS from /proc/{pid}/status. Returns 0 if the process is gone."""
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
    return 0


def _child_pids(parent: int) -> list[int]:
    """Direct children of `parent` from /proc/{pid}/task/{tid}/children."""
    pids: list[int] = []
    try:
        task_dir = f"/proc/{parent}/task"
        for tid in os.listdir(task_dir):
            try:
                with open(f"{task_dir}/{tid}/children") as f:
                    pids.extend(int(p) for p in f.read().split())
            except (FileNotFoundError, ProcessLookupError):
                continue
    except (FileNotFoundError, ProcessLookupError):
        pass
    return pids


def _total_rss_kib(pid: int) -> int:
    """RSS of `pid` plus all direct children (one level; enough for ffmpeg subprocess)."""
    total = _rss_kib(pid)
    for cpid in _child_pids(pid):
        total += _rss_kib(cpid)
    return total


class _RssSampler:
    """Poll /proc RSS every `interval_s` seconds in a background thread."""

    def __init__(self, interval_s: float = 0.01):
        self._interval = interval_s
        self._peak_kib = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._pid = os.getpid()

    def _loop(self) -> None:
        while not self._stop.is_set():
            rss = _total_rss_kib(self._pid)
            if rss > self._peak_kib:
                self._peak_kib = rss
            self._stop.wait(self._interval)

    def __enter__(self):
        self._peak_kib = _total_rss_kib(self._pid)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        # One final read after teardown, so a spike in the last ms isn't missed.
        rss = _total_rss_kib(self._pid)
        if rss > self._peak_kib:
            self._peak_kib = rss

    @property
    def peak_mb(self) -> float:
        return self._peak_kib / 1024.0


def run_once(backend_cls, path: Path, scenario_fn) -> RunResult:
    gc.collect()
    baseline_rss_kib = _total_rss_kib(os.getpid())
    cpu_self_0, cpu_child_0 = _cpu_totals()

    with _RssSampler() as sampler:
        wall_0 = time.perf_counter()
        backend = backend_cls(path)
        frames, valid = scenario_fn(backend)
        backend.close()
        wall_1 = time.perf_counter()

    cpu_self_1, cpu_child_1 = _cpu_totals()

    # Peak RSS *attributable to this run*: sampler peak minus baseline (self only).
    # If ffmpeg pushed the total higher, that shows up here; if the run stayed
    # under baseline (no allocations, small subprocess), we clamp to 0.
    peak_delta_kib = max(0, int(sampler.peak_mb * 1024) - baseline_rss_kib)

    return RunResult(
        wall_s=wall_1 - wall_0,
        cpu_self_s=cpu_self_1 - cpu_self_0,
        cpu_child_s=cpu_child_1 - cpu_child_0,
        peak_rss_mb=peak_delta_kib / 1024.0,
        frames=frames,
        valid=valid,
    )


def bench(backend_name: str, backend_cls, path: Path, scenario_name: str, scenario_fn, repeats: int) -> ScenarioResult:
    result = ScenarioResult(scenario=scenario_name, backend=backend_name, codec=path.stem)
    # We do NOT warm up per-scenario: fixtures are small and the FS cache is
    # already hot after the first scenario touches the file. Skipping warmup
    # roughly halves total wall time.
    for _ in range(repeats):
        try:
            result.runs.append(run_once(backend_cls, path, scenario_fn))
        except Exception as e:
            print(f"  [{backend_name}/{scenario_name}/{path.stem}] run failed: {e}")
            return result
    return result


# ---- reporting -------------------------------------------------------------

def print_table(results: list[ScenarioResult]) -> None:
    header = f"{'scenario':<17} {'codec':<6} {'backend':<8} {'wall(s)':>10} {'cpu(s)':>10} {'peak_rss(MB)':>13} {'fps':>10} {'valid':>6}"
    print(header)
    print("-" * len(header))
    for r in results:
        if not r.runs:
            print(f"{r.scenario:<17} {r.codec:<6} {r.backend:<8} {'--':>10} {'--':>10} {'--':>13} {'--':>10} {'ERR':>6}")
            continue
        wall = f"{r.median_wall_s:.3f}"
        cpu = f"{r.median_cpu_total_s:.3f}"
        rss = f"{r.peak_rss_mb:.1f}"
        fps = f"{r.median_fps:.1f}"
        valid = "yes" if r.all_valid else "NO"
        print(f"{r.scenario:<17} {r.codec:<6} {r.backend:<8} {wall:>10} {cpu:>10} {rss:>13} {fps:>10} {valid:>6}")


def write_json(results: list[ScenarioResult], path: Path) -> None:
    payload = []
    for r in results:
        d = {
            "scenario": r.scenario,
            "backend": r.backend,
            "codec": r.codec,
            "median_wall_s": r.median_wall_s if r.runs else None,
            "min_wall_s": r.min_wall_s if r.runs else None,
            "max_wall_s": r.max_wall_s if r.runs else None,
            "median_cpu_total_s": r.median_cpu_total_s if r.runs else None,
            "peak_rss_mb": r.peak_rss_mb if r.runs else None,
            "median_fps": r.median_fps if r.runs else None,
            "all_valid": r.all_valid if r.runs else False,
            "runs": [asdict(run) for run in r.runs],
        }
        payload.append(d)
    path.write_text(json.dumps(payload, indent=2))


# ---- main ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=REPEATS)
    parser.add_argument("--scenarios", nargs="+", default=list(SCENARIOS.keys()),
                        choices=list(SCENARIOS.keys()))
    parser.add_argument("--backends", nargs="+", default=list(BACKENDS.keys()),
                        choices=list(BACKENDS.keys()))
    parser.add_argument("--codecs", nargs="+", default=None,
                        help="Codec names (basenames of fixture files). Default: everything in fixtures/")
    args = parser.parse_args()

    if not FIXTURES_DIR.exists():
        sys.exit(f"error: {FIXTURES_DIR} does not exist. Run fixtures.py first.")

    fixtures = sorted(FIXTURES_DIR.glob("*.mp4"))
    if args.codecs:
        fixtures = [f for f in fixtures if f.stem in args.codecs]
    if not fixtures:
        sys.exit(f"error: no fixtures in {FIXTURES_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fixtures: {[f.name for f in fixtures]}")
    print(f"Backends: {args.backends}")
    print(f"Scenarios: {args.scenarios}")
    print(f"Repeats per scenario: {args.repeats}")
    print()

    results: list[ScenarioResult] = []
    for fixture in fixtures:
        for scenario_name in args.scenarios:
            for backend_name in args.backends:
                r = bench(
                    backend_name, BACKENDS[backend_name],
                    fixture, scenario_name, SCENARIOS[scenario_name],
                    args.repeats,
                )
                results.append(r)

    print()
    print_table(results)

    out = OUTPUT_DIR / "results.json"
    write_json(results, out)
    print()
    print(f"Full JSON written to {out}")


if __name__ == "__main__":
    main()
