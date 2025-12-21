"""Tests for comment stripping functionality."""

from pathlib import Path

from uithub_local.utils import strip_comments


def test_strip_python_comments():
    """Test stripping # comments from Python."""
    content = """# This is a comment
x = 5  # inline comment
y = "# not a comment"
z = '# also not a comment'
"""
    result = strip_comments(content, Path("test.py"))
    assert "# This is a comment" not in result
    assert "# inline comment" not in result
    assert "# not a comment" in result
    assert "# also not a comment" in result
    assert "x = 5" in result


def test_strip_javascript_comments():
    """Test stripping // and /* */ from JavaScript."""
    content = """// Single line comment
const x = 5; // inline
/* Multi-line
   comment */
const y = "// not a comment";
const z = '/* also not */';
"""
    result = strip_comments(content, Path("test.js"))
    assert "// Single line comment" not in result
    assert "// inline" not in result
    assert "Multi-line" not in result
    assert "comment */" not in result
    assert "const x = 5;" in result
    assert "// not a comment" in result
    assert "/* also not */" in result


def test_strip_c_comments():
    """Test stripping C-style comments."""
    content = """// C++ style comment
int x = 5; // inline
/* C style
   comment */
char *s = "// not a comment";
"""
    result = strip_comments(content, Path("test.c"))
    assert "// C++ style comment" not in result
    assert "// inline" not in result
    assert "C style" not in result
    assert "int x = 5;" in result
    assert "// not a comment" in result


def test_strip_html_comments():
    """Test stripping HTML comments."""
    content = """<html>
<!-- This is a comment -->
<body>
<!-- Multi-line
     comment -->
<p>Text</p>
</body>
</html>"""
    result = strip_comments(content, Path("test.html"))
    assert "<!-- This is a comment -->" not in result
    assert "Multi-line" not in result
    assert "<body>" in result
    assert "<p>Text</p>" in result


def test_strip_css_comments():
    """Test stripping CSS comments."""
    content = """/* Header styles */
.header {
    color: red; /* inline */
}
/* Multi-line
   comment */
"""
    result = strip_comments(content, Path("test.css"))
    assert "Header styles" not in result
    assert "inline" not in result
    assert "Multi-line" not in result
    assert ".header {" in result
    assert "color: red;" in result


def test_strip_sql_comments():
    """Test stripping SQL comments."""
    content = """-- Single line comment
SELECT * FROM users; -- inline comment
/* Multi-line
   comment */
WHERE name = 'test';
"""
    result = strip_comments(content, Path("test.sql"))
    assert "-- Single line comment" not in result
    assert "-- inline comment" not in result
    assert "Multi-line" not in result
    assert "SELECT * FROM users;" in result
    assert "WHERE name = 'test';" in result


def test_strip_ruby_comments():
    """Test stripping Ruby # comments."""
    content = """# Ruby comment
x = 5 # inline
y = "# not a comment"
"""
    result = strip_comments(content, Path("test.rb"))
    assert "# Ruby comment" not in result
    assert "# inline" not in result
    assert "# not a comment" in result
    assert "x = 5" in result


def test_strip_lua_comments():
    """Test stripping Lua comments."""
    content = """-- Single line
x = 5 -- inline
--[[ Multi-line
     comment ]]
y = 10
"""
    result = strip_comments(content, Path("test.lua"))
    assert "-- Single line" not in result
    assert "-- inline" not in result
    assert "Multi-line" not in result
    assert "x = 5" in result
    assert "y = 10" in result


def test_strip_haskell_comments():
    """Test stripping Haskell comments."""
    content = """-- Single line
x = 5 -- inline
{- Multi-line
   comment -}
y = 10
"""
    result = strip_comments(content, Path("test.hs"))
    assert "-- Single line" not in result
    assert "-- inline" not in result
    assert "Multi-line" not in result
    assert "x = 5" in result
    assert "y = 10" in result


def test_strip_lisp_comments():
    """Test stripping Lisp ; comments."""
    content = """; Comment
(defun test ()
  (+ 1 2)) ; inline
"""
    result = strip_comments(content, Path("test.lisp"))
    assert "; Comment" not in result
    assert "; inline" not in result
    assert "(defun test ()" in result


