"""Tests for the --split feature."""

from pathlib import Path

from click.testing import CliRunner

from uithub_local.cli import main
from uithub_local.renderer import render_split
from uithub_local.walker import collect_files


def test_split_basic(tmp_path: Path):
    """Test basic split functionality with small files."""
    (tmp_path / "a.txt").write_text("hello world")
    (tmp_path / "b.txt").write_text("foo bar baz")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            str(tmp_path),
            "--split",
            "50",
            "--outfile",
            str(tmp_path / "out.txt"),
            "--no-stdout",
        ],
    )
    assert result.exit_code == 0

    # Check that at least one file was created
    split_files = list(tmp_path.glob(f"{tmp_path.name}_*.txt"))
    assert len(split_files) >= 1

    # Verify files have content
    for f in split_files:
        content = f.read_text()
        assert "Uithub-local dump" in content
        assert "tokens" in content


def test_split_multiple_chunks(tmp_path: Path):
    """Test split produces multiple files when needed."""
    # Create files with enough content to require multiple chunks
    for i in range(10):
        (tmp_path / f"file{i}.txt").write_text("x" * 1000)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            str(tmp_path),
            "--split",
            "500",
            "--outfile",
            str(tmp_path / "out.txt"),
            "--no-stdout",
        ],
    )
    assert result.exit_code == 0

    # Should produce multiple files
    split_files = sorted(tmp_path.glob(f"{tmp_path.name}_*.txt"))
    assert len(split_files) > 1

    # Check filenames are numbered correctly
    for idx, f in enumerate(split_files, start=1):
        assert f.name == f"{tmp_path.name}_{idx}.txt"


def test_split_requires_outfile(tmp_path: Path):
    """Test that --split requires --outfile."""
    (tmp_path / "a.txt").write_text("hello")

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--split", "50"])
    assert result.exit_code != 0
    assert "--split requires --outfile" in result.output


def test_split_invalid_value(tmp_path: Path):
    """Test that --split validates positive integers."""
    (tmp_path / "a.txt").write_text("hello")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [str(tmp_path), "--split", "-1", "--outfile", str(tmp_path / "out.txt")],
    )
    assert result.exit_code != 0
    assert "--split must be a positive integer" in result.output


def test_split_with_json_format(tmp_path: Path):
    """Test split with JSON format."""
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.txt").write_text("world")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            str(tmp_path),
            "--split",
            "20",
            "--format",
            "json",
            "--outfile",
            str(tmp_path / "out.json"),
            "--no-stdout",
        ],
    )
    assert result.exit_code == 0

    # Check JSON files were created
    split_files = list(tmp_path.glob(f"{tmp_path.name}_*.json"))
    assert len(split_files) >= 1

    # Verify JSON is valid
    import json

    for f in split_files:
        data = json.loads(f.read_text())
        assert "repo" in data
        assert "total_tokens" in data
        assert "files" in data


def test_split_with_html_format(tmp_path: Path):
    """Test split with HTML format."""
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.txt").write_text("world")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            str(tmp_path),
            "--split",
            "20",
            "--format",
            "html",
            "--outfile",
            str(tmp_path / "out.html"),
            "--no-stdout",
        ],
    )
    assert result.exit_code == 0

    # Check HTML files were created
    split_files = list(tmp_path.glob(f"{tmp_path.name}_*.html"))
    assert len(split_files) >= 1

    # Verify HTML structure
    for f in split_files:
        content = f.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<h1>Uithub-local dump" in content


def test_render_split_function(tmp_path: Path):
    """Test render_split function directly."""
    (tmp_path / "a.txt").write_text("a" * 100)
    (tmp_path / "b.txt").write_text("b" * 100)
    (tmp_path / "c.txt").write_text("c" * 100)

    files = collect_files(tmp_path, ["*.txt"], [])
    outputs = render_split(files, tmp_path, split_tokens=50)

    # Should produce multiple outputs
    assert len(outputs) > 1

    # Each output should be a (filename, content) tuple
    for filename, content in outputs:
        assert filename.endswith(".txt")
        assert f"{tmp_path.name}_" in filename
        assert "Uithub-local dump" in content
        assert "tokens" in content


def test_split_with_max_tokens(tmp_path: Path):
    """Test split combined with max_tokens truncation."""
    # Create multiple files
    for i in range(10):
        (tmp_path / f"file{i}.txt").write_text("x" * 100)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            str(tmp_path),
            "--split",
            "50",
            "--max-tokens",
            "100",
            "--outfile",
            str(tmp_path / "out.txt"),
            "--no-stdout",
        ],
    )
    assert result.exit_code == 0

    # Check files were created
    split_files = list(tmp_path.glob(f"{tmp_path.name}_*.txt"))
    assert len(split_files) >= 1


def test_split_single_large_file(tmp_path: Path):
    """Test split with a single file that exceeds split limit."""
    (tmp_path / "large.txt").write_text("x" * 10000)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            str(tmp_path),
            "--split",
            "100",
            "--outfile",
            str(tmp_path / "out.txt"),
            "--no-stdout",
        ],
    )
    assert result.exit_code == 0

    # Should create at least one file (single large file can't be split further)
    split_files = list(tmp_path.glob(f"{tmp_path.name}_*.txt"))
    assert len(split_files) >= 1
