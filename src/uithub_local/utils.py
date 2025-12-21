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
        # Find # not in strings
        in_single = False
        in_double = False
        escape = False
        result = []
        i = 0
        while i < len(line):
            char = line[i]

            # If previous character started an escape sequence,
            # treat this character as escaped and do not change string state.
            if escape:
                result.append(char)
                escape = False
                i += 1
                continue

            # Start a new escape sequence when we see an unescaped backslash
            # inside a string. The next character will be treated as escaped.
            if char == "\\" and (in_single or in_double):
                result.append(char)
                escape = True
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
    escape = False

    while i < len(content):
        char = content[i]

        # If previous character started an escape sequence,
        # treat this character as escaped and do not change string state.
        if escape:
            result.append(char)
            escape = False
            i += 1
            continue

        # Start a new escape sequence when we see an unescaped backslash
        # inside a string. The next character will be treated as escaped.
        if char == "\\" and (in_single or in_double):
            result.append(char)
            escape = True
            i += 1
            continue

        # Toggle string states
        if char == "'" and not in_double:
            in_single = not in_single
            result.append(char)
            i += 1
        elif char == '"' and not in_single:
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
                    if (
                        i + 1 < len(content)
                        and content[i] == "*"
                        and content[i + 1] == "/"
                    ):
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
    """Strip CSS /* */ comments, preserving strings."""
    result: list[str] = []
    i = 0
    length = len(content)
    in_single = False
    in_double = False
    in_comment = False

    while i < length:
        ch = content[i]
        next_ch = content[i + 1] if i + 1 < length else ""

        if in_comment:
            # Look for end of comment
            if ch == "*" and next_ch == "/":
                in_comment = False
                i += 2
            else:
                i += 1
            continue

        # Handle start of comment (only when not inside a string)
        if not in_single and not in_double and ch == "/" and next_ch == "*":
            in_comment = True
            i += 2
            continue

        # Handle escape sequences inside strings: keep backslash + next char
        if (in_single or in_double) and ch == "\\" and i + 1 < length:
            result.append(ch)
            result.append(content[i + 1])
            i += 2
            continue

        # Toggle string states
        if ch == "'" and not in_double:
            in_single = not in_single
            result.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            result.append(ch)
            i += 1
            continue

        # Regular character
        result.append(ch)
        i += 1

    return "".join(result)


def _strip_line_comment(line: str, marker: str) -> str:
    """Strip a line comment starting with marker, ignoring markers inside strings."""
    in_single = False
    in_double = False
    escape = False
    i = 0
    length = len(line)
    while i < length:
        ch = line[i]
        if escape:
            # Current character is escaped; skip special handling.
            escape = False
        elif ch == "\\":
            # Start of an escape sequence.
            escape = True
        elif ch == "'" and not in_double:
            # Toggle single-quoted (character) literal.
            in_single = not in_single
        elif ch == '"' and not in_single:
            # Toggle double-quoted string literal.
            in_double = not in_double
        elif not in_single and not in_double and line.startswith(marker, i):
            # Marker found outside of any string/char literal: start of comment.
            return line[:i].rstrip()
        i += 1
    return line


def _strip_sql_line_comment(line: str) -> str:
    """Strip a SQL -- line comment from a single line, preserving string literals."""
    in_single = False
    in_double = False
    i = 0
    length = len(line)
    while i < length:
        ch = line[i]
        # Handle single-quoted strings and doubled-quote escapes (e.g. 'it''s')
        if ch == "'" and not in_double:
            if in_single and i + 1 < length and line[i + 1] == "'":
                # Escaped single quote inside a single-quoted string
                i += 2
                continue
            in_single = not in_single
            i += 1
            continue
        # Handle double-quoted identifiers/strings
        # and doubled-quote escapes (e.g. "a""b")
        if ch == '"' and not in_single:
            if in_double and i + 1 < length and line[i + 1] == '"':
                # Escaped double quote inside a double-quoted string
                i += 2
                continue
            in_double = not in_double
            i += 1
            continue
        # Detect start of a line comment when not inside any string literal
        if not in_single and not in_double and ch == "-" and i + 1 < length:
            if line[i + 1] == "-":
                return line[:i].rstrip()
        i += 1
    return line


def _strip_sql_comments(content: str) -> str:
    """Strip SQL -- and /* */ comments."""
    # Remove /* */ comments
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    # Remove -- comments, taking care not to strip inside string literals
    lines = []
    for line in content.splitlines():
        lines.append(_strip_sql_line_comment(line))
    return "\n".join(lines)


def _strip_lua_comments(content: str) -> str:
    """Strip Lua -- and --[[ ]] comments."""
    # Remove --[[ ]] comments
    content = re.sub(r"--\[\[.*?\]\]", "", content, flags=re.DOTALL)
    # Remove -- comments outside of string literals
    lines = []
    for line in content.splitlines():
        lines.append(_strip_line_comment(line, "--"))
    return "\n".join(lines)


def _strip_haskell_comments(content: str) -> str:
    """Strip Haskell -- and {- -} comments."""
    # Remove {- -} comments
    content = re.sub(r"\{-.*?-\}", "", content, flags=re.DOTALL)
    # Remove -- comments outside of string/char literals
    lines = []
    for line in content.splitlines():
        lines.append(_strip_line_comment(line, "--"))
    return "\n".join(lines)


def _strip_lisp_comments(content: str) -> str:
    """Strip Lisp ; comments, preserving string literals."""
    lines = []
    for line in content.splitlines():
        in_string = False
        escape = False
        result: list[str] = []
        i = 0
        while i < len(line):
            char = line[i]
            # Handle escape sequences
            if escape:
                result.append(char)
                escape = False
                i += 1
                continue
            # Start escape sequence
            if char == "\\" and in_string:
                result.append(char)
                escape = True
                i += 1
                continue
            # Toggle string state on unescaped double quotes
            if char == '"':
                in_string = not in_string
                result.append(char)
            elif char == ";" and not in_string:
                # Start of comment outside a string; ignore rest of line
                break
            else:
                result.append(char)
            i += 1
        lines.append("".join(result).rstrip())
    return "\n".join(lines)
