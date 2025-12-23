"""CLI entry point for uithub-local."""

from __future__ import annotations

from pathlib import Path
from typing import List, cast

import click

from .renderer import render, render_split
from .walker import DEFAULT_MAX_SIZE, collect_files
from .downloader import download_repo


def _expand_comma_separated(patterns: List[str]) -> List[str]:
    """Expand comma-separated patterns into individual patterns.
    
    Example:
        ["*.py", "*.html,*.js"] -> ["*.py", "*.html", "*.js"]
    """
    expanded = []
    for pattern in patterns:
        # Split by comma and strip whitespace from each part
        parts = [p.strip() for p in pattern.split(",")]
        expanded.extend(parts)
    return expanded


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "path",
    required=False,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option("--remote-url", help="Git repo URL to download")
@click.option(
    "--local-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Local directory path to process (alternative to PATH argument)",
)
@click.option("--private-token", envvar="GITHUB_TOKEN", help="Token for private repos")
@click.option(
    "--include",
    multiple=True,
    default=["*"],
    help=("Glob(s) to include. Supports comma-separated patterns. Trailing '/' or '\\' expands recursively."),
)
@click.option(
    "--exclude",
    multiple=True,
    help=(
        "Glob(s) to exclude. Supports comma-separated patterns. Trailing '/' or '\\' expands recursively. "
        "'.git/' is excluded by default."
    ),
)
@click.option(
    "--max-size",
    type=int,
    default=DEFAULT_MAX_SIZE,
    show_default=f"{DEFAULT_MAX_SIZE} bytes",
    help="Skip files larger than this many bytes",
)
@click.option("--max-tokens", type=int, help="Hard cap; truncate largest files first")
@click.option(
    "--split",
    type=int,
    help="Split output into multiple files, each with approximately N tokens",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json", "html"]),
    default="text",
)
@click.option(
    "--binary-strict/--no-binary-strict",
    default=True,
    help="Use strict binary detection",
)
@click.option(
    "--exclude-comments",
    is_flag=True,
    default=False,
    help="Strip code comments from output",
)
@click.option(
    "--not-ignore",
    is_flag=True,
    default=False,
    help="Do not respect .gitignore rules (default: respect .gitignore)",
)
@click.option("--stdout/--no-stdout", default=True, help="Print dump to STDOUT")
@click.option("--outfile", type=click.Path(path_type=Path), help="Write dump to file")
@click.option(
    "--encoding",
    default="utf-8",
    show_default=True,
    help="Encoding for --outfile",
)
@click.version_option()
def main(
    path: Path | None,
    remote_url: str | None,
    local_path: Path | None,
    private_token: str | None,
    include: List[str],
    exclude: List[str],
    max_size: int,
    max_tokens: int | None,
    split: int | None,
    fmt: str,
    binary_strict: bool,
    exclude_comments: bool,
    not_ignore: bool,
    stdout: bool,
    outfile: Path | None,
    encoding: str,
) -> None:
    """Flatten a repository into one text dump."""
    # Count how many path sources are provided
    path_sources = sum([path is not None, local_path is not None, remote_url is not None])
    if path_sources > 1:
        raise click.UsageError("Only one of PATH, --local-path, or --remote-url can be used")
    if path_sources == 0:
        raise click.UsageError("One of PATH, --local-path, or --remote-url is required")

    # Consolidate path sources - use whichever was provided
    if local_path is not None:
        path = local_path
    if split is not None and split <= 0:
        raise click.UsageError("--split must be a positive integer")
    if split and outfile is None:
        raise click.UsageError("--split requires --outfile")

    # Expand comma-separated patterns
    include = _expand_comma_separated(list(include))
    exclude = _expand_comma_separated(list(exclude))

    try:
        if remote_url:
            with download_repo(remote_url, private_token) as tmp:
                files = collect_files(
                    tmp,
                    include,
                    exclude,
                    max_size=max_size,
                    binary_strict=binary_strict,
                    respect_gitignore=not not_ignore,
                )
                if split:
                    outputs = render_split(
                        files,
                        tmp,
                        split,
                        max_tokens=max_tokens,
                        fmt=fmt,
                        exclude_comments=exclude_comments,
                    )
                else:
                    outputs = [
                        (
                            None,
                            render(
                                files,
                                tmp,
                                max_tokens=max_tokens,
                                fmt=fmt,
                                exclude_comments=exclude_comments,
                            ),
                        )
                    ]
        else:
            files = collect_files(
                cast(Path, path),
                include,
                exclude,
                max_size=max_size,
                binary_strict=binary_strict,
                respect_gitignore=not not_ignore,
            )
            if split:
                outputs = render_split(
                    files,
                    cast(Path, path),
                    split,
                    max_tokens=max_tokens,
                    fmt=fmt,
                    exclude_comments=exclude_comments,
                )
            else:
                outputs = [
                    (
                        None,
                        render(
                            files,
                            cast(Path, path),
                            max_tokens=max_tokens,
                            fmt=fmt,
                            exclude_comments=exclude_comments,
                        ),
                    )
                ]
    except Exception as exc:  # pragma: no cover - fatal CLI errors
        click.echo(str(exc), err=True)
        raise SystemExit(1)

    # Handle output
    if split:
        # Write multiple files
        base_dir = cast(Path, outfile).parent
        for filename, content in outputs:
            output_path = base_dir / filename
            output_path.write_text(content, encoding=encoding, errors="replace")
            if stdout:
                click.echo(f"Written {output_path}")
    else:
        # Single output
        output = outputs[0][1]
        if outfile:
            outfile.write_text(output, encoding=encoding, errors="replace")
        if stdout:
            click.echo(output)


if __name__ == "__main__":  # pragma: no cover
    main()
