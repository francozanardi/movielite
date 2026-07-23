# Read-backend benchmark

Head-to-head comparison of the two frame-reader strategies present in
movielite today:

- **`cv2`** — `cv2.VideoCapture`, the one used by `VideoClip`.
- **`ffmpeg`** — an ffmpeg subprocess piping rawvideo, the one used by
  `AlphaVideoClip`.

The motivation is [issue #11](https://github.com/francozanardi/movielite/issues/11):
`VideoClip` cannot decode AV1 (or any codec the installed OpenCV wheel
lacks). Migrating to the ffmpeg backend would fix it, but only if the
performance cost is acceptable — movielite is a CPU-focused,
performance-first library.

## Files

- `fixtures.py` — regenerates the test videos from `tests/e2e/fixtures/bg.mp4`
  in H.264, HEVC and AV1 (picks the best available software encoder,
  skips a codec if none is present in the local ffmpeg build).
- `backends.py` — `Cv2Backend` and `FfmpegBackend`, mirroring the logic
  in `VideoClip` and `AlphaVideoClip` respectively. Both return BGR24
  numpy arrays so comparisons are apples-to-apples.
- `bench.py` — the harness. Runs a matrix of {backend × codec × scenario},
  measures wall / CPU / peak-RSS, prints a table, and dumps JSON to
  `output/results.json`.

## Running

```bash
# Generate fixtures (small profile: 360p @ 30fps × 3s = 90 frames)
python benchmarks/read_backends/fixtures.py

# Or the stress profile (720p × 30s = 900 frames — slow scenarios take longer)
python benchmarks/read_backends/fixtures.py --big --force

# Run the whole matrix
python benchmarks/read_backends/bench.py

# Subset: only sequential + strided, both backends, only h264
python benchmarks/read_backends/bench.py --scenarios sequential strided --codecs h264
```

## Scenarios

| Scenario         | What it exercises                                                       |
|------------------|-------------------------------------------------------------------------|
| `sequential`     | Read every frame in order. The dominant case for rendering.             |
| `strided`        | Read every 3rd frame. Simulates `speed > 1` or FPS drop.                |
| `reverse`        | Read frames in reverse. Worst case for ffmpeg (reopen per frame).       |
| `random_seek`    | 100 random accesses. Worst case for both backends.                      |
| `near_sequential`| Forward jumps of +1..+4. Exercises the small-jump fast path.            |

## Metrics

- `wall_s` — `time.perf_counter` delta for the whole run.
- `cpu_self_s + cpu_child_s` — CPU time from `getrusage`, including the
  ffmpeg subprocess. Reporting only self would hide the decoder cost.
- `peak_rss_mb` — highest observed RSS during the run, sampled from
  `/proc/{pid}/status` every 10ms (self + direct children), minus a
  baseline snapshot. `ru_maxrss` is not usable here — it's a high-water
  mark of the process and stays flat across runs once ffmpeg has been
  spawned.
- `fps` — `frames / wall_s`.
- `valid` — `NO` when the returned frames were all zeros (means the
  decoder silently failed, as cv2 does on AV1).

## Reproducing the AV1 failure

The `cv2` backend fails on AV1 with the exact error from issue #11:

```
[av1 @ 0x...] Your platform doesn't support hardware accelerated AV1 decoding.
[av1 @ 0x...] Failed to get pixel format.
[av1 @ 0x...] Get current frame error
```

...and returns empty frames (mean=0). The bench reports these runs as
`valid=NO`.
