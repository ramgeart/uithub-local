from pathlib import Path

from uithub_local import dump_repo


def test_dump_repo(tmp_path: Path):
    (tmp_path / "a.txt").write_text("hi")
    output = dump_repo(tmp_path, fmt="text")
    assert "hi" in output


def test_dump_repo_exclude_comments(tmp_path: Path):
    (tmp_path / "script.py").write_text("# Comment\nx = 5  # inline")
    output = dump_repo(tmp_path, fmt="text", exclude_comments=True)
    assert "# Comment" not in output
    assert "# inline" not in output
    assert "x = 5" in output


def test_dump_repo_exclude_comments_json(tmp_path: Path):
    import json

    (tmp_path / "code.js").write_text("// Comment\nconst x = 5;")
    output = dump_repo(tmp_path, fmt="json", exclude_comments=True)
    data = json.loads(output)
    content = data["files"][0]["contents"]
    assert "// Comment" not in content
    assert "const x = 5;" in content
