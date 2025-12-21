"""Render repository files into a single dump."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple
import html

from .loader import load_text
from .tokenizer import approximate_tokens
from .walker import FileInfo


class FileDump:
    """A file plus its loaded contents and token count."""

    def __init__(
        self, info: FileInfo, root: Path, exclude_comments: bool = False
    ) -> None:
        self.path = info.path
        self.full_path = root / info.path
        self.size = info.size
        self.tokens = 0
        self.content = ""
        try:
            self.content = load_text(self.full_path, exclude_comments=exclude_comments)
            self.tokens = approximate_tokens(self.content)
        except Exception:
            self.content = ""
            self.tokens = 0


class Dump:
    def __init__(
        self,
        files: List[FileInfo],
        root: Path,
        max_tokens: int | None = None,
        exclude_comments: bool = False,
    ) -> None:
        self.root = root
        self.file_dumps: List[FileDump] = [
            FileDump(info, root, exclude_comments=exclude_comments) for info in files
        ]
        self.total_tokens = sum(fd.tokens for fd in self.file_dumps)
        if max_tokens is not None and self.total_tokens > max_tokens:
            self._truncate(max_tokens)

    def _truncate(self, limit: int) -> None:
        self.file_dumps.sort(key=lambda f: (f.tokens, f.path.as_posix()), reverse=True)
        while self.total_tokens > limit and self.file_dumps:
            victim = self.file_dumps.pop(0)
            self.total_tokens -= victim.tokens

    def split_by_tokens(self, split_tokens: int) -> List[List[FileDump]]:
        """Split file_dumps into chunks, each with approximately split_tokens tokens."""
        if split_tokens <= 0:
            return [self.file_dumps]
        
        chunks: List[List[FileDump]] = []
        current_chunk: List[FileDump] = []
        current_tokens = 0
        
        for fd in self.file_dumps:
            # If adding this file would exceed the limit and we already have files in the chunk
            if current_tokens + fd.tokens > split_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(fd)
            current_tokens += fd.tokens
        
        # Add the last chunk if it has any files
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks if chunks else [[]]

    def as_text(self, repo_name: str, file_dumps: List[FileDump] | None = None) -> str:
        """Render as text format.
        
        Args:
            repo_name: Name of the repository.
            file_dumps: Optional list of FileDump objects. If None, uses self.file_dumps.
        """
        if file_dumps is None:
            file_dumps = self.file_dumps
        timestamp = datetime.now(timezone.utc).isoformat()
        chunk_tokens = sum(fd.tokens for fd in file_dumps)
        lines = [f"# Uithub-local dump – {repo_name} – {timestamp}"]
        lines.append(f"# ≈ {chunk_tokens} tokens")
        for fd in file_dumps:
            lines.append(f"\n### {fd.path.as_posix()}")
            lines.append(fd.content)
        lines.append("")
        return "\n".join(lines)

    def as_json(self, repo_name: str, file_dumps: List[FileDump] | None = None) -> str:
        """Render as JSON format.
        
        Args:
            repo_name: Name of the repository.
            file_dumps: Optional list of FileDump objects. If None, uses self.file_dumps.
        """
        if file_dumps is None:
            file_dumps = self.file_dumps
        chunk_tokens = sum(fd.tokens for fd in file_dumps)
        obj = {
            "repo": repo_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_tokens": chunk_tokens,
            "files": [
                {
                    "path": fd.path.as_posix(),
                    "contents": fd.content,
                    "tokens": fd.tokens,
                }
                for fd in file_dumps
            ],
        }
        return json.dumps(obj, indent=2)

    def as_html(self, repo_name: str, file_dumps: List[FileDump] | None = None) -> str:
        """Render as HTML format.
        
        Args:
            repo_name: Name of the repository.
            file_dumps: Optional list of FileDump objects. If None, uses self.file_dumps.
        """
        if file_dumps is None:
            file_dumps = self.file_dumps
        chunk_tokens = sum(fd.tokens for fd in file_dumps)
        timestamp = datetime.now(timezone.utc).isoformat()
        style = """
        <style>
        html {
            font-size:14px;
            font-family:ui-monospace, SFMono-Regular, Menlo, monospace;
        }
        body {
            margin:0;
            background:#0d1117;
            color:#c9d1d9;
        }
        .container {
            max-width:1100px;
            padding:2rem;
            margin:0 auto;
            display:flex;
            flex-direction:column;
            gap:1rem;
        }
        .header-card, details.file-card {
            border:1px solid #30363d;
            border-radius:6px;
            box-shadow:0 2px 4px rgba(0,0,0,.6);
            background:#161b22;
        }
        .header-card {
            padding:1rem 1.25rem;
        }
        .header-card h1 {
            margin:0 0 .5rem;
            font-size:1.25rem;
        }
        .header-card p {
            margin:0;
            color:#8b949e;
            font-size:.9rem;
        }
        details.file-card summary {
            display:flex;
            align-items:center;
            gap:.75rem;
            padding:.8rem 1rem;
            cursor:pointer;
            background:#161b22;
            color:inherit;
            list-style:none;
        }
        details.file-card summary:hover {
            background:#21262d;
        }
        details.file-card summary::-webkit-details-marker {display:none;}
        .chevron {
            fill:#58a6ff;
            transition:transform .15s;
            flex:none;
        }
        @media (prefers-reduced-motion: reduce) {
            .chevron {transition:none;}
        }
        details.file-card[open] > summary .chevron {
            transform:rotate(90deg);
        }
        summary:focus-visible {
            outline:2px solid #58a6ff;
            outline-offset:2px;
        }
        .path {
            font-weight:bold;
            flex:1;
            overflow:hidden;
            text-overflow:ellipsis;
            white-space:nowrap;
            direction:rtl;
        }
        .badge {
            font-size:.7rem;
            background:#238636;
            color:#fff;
            padding:.15rem .45rem;
            border-radius:9999px;
        }
        details.file-card pre {
            background:#0d1117;
            padding:1rem 1.25rem;
            margin:0;
            overflow:auto;
            line-height:1.45;
            white-space:pre;
            border-top:1px solid #30363d;
            border-radius:0 0 6px 6px;
            background-image:linear-gradient(transparent 97%,
                rgba(255,255,255,.05) 97%);
            background-size:100% 1.6em;
        }
        @media (max-width:600px) {
            .container {padding:1rem;}
        }
        </style>
        """
        lines = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width,initial-scale=1">',
            f"<title>{repo_name} dump</title>",
            style,
            "</head>",
            "<body>",
            "<div class='container'>",
            "<div class='header-card'>",
            f"<h1>Uithub-local dump – {repo_name}</h1>",
            f"<p>{timestamp} \u00b7 \u2248 {chunk_tokens} tokens</p>",
            "</div>",
        ]
        for fd in file_dumps:
            path = html.escape(fd.path.as_posix())
            lines.append("<details class='file-card'>")
            lines.append(
                "<summary>"
                "<svg class='chevron' width='10' height='10'"
                " viewBox='0 0 8 8' aria-hidden='true'>"
                "<path d='M0 0 L6 4 L0 8z'/></svg>"
                f"<span class='path'>{path}</span>"
                "</summary>"
            )
            lines.append("<pre><code>")
            lines.append(html.escape(fd.content))
            lines.append("</code></pre>")
            lines.append("</details>")
        lines.append("</div></body></html>")
        return "\n".join(lines)


def render(
    files: List[FileInfo],
    root: Path,
    *,
    max_tokens: int | None = None,
    fmt: str = "text",
    exclude_comments: bool = False,
) -> str:
    dump = Dump(files, root, max_tokens, exclude_comments=exclude_comments)
    resolved = root.resolve()
    repo_name = resolved.name or resolved.parent.name
    if fmt == "json":
        return dump.as_json(repo_name)
    if fmt == "html":
        return dump.as_html(repo_name)
    return dump.as_text(repo_name)


def render_split(
    files: List[FileInfo],
    root: Path,
    split_tokens: int,
    *,
    max_tokens: int | None = None,
    fmt: str = "text",
    exclude_comments: bool = False,
) -> List[Tuple[str, str]]:
    """Render repository into multiple outputs split by token count.
    
    Args:
        files: List of FileInfo objects to render.
        root: Root path of the repository.
        split_tokens: Maximum tokens per output chunk.
        max_tokens: Optional hard cap on total tokens (applied before splitting).
        fmt: Output format ("text", "json", or "html").
        exclude_comments: Whether to strip code comments.
    
    Returns:
        List of (filename, content) tuples for each chunk.
    """
    dump = Dump(files, root, max_tokens, exclude_comments=exclude_comments)
    resolved = root.resolve()
    repo_name = resolved.name or resolved.parent.name
    
    # Get file extension based on format
    ext = {"text": "txt", "json": "json", "html": "html"}.get(fmt, "txt")
    
    # Split into chunks
    chunks = dump.split_by_tokens(split_tokens)
    
    # Generate outputs for each chunk
    outputs: List[Tuple[str, str]] = []
    for idx, chunk in enumerate(chunks, start=1):
        filename = f"{repo_name}_{idx}.{ext}"
        if fmt == "json":
            content = dump.as_json(repo_name, chunk)
        elif fmt == "html":
            content = dump.as_html(repo_name, chunk)
        else:
            content = dump.as_text(repo_name, chunk)
        outputs.append((filename, content))
    
    return outputs
