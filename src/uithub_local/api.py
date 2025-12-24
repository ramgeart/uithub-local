"""High-level programmatic API for uithub-local."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .downloader import download_repo
from .renderer import render, render_split
from .walker import DEFAULT_MAX_SIZE, collect_files


def dump_repo(
    path_or_url: str | Path,
    *,
    fmt: str = "text",
    encoding: str = "utf-8",
    **cli_kwargs: Any,
) -> str:
    """Return a repository dump as a string.

    Args:
        path_or_url: Local directory or remote repository URL.
        fmt: Output format ("text", "json" or "html").
        encoding: Suggested encoding if the caller writes the dump to disk. The
            value is not used by ``dump_repo`` itself.
        **cli_kwargs: Extra options matching the CLI such as ``include``,
            ``exclude``, ``max_size``, ``max_tokens``, ``binary_strict``,
            ``exclude_comments``, ``respect_gitignore`` and ``private_token``.

    Returns:
        The rendered dump.
    """

    include = cli_kwargs.get("include", ["*"])
    exclude = cli_kwargs.get("exclude", [])
    max_size = cli_kwargs.get("max_size", DEFAULT_MAX_SIZE)
    max_tokens = cli_kwargs.get("max_tokens")
    binary_strict = cli_kwargs.get("binary_strict", True)
    exclude_comments = cli_kwargs.get("exclude_comments", False)
    respect_gitignore = cli_kwargs.get("respect_gitignore", True)
    private_token = cli_kwargs.get("private_token")

    path = Path(path_or_url)
    if path.exists():
        files = collect_files(
            path,
            include,
            exclude,
            max_size=max_size,
            binary_strict=binary_strict,
            respect_gitignore=respect_gitignore,
        )
        return render(
            files,
            path,
            max_tokens=max_tokens,
            fmt=fmt,
            exclude_comments=exclude_comments,
        )

    url = str(path_or_url)
    with download_repo(url, private_token) as tmp:
        files = collect_files(
            tmp,
            include,
            exclude,
            max_size=max_size,
            binary_strict=binary_strict,
            respect_gitignore=respect_gitignore,
        )
        return render(
            files,
            tmp,
            max_tokens=max_tokens,
            fmt=fmt,
            exclude_comments=exclude_comments,
        )


def dump_repo_split(
    path_or_url: str | Path,
    split: int,
    *,
    fmt: str = "text",
    **cli_kwargs: Any,
) -> list[tuple[str | None, str]]:
    """Return a repository dump split into multiple parts.

    Args:
        path_or_url: Local directory or remote repository URL.
        split: Number of tokens per split.
        fmt: Output format ("text", "json" or "html").
        **cli_kwargs: Extra options matching the CLI.

    Returns:
        A list of (filename, content) tuples.
    """
    include = cli_kwargs.get("include", ["*"])
    exclude = cli_kwargs.get("exclude", [])
    max_size = cli_kwargs.get("max_size", DEFAULT_MAX_SIZE)
    max_tokens = cli_kwargs.get("max_tokens")
    binary_strict = cli_kwargs.get("binary_strict", True)
    exclude_comments = cli_kwargs.get("exclude_comments", False)
    respect_gitignore = cli_kwargs.get("respect_gitignore", True)
    private_token = cli_kwargs.get("private_token")

    path = Path(path_or_url)
    if path.exists():
        files = collect_files(
            path,
            include,
            exclude,
            max_size=max_size,
            binary_strict=binary_strict,
            respect_gitignore=respect_gitignore,
        )
        return render_split(
            files,
            path,
            split,
            max_tokens=max_tokens,
            fmt=fmt,
            exclude_comments=exclude_comments,
        )

    url = str(path_or_url)
    with download_repo(url, private_token) as tmp:
        files = collect_files(
            tmp,
            include,
            exclude,
            max_size=max_size,
            binary_strict=binary_strict,
            respect_gitignore=respect_gitignore,
        )
        return render_split(
            files,
            tmp,
            split,
            max_tokens=max_tokens,
            fmt=fmt,
            exclude_comments=exclude_comments,
        )
