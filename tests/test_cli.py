from pathlib import Path

from click.testing import CliRunner
import io
import zipfile
import responses

from uithub_local.cli import main


def test_cli_basic(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hello")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert "hello" in result.output


def test_cli_outfile(tmp_path: Path):
    from click.testing import CliRunner

    (tmp_path / "a.txt").write_text("hello")
    outfile = tmp_path / "out.txt"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(tmp_path), "--outfile", str(outfile), "--no-stdout"],
    )
    assert result.exit_code == 0
    assert outfile.read_text()


def test_cli_outfile_utf8(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hi")
    out = tmp_path / "out.txt"
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--outfile", str(out)])
    assert result.exit_code == 0
    assert out.read_text(encoding="utf-8").startswith("# Uithub-local")


def test_cli_outfile_cp1252(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hi")
    out = tmp_path / "o.txt"
    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(tmp_path), "--outfile", str(out), "--encoding", "cp1252", "--no-stdout"],
    )
    assert result.exit_code == 0
    assert out.read_text(encoding="cp1252").startswith("# Uithub-local")


def test_cli_max_size(tmp_path: Path):
    from uithub_local.walker import DEFAULT_MAX_SIZE

    big = tmp_path / "big.txt"
    big.write_bytes(b"x" * (DEFAULT_MAX_SIZE + 1))
    (tmp_path / "small.txt").write_text("ok")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert "big.txt" not in result.output
    result = runner.invoke(
        main, [str(tmp_path), "--max-size", str(DEFAULT_MAX_SIZE * 2)]
    )
    assert result.exit_code == 0
    assert "big.txt" in result.output


@responses.activate
def test_cli_remote(tmp_path: Path):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as zf:
        zf.writestr("repo/file.txt", "hi")
    responses.add(
        responses.GET,
        "https://api.github.com/repos/foo/bar/zipball",
        body=data.getvalue(),
        status=200,
        content_type="application/zip",
    )
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--remote-url", "https://github.com/foo/bar"],
    )
    assert result.exit_code == 0
    assert "file.txt" in result.output
    assert "hi" in result.output


def test_cli_no_binary_strict(tmp_path: Path):
    noisy = tmp_path / "n.txt"
    noisy.write_bytes(b"\x80" * 40 + b"a" * 10)
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--no-binary-strict"])
    assert result.exit_code == 0
    assert "n.txt" in result.output


def test_cli_html(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hello")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--format", "html"])
    assert result.exit_code == 0
    assert "<details class='file-card'>" in result.output


def test_cli_exclude_directory(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "data").write_text("x")
    (tmp_path / "a.txt").write_text("hi")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--exclude", ".git"])
    assert result.exit_code == 0
    assert ".git/data" not in result.output
    assert "a.txt" in result.output


def test_cli_exclude_tests(tmp_path: Path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "a.txt").write_text("x")
    (tmp_path / "b.txt").write_text("y")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--exclude", "tests/"])
    assert result.exit_code == 0
    assert "tests/a.txt" not in result.output
    assert "b.txt" in result.output


