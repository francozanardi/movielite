"""
Extract the release notes for a given version from CHANGELOG.md and validate that
pyproject.toml is on the same version. Fails loudly on any mismatch so the release
workflow bails before touching PyPI.

Usage: extract_release_info.py <tag> <notes_output_path>
  <tag> is the pushed git tag, e.g. 'v0.3.0' (with or without leading 'v').
  Writes the changelog body for that version to <notes_output_path>.
"""
import re
import sys
import tomllib
from pathlib import Path


def die(msg: str) -> None:
    sys.stderr.write(f"error: {msg}\n")
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 3:
        die("usage: extract_release_info.py <tag> <notes_output_path>")

    tag = sys.argv[1]
    notes_path = Path(sys.argv[2])
    version = tag.lstrip("v")

    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    py_version = pyproject["project"]["version"]
    if py_version != version:
        die(
            f"tag {tag!r} implies version {version!r} but pyproject.toml has "
            f"{py_version!r}. Bump pyproject.toml or retag."
        )

    changelog = Path("CHANGELOG.md").read_text()
    # Match "## [<version>] - ..." and grab everything up to the next "## " (or EOF).
    section_re = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = section_re.search(changelog)
    if not m:
        die(
            f"no '## [{version}]' section found in CHANGELOG.md. "
            f"Add one before tagging."
        )

    body = m.group(1).strip()
    if not body:
        die(f"the '## [{version}]' section in CHANGELOG.md is empty.")

    notes_path.write_text(body + "\n")
    print(f"Extracted notes for {version} → {notes_path} ({len(body)} chars)")


if __name__ == "__main__":
    main()
