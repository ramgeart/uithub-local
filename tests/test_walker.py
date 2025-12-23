def test_collect_files_exclude_binary(tmp_path):
    from uithub_local.walker import collect_files

    (tmp_path / "bin").write_bytes(b"\0\1")
    (tmp_path / "a.txt").write_text("hi")
    files = collect_files(tmp_path, ["*"], [])
    assert len(files) == 1
    assert files[0].path.name == "a.txt"


def test_collect_files_respects_max_size(tmp_path):
    from uithub_local.walker import collect_files, DEFAULT_MAX_SIZE

    big = tmp_path / "big.txt"
    big.write_bytes(b"x" * (DEFAULT_MAX_SIZE + 1))
    small = tmp_path / "a.txt"
    small.write_text("hi")
    files = collect_files(tmp_path, ["*"], [], max_size=DEFAULT_MAX_SIZE)
    names = {f.path.name for f in files}
    assert names == {"a.txt"}


def test_collect_files_exclude_dir(tmp_path):
    from uithub_local.walker import collect_files

    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("x")
    (tmp_path / "a.txt").write_text("hi")
    files = collect_files(tmp_path, ["*"], [".git"])
    names = {f.path.as_posix() for f in files}
    assert "a.txt" in names
    assert not any(n.startswith(".git/") for n in names)


def test_collect_files_trailing_slash(tmp_path):
    from uithub_local.walker import collect_files

    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "a.txt").write_text("x")
    (tmp_path / "b.txt").write_text("y")

    names = {f.path.as_posix() for f in collect_files(tmp_path, ["*"], ["tests/"])}
    assert "b.txt" in names
    assert not any(n.startswith("tests/") for n in names)


def test_collect_files_trailing_backslash(tmp_path):
    from uithub_local.walker import collect_files

    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "a.txt").write_text("x")
    (tmp_path / "b.txt").write_text("y")

    names = {f.path.as_posix() for f in collect_files(tmp_path, ["*"], ["tests\\"])}
    assert "b.txt" in names
    assert not any(n.startswith("tests/") for n in names)


def test_collect_files_include_leading_dot_slash(tmp_path):
    from uithub_local.walker import collect_files

    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "deep.txt").write_text("data")
    (tmp_path / "root.txt").write_text("root")

    names = {f.path.as_posix() for f in collect_files(tmp_path, ["./nested"], [])}
    assert "nested/deep.txt" in names
    assert "root.txt" not in names


def test_collect_files_exclude_leading_dot_slash(tmp_path):
    from uithub_local.walker import collect_files

    skip = tmp_path / "skip"
    skip.mkdir()
    (skip / "omit.txt").write_text("x")
    (tmp_path / "keep.txt").write_text("y")

    names = {f.path.as_posix() for f in collect_files(tmp_path, ["*"], ["./skip"])}
    assert "keep.txt" in names
    assert not any(n.startswith("skip/") for n in names)


def test_collect_files_respects_gitignore(tmp_path):
    """Test that .gitignore rules are respected by default."""
    from uithub_local.walker import collect_files

    # Create .gitignore file
    (tmp_path / ".gitignore").write_text("*.log\nbuild/\n")
    
    # Create files matching gitignore patterns
    (tmp_path / "app.log").write_text("log data")
    (tmp_path / "debug.log").write_text("debug data")
    
    # Create build directory with files
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (build_dir / "output.txt").write_text("output")
    
    # Create files not matching gitignore patterns
    (tmp_path / "readme.txt").write_text("readme")
    (tmp_path / "app.py").write_text("code")
    
    files = collect_files(tmp_path, ["*"], [])
    names = {f.path.as_posix() for f in files}
    
    # Should include files not in .gitignore
    assert "readme.txt" in names
    assert "app.py" in names
    
    # Should exclude files matching .gitignore
    assert "app.log" not in names
    assert "debug.log" not in names
    assert "build/output.txt" not in names


def test_collect_files_not_ignore_flag(tmp_path):
    """Test that respect_gitignore=False ignores .gitignore rules."""
    from uithub_local.walker import collect_files

    # Create .gitignore file
    (tmp_path / ".gitignore").write_text("*.log\n")
    
    # Create files matching gitignore patterns
    (tmp_path / "app.log").write_text("log data")
    (tmp_path / "readme.txt").write_text("readme")
    
    files = collect_files(tmp_path, ["*"], [], respect_gitignore=False)
    names = {f.path.as_posix() for f in files}
    
    # Should include all files when respect_gitignore=False
    assert "app.log" in names
    assert "readme.txt" in names


def test_collect_files_no_gitignore(tmp_path):
    """Test that collect_files works when no .gitignore exists."""
    from uithub_local.walker import collect_files

    (tmp_path / "app.log").write_text("log data")
    (tmp_path / "readme.txt").write_text("readme")
    
    files = collect_files(tmp_path, ["*"], [])
    names = {f.path.as_posix() for f in files}
    
    # Should include all files when no .gitignore exists
    assert "app.log" in names
    assert "readme.txt" in names