def test_cli_auto_excludes_git(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x")
    (tmp_path / "a.txt").write_text("hi")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert ".git/config" not in result.output


def test_cli_exclude_comments(tmp_path: Path):
    (tmp_path / "script.py").write_text("# This is a comment\nx = 5  # inline\ny = 10")
    (tmp_path / "code.js").write_text("// Comment\nconst x = 5; // inline")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--exclude-comments"])
    assert result.exit_code == 0
    assert "# This is a comment" not in result.output
    assert "# inline" not in result.output
    assert "// Comment" not in result.output
    assert "// inline" not in result.output
    assert "x = 5" in result.output
    assert "const x = 5;" in result.output


def test_cli_exclude_comments_preserves_strings(tmp_path: Path):
    (tmp_path / "test.py").write_text('x = "# not a comment"  # real comment')
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--exclude-comments"])
    assert result.exit_code == 0
    assert "# not a comment" in result.output
    assert "# real comment" not in result.output


def test_cli_exclude_comma_separated(tmp_path: Path):
    """Test that --exclude accepts comma-separated patterns."""
    (tmp_path / "file.html").write_text("html content")
    (tmp_path / "script.js").write_text("js content")
    (tmp_path / "readme.md").write_text("md content")
    (tmp_path / "readme.txt").write_text("txt content")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--exclude", "*.html,*.js"])
    assert result.exit_code == 0
    assert "file.html" not in result.output
    assert "script.js" not in result.output
    assert "readme.md" in result.output
    assert "readme.txt" in result.output


def test_cli_include_comma_separated(tmp_path: Path):
    """Test that --include accepts comma-separated patterns."""
    (tmp_path / "file.py").write_text("py content")
    (tmp_path / "script.js").write_text("js content")
    (tmp_path / "readme.md").write_text("md content")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--include", "*.py,*.js"])
    assert result.exit_code == 0
    assert "file.py" in result.output
    assert "script.js" in result.output
    assert "readme.md" not in result.output


def test_cli_comma_separated_with_spaces(tmp_path: Path):
    """Test that comma-separated patterns handle spaces correctly."""
    (tmp_path / "file.html").write_text("html content")
    (tmp_path / "script.js").write_text("js content")
    (tmp_path / "readme.txt").write_text("txt content")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--exclude", "*.html, *.js"])
    assert result.exit_code == 0
    assert "file.html" not in result.output
    assert "script.js" not in result.output
    assert "readme.txt" in result.output


def test_cli_respects_gitignore(tmp_path: Path):
    """Test that CLI respects .gitignore by default."""
    (tmp_path / ".gitignore").write_text("*.log\n")
    (tmp_path / "app.log").write_text("log data")
    (tmp_path / "readme.txt").write_text("readme")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert "app.log" not in result.output
    assert "readme.txt" in result.output


def test_cli_not_ignore_flag(tmp_path: Path):
    """Test that --not-ignore flag disables .gitignore."""
    (tmp_path / ".gitignore").write_text("*.log\n")
    (tmp_path / "app.log").write_text("log data")
    (tmp_path / "readme.txt").write_text("readme")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--not-ignore"])
    assert result.exit_code == 0
    assert "app.log" in result.output
    assert "readme.txt" in result.output


def test_cli_local_path_option(tmp_path: Path):
    """Test that --local-path option works."""
    (tmp_path / "file.txt").write_text("content")
    runner = CliRunner()
    result = runner.invoke(main, ["--local-path", str(tmp_path)])
    assert result.exit_code == 0
    assert "file.txt" in result.output
    assert "content" in result.output


def test_cli_local_path_with_subdirs(tmp_path: Path):
    """Test that --local-path traverses subdirectories."""
    (tmp_path / "root.txt").write_text("root")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("nested")
    runner = CliRunner()
    result = runner.invoke(main, ["--local-path", str(tmp_path)])
    assert result.exit_code == 0
    assert "root.txt" in result.output
    assert "subdir/nested.txt" in result.output
    assert "nested" in result.output


def test_cli_local_path_mutually_exclusive_with_path(tmp_path: Path):
    """Test that PATH and --local-path cannot be used together."""
    (tmp_path / "file.txt").write_text("content")
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--local-path", str(tmp_path)])
    assert result.exit_code == 2
    assert "Only one of PATH, --local-path, or --remote-url can be used" in result.output


def test_cli_local_path_mutually_exclusive_with_remote(tmp_path: Path):
    """Test that --local-path and --remote-url cannot be used together."""
    (tmp_path / "file.txt").write_text("content")
    runner = CliRunner()
    result = runner.invoke(
        main, ["--local-path", str(tmp_path), "--remote-url", "https://github.com/foo/bar"]
    )
    assert result.exit_code == 2
    assert "Only one of PATH, --local-path, or --remote-url can be used" in result.output


def test_cli_path_mutually_exclusive_with_remote(tmp_path: Path):
    """Test that PATH and --remote-url cannot be used together."""
    (tmp_path / "file.txt").write_text("content")
    runner = CliRunner()
    result = runner.invoke(
        main, [str(tmp_path), "--remote-url", "https://github.com/foo/bar"]
    )
    assert result.exit_code == 2
    assert "Only one of PATH, --local-path, or --remote-url can be used" in result.output


def test_cli_requires_path_source():
    """Test that at least one path source is required."""
    runner = CliRunner()
    result = runner.invoke(main, [])
    assert result.exit_code == 2
    assert "One of PATH, --local-path, or --remote-url is required" in result.output

