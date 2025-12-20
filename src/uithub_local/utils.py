"""Utility helpers for uithub-local."""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path

ASCII_WHITELIST = set(b"\t\n\r")


def is_binary_path(path: Path, *, strict: bool = True) -> bool:
    """Return True if file looks binary."""
    mime, _ = mimetypes.guess_type(path.as_posix())
    if mime is not None and not mime.startswith("text"):
        return True
    try:
        with open(path, "rb") as fh:
            chunk = fh.read(8192)
        if b"\0" in chunk:
            return True
        if strict and chunk:
            non_text = sum(
                1 for b in chunk if not (32 <= b <= 126 or b in ASCII_WHITELIST)
            )
            if non_text / len(chunk) > 0.30:
                return True
        return False
    except OSError:
        return True


def strip_comments(content: str, file_path: Path) -> str:
    """Remove comments from code based on file extension.

    Args:
        content: The file content as a string.
        file_path: Path to the file (used to determine language).

    Returns:
        Content with comments removed.
    """
    ext = file_path.suffix.lower()

    # Languages with # comments (Python, Ruby, Shell, YAML, etc.)
    if ext in {
        ".py",
        ".pyw",
        ".rb",
        ".sh",
        ".bash",
        ".zsh",
        ".yml",
        ".yaml",
        ".toml",
        ".conf",
        ".ini",
        ".r",
        ".pl",
        ".tcl",
    }:
        return _strip_hash_comments(content)

    # Languages with // and /* */ comments
    # (C-style: C, C++, Java, JavaScript, Go, Rust, etc.)
    elif ext in {
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cc",
        ".cxx",
        ".java",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".cs",
        ".swift",
        ".kt",
        ".kts",
        ".scala",
        ".m",
        ".mm",
        ".php",
        ".dart",
    }:
        return _strip_c_style_comments(content)

    # HTML/XML
    elif ext in {".html", ".htm", ".xml", ".svg", ".xhtml"}:
        return _strip_html_comments(content)

    # CSS
    elif ext in {".css", ".scss", ".sass", ".less"}:
        return _strip_css_comments(content)

    # SQL
    elif ext in {".sql"}:
        return _strip_sql_comments(content)

    # Lua
    elif ext in {".lua"}:
        return _strip_lua_comments(content)

    # Haskell
    elif ext in {".hs", ".lhs"}:
        return _strip_haskell_comments(content)

    # Lisp-family
    elif ext in {".lisp", ".cl", ".el", ".scm", ".clj", ".cljs"}:
        return _strip_lisp_comments(content)

    # Return original content for unsupported file types
    return content


def _strip_hash_comments(content: str) -> str:
    """Strip # comments from content, preserving strings."""
    lines = []
    for line in content.splitlines():
        # Simple approach: find # not in strings
        in_single = False
        in_double = False
        result = []
        i = 0
        while i < len(line):
            char = line[i]

            # Handle escape sequences
            if i > 0 and line[i - 1] == "\\":
                result.append(char)
                i += 1
                continue

            # Toggle string states
            if char == "'" and not in_double:
                in_single = not in_single
                result.append(char)
            elif char == '"' and not in_single:
                in_double = not in_double
                result.append(char)
            elif char == "#" and not in_single and not in_double:
                # Found a comment, stop processing this line
                break
            else:
                result.append(char)
            i += 1

        lines.append("".join(result).rstrip())
    return "\n".join(lines)


def _strip_c_style_comments(content: str) -> str:
    """Strip // and /* */ comments, preserving strings."""
    result = []
    i = 0
    in_single = False
    in_double = False

    while i < len(content):
        # Handle escape sequences in strings
        if i > 0 and content[i - 1] == "\\" and (in_single or in_double):
            result.append(content[i])
            i += 1
            continue

        char = content[i]

        # Toggle string states
        if char == "'" and not in_double and (i == 0 or content[i - 1] != "\\"):
            in_single = not in_single
            result.append(char)
            i += 1
        elif char == '"' and not in_single and (i == 0 or content[i - 1] != "\\"):
            in_double = not in_double
            result.append(char)
            i += 1
        elif not in_single and not in_double:
            # Check for // comment
            if char == "/" and i + 1 < len(content) and content[i + 1] == "/":
                # Skip until end of line
                while i < len(content) and content[i] != "\n":
                    i += 1
                if i < len(content):
                    result.append("\n")
                    i += 1
            # Check for /* */ comment
            elif char == "/" and i + 1 < len(content) and content[i + 1] == "*":
                i += 2
                # Skip until */
                while i < len(content):
                    if i + 1 < len(content) and content[i] == "*" and content[i + 1] == "/":
                        i += 2
                        break
                    i += 1
            else:
                result.append(char)
                i += 1
        else:
            result.append(char)
            i += 1

    return "".join(result)


def _strip_html_comments(content: str) -> str:
    """Strip HTML/XML <!-- --> comments."""
    return re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)


def _strip_css_comments(content: str) -> str:
    """Strip CSS /* */ comments."""
    return re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)


def _strip_sql_comments(content: str) -> str:
    """Strip SQL -- and /* */ comments."""
    # Remove /* */ comments
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    # Remove -- comments
    lines = []
    for line in content.splitlines():
        # Find -- not in strings
        idx = line.find("--")
        if idx != -1:
            line = line[:idx].rstrip()
        lines.append(line)
    return "\n".join(lines)


def _strip_lua_comments(content: str) -> str:
    """Strip Lua -- and --[[ ]] comments."""
    # Remove --[[ ]] comments
    content = re.sub(r"--\[\[.*?\]\]", "", content, flags=re.DOTALL)
    # Remove -- comments
    lines = []
    for line in content.splitlines():
        idx = line.find("--")
        if idx != -1:
            line = line[:idx].rstrip()
        lines.append(line)
    return "\n".join(lines)


def _strip_haskell_comments(content: str) -> str:
    """Strip Haskell -- and {- -} comments."""
    # Remove {- -} comments
    content = re.sub(r"\{-.*?-\}", "", content, flags=re.DOTALL)
    # Remove -- comments
    lines = []
    for line in content.splitlines():
        idx = line.find("--")
        if idx != -1:
            line = line[:idx].rstrip()
        lines.append(line)
    return "\n".join(lines)


def _strip_lisp_comments(content: str) -> str:
    """Strip Lisp ; comments."""
    lines = []
    for line in content.splitlines():
        idx = line.find(";")
        if idx != -1:
            line = line[:idx].rstrip()
        lines.append(line)
    return "\n".join(lines)
