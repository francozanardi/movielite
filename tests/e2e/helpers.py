"""
Golden-file testing helpers for movielite's e2e suite.

Workflow:
  # First-time setup (or after intentional output changes):
  #   docker build -t movielite-test -f Dockerfile.test .
  #   docker run --rm -e UPDATE_GOLDENS=1 -v $PWD:/workspace movielite-test
  #   git add tests/e2e/{fixtures,goldens} && git commit
  #
  # Normal run (must match committed goldens byte-for-byte):
  #   docker run --rm -v $PWD:/workspace movielite-test
"""
import hashlib
import os
import shutil
from pathlib import Path

E2E_DIR = Path(__file__).parent
FIXTURES_DIR = E2E_DIR / "fixtures"
GOLDENS_DIR = E2E_DIR / "goldens"

UPDATE_GOLDENS = os.environ.get("UPDATE_GOLDENS", "").lower() in ("1", "true", "yes")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def assert_matches_golden(output: Path, golden_name: str) -> None:
    """
    Compare `output` byte-for-byte against tests/e2e/goldens/<golden_name>.

    - UPDATE_GOLDENS=1: copies `output` over the golden (creating goldens/ if needed).
    - Golden missing (no UPDATE flag): generates it and fails with instructions, so
      the first test run doesn't silently accept whatever came out.
    - Byte mismatch: writes the actual output to goldens/_actual__<name> for inspection
      and reports both hashes.
    """
    output = Path(output)
    golden = GOLDENS_DIR / golden_name
    GOLDENS_DIR.mkdir(exist_ok=True)

    if UPDATE_GOLDENS:
        shutil.copyfile(output, golden)
        return

    if not golden.exists():
        shutil.copyfile(output, golden)
        raise AssertionError(
            f"Golden '{golden_name}' did not exist. It was just generated at:\n"
            f"  {golden}\n"
            f"Review it, commit it, and re-run the tests.\n"
            f"To (re)generate all goldens at once: UPDATE_GOLDENS=1 pytest tests/e2e"
        )

    actual_hash = sha256_file(output)
    expected_hash = sha256_file(golden)
    if actual_hash != expected_hash:
        debug = GOLDENS_DIR / f"_actual__{golden_name}"
        shutil.copyfile(output, debug)
        raise AssertionError(
            f"Byte mismatch for {golden_name}\n"
            f"  expected sha256: {expected_hash}  ({golden.stat().st_size} bytes)\n"
            f"  actual   sha256: {actual_hash}  ({output.stat().st_size} bytes)\n"
            f"  actual saved to: {debug}\n"
            f"If the change is intentional: UPDATE_GOLDENS=1 pytest tests/e2e"
        )
