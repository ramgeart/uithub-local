def test_is_binary_path(tmp_path):
    from uithub_local.utils import is_binary_path

    text = tmp_path / "a.txt"
    text.write_text("hello")
    binary = tmp_path / "b.bin"
    binary.write_bytes(b"\0\1")
    assert not is_binary_path(text)
    assert is_binary_path(binary)


def test_is_binary_path_high_ascii(tmp_path):
    from uithub_local.utils import is_binary_path

    noisy = tmp_path / "noise.txt"
    noisy.write_bytes(b"\x80" * 40 + b"a" * 10)
    assert is_binary_path(noisy)
    assert not is_binary_path(noisy, strict=False)


def test_is_binary_path_code_extensions(tmp_path):
    from uithub_local.utils import is_binary_path

    # Test that common code files are never marked as binary (unless they contain null bytes)
    test_cases = [
        ("main.rs", "fn main() {}"),
        ("lib.py", "def hello(): pass"),
        ("app.js", "console.log('hi');"),
        ("lib.cpp", "int main() { return 0; }"),
        ("prog.go", "package main"),
        ("test.java", "class Test {}"),
        ("script.sh", "#!/bin/bash\necho hi"),
        ("config.toml", '[section]\nkey = "value"'),
        ("data.json", '{"key": "value"}'),
    ]

    for filename, content in test_cases:
        f = tmp_path / filename
        f.write_text(content)
        # Should never be binary (no null bytes)
        assert not is_binary_path(f, strict=True)
        assert not is_binary_path(f, strict=False)

    # Test that code files WITH null bytes ARE marked as binary
    for filename, _ in test_cases:
        f = tmp_path / f"binary_{filename}"
        f.write_bytes(b"\0null byte makes it binary")
        assert is_binary_path(f, strict=True)
        assert is_binary_path(f, strict=False)