def test_unsupported_extension():
    """Test that unsupported extensions return original content."""
    content = "# This should remain"
    result = strip_comments(content, Path("test.unknown"))
    assert result == content


def test_empty_file():
    """Test handling empty files."""
    content = ""
    result = strip_comments(content, Path("test.py"))
    assert result == ""


def test_file_with_only_comments():
    """Test file containing only comments."""
    content = """# Comment 1
# Comment 2
# Comment 3"""
    result = strip_comments(content, Path("test.py"))
    # Result should have no comment markers and only whitespace/newlines
    assert "#" not in result
    assert "Comment" not in result
    # Result should be mostly empty (just whitespace/newlines)
    assert result.strip() == ""


def test_multiline_string_preservation():
    """Test that multi-line strings are preserved."""
    content = '''"""
This is a docstring
with multiple lines
"""
x = 5  # comment
'''
    result = strip_comments(content, Path("test.py"))
    assert "This is a docstring" in result
    assert "with multiple lines" in result
    assert "# comment" not in result


def test_escaped_quotes_in_strings():
    """Test handling of escaped quotes."""
    content = r"""x = "He said \"hello\" # not a comment"
y = 'It\'s working'  # this is a comment
"""
    result = strip_comments(content, Path("test.py"))
    assert 'He said \\"hello\\" # not a comment' in result
    assert "# this is a comment" not in result


def test_unclosed_multiline_comment():
    """Test handling of unclosed multi-line comments."""
    content = """const x = 5;
/* This comment is never closed
const y = 10;"""
    result = strip_comments(content, Path("test.js"))
    # Everything after /* should be removed
    assert "const x = 5;" in result
    assert "This comment" not in result
    assert "const y = 10" not in result


def test_sql_string_preservation():
    """Test SQL comment stripping preserves strings."""
    content = """SELECT '--not a comment' as text; -- real comment
SELECT "column" FROM table; -- another comment"""
    result = strip_comments(content, Path("test.sql"))
    assert "--not a comment" in result
    assert "-- real comment" not in result
    assert "-- another comment" not in result


def test_lua_string_preservation():
    """Test Lua comment stripping preserves strings."""
    content = """local s = "--not a comment" -- real comment
local x = 5"""
    result = strip_comments(content, Path("test.lua"))
    assert "--not a comment" in result
    assert "-- real comment" not in result


def test_haskell_string_preservation():
    """Test Haskell comment stripping preserves strings."""
    content = """s = "--not a comment" -- real comment
x = 5"""
    result = strip_comments(content, Path("test.hs"))
    assert "--not a comment" in result
    assert "-- real comment" not in result


def test_lisp_string_preservation():
    """Test Lisp comment stripping preserves strings."""
    content = """(setq s "; not a comment") ; real comment
(+ 1 2)"""
    result = strip_comments(content, Path("test.lisp"))
    assert "; not a comment" in result
    assert "; real comment" not in result


def test_css_string_preservation():
    """Test CSS comment stripping preserves strings."""
    content = """.class { content: "/* not a comment */"; } /* real comment */
.other { color: red; }"""
    result = strip_comments(content, Path("test.css"))
    assert "/* not a comment */" in result
    assert "/* real comment */" not in result


def test_escaped_backslash_in_strings():
    """Test handling of escaped backslashes."""
    content = r"""x = "\\\\" # comment
y = "\\" # another comment"""
    result = strip_comments(content, Path("test.py"))
    assert r'"\\\\"' in result
    assert r'"\\"' in result
    assert "# comment" not in result
    assert "# another comment" not in result


def test_sql_doubled_quotes():
    """Test SQL with doubled quote escaping."""
    content = """SELECT 'it''s ok' as text; -- comment
SELECT "a""b" FROM table;"""
    result = strip_comments(content, Path("test.sql"))
    assert "'it''s ok'" in result
    assert '"a""b"' in result
    assert "-- comment" not in result


def test_css_escaped_quotes():
    """Test CSS with escaped quotes in strings."""
    content = """.class { content: "test\\"quote"; } /* comment */"""
    result = strip_comments(content, Path("test.css"))
    assert 'test\\"quote' in result
    assert "/* comment */" not in result
