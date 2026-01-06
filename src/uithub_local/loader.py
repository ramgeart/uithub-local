"""Safe file loader with encoding fallback."""

from __future__ import annotations

from pathlib import Path

from .filters import apply_content_filters
from .utils import strip_comments


def load_text(
    path: Path,
    *,
    exclude_comments: bool = False,
    filter_content: bool = False,
) -> str:
    """Return text of *path* with UTF-8 fallback.

    Args:
        path: Path to the file.
        exclude_comments: If True, strip comments from the content.
        filter_content: If True, filter ipynb outputs, base64 strings,
            and sensitive URLs.

    Returns:
        File content, optionally with comments and/or noise removed.
    """

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="replace")

    # Strip comments first (if enabled) to reduce content that needs filtering
    if exclude_comments:
        content = strip_comments(content, path)

    if filter_content:
        content = apply_content_filters(content, path)

    return content
