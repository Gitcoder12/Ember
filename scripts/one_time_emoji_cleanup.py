from __future__ import annotations

import re
from pathlib import Path

EMOJI_PATTERN = re.compile(
    r"[\U0001F1E6-\U0001F1FF\U0001F300-\U0001F5FF"
    r"\U0001F600-\U0001F64F\U0001F680-\U0001F6FF"
    r"\U0001F700-\U0001F77F\U0001F780-\U0001F7FF"
    r"\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF"
    r"\U0001FA00-\U0001FAFF\u2300-\u23FF\u2600-\u27BF"
    r"\u2B00-\u2BFF\uFE0E-\uFE0F\u200D\u20E3"
    r"\U0001F3FB-\U0001F3FF]"
)
SKIP_PARTS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__",
    "node_modules", "vendor", "dist", "build", ".next", "coverage",
    ".ruff_cache", ".pytest_cache",
}
MAX_FILE_BYTES = 5 * 1024 * 1024


def main() -> int:
    changed = 0
    root = Path.cwd()
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        if any(part in SKIP_PARTS for part in path.relative_to(root).parts):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            with path.open("r", encoding="utf-8", newline="") as handle:
                original = handle.read()
        except (OSError, UnicodeDecodeError):
            continue
        cleaned = EMOJI_PATTERN.sub("", original)
        if cleaned == original:
            continue
        try:
            with path.open("w", encoding="utf-8", newline="") as handle:
                handle.write(cleaned)
        except OSError:
            continue
        changed += 1
        print(path.as_posix())
    print(f"Updated {changed} text files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
