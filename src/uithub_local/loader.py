"""Safe file loader with encoding fallback."""

from __future__ import annotations

from pathlib import Path

from .utils import strip_comments


def load_text(path: Path, *, exclude_comments: bool = False) -> str:
    """Return text of *path* with UTF-8 fallback.

    Args:
        path: Path to the file.
        exclude_comments: If True, strip comments from the content.

    Returns:
        File content, optionally with comments removed.
    """

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="replace")

    if exclude_comments:
        content = strip_comments(content, path)

    return content
