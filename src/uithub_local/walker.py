"""Collects file paths and metadata."""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import pathspec

from .utils import is_binary_path

DEFAULT_MAX_SIZE = 1_048_576


def _load_gitignore_spec(root: Path) -> pathspec.PathSpec | None:
    """Load and parse .gitignore file from the root directory.
    
    Parameters
    ----------
    root:
        Root directory to look for .gitignore file.
        
    Returns
    -------
    pathspec.PathSpec or None:
        A PathSpec object if .gitignore exists, None otherwise.
    """
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        return None
    
    try:
        with open(gitignore_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", lines)
    except (OSError, UnicodeDecodeError):
        return None


@dataclass
class FileInfo:
    """Metadata about a file in the repository."""

    path: Path
    size: int
    mtime: float


def collect_files(
    path: Path,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
    max_size: int = DEFAULT_MAX_SIZE,
    *,
    binary_strict: bool = True,
    respect_gitignore: bool = True,
) -> List[FileInfo]:
    """Return list of readable, non-binary files under *path*.

    Parameters
    ----------
    path:
        Directory to walk.
    include:
        Glob patterns to include.
    exclude:
        Glob patterns to exclude.
    max_size:
        Skip files larger than this number of bytes.
    binary_strict:
        Use strict binary detection.
    respect_gitignore:
        If True, respect .gitignore rules (default True).
    """
    include = list(include or ["*"])
    exclude = list(exclude or [])
    files: List[FileInfo] = []
    root = Path(path)
    
    # Load .gitignore if respect_gitignore is True
    gitignore_spec = None
    if respect_gitignore:
        gitignore_spec = _load_gitignore_spec(root)

    def _expand(pattern: str) -> str:
        # normalize platform separators
        pat = pattern.replace("\\", "/").rstrip("/")
        if pat in {"*", "**"}:
            return pat
        if (root / pat).is_dir():
            return f"{pat}/**"  # recurse
        return pattern

    include = [_expand(p) for p in include]
    exclude = [_expand(p) for p in exclude]

    if (root / ".git").is_dir():
        git_included = any(pat.lstrip("./").startswith(".git") for pat in include)
        if not git_included:
            exclude.append(".git/**")

    for file in root.rglob("*"):
        try:
            rel = file.relative_to(root)
            rel_path = str(rel).replace("\\", "/")
            if not file.is_file():
                continue
            if not any(fnmatch.fnmatch(rel_path, pattern) for pattern in include):
                continue
            if any(fnmatch.fnmatch(rel_path, pattern) for pattern in exclude):
                continue
            # Check gitignore rules
            if gitignore_spec and gitignore_spec.match_file(rel_path):
                continue
            if is_binary_path(file, strict=binary_strict):
                continue
            stat = file.stat()
            if not os.access(file, os.R_OK):
                continue
            if stat.st_size > max_size:
                continue
            files.append(FileInfo(path=rel, size=stat.st_size, mtime=stat.st_mtime))
        except OSError:
            continue
    return files
