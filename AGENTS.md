# AGENTS.md – Local Uithub Project Guide for OpenAI Codex

## 1 Project Goal

Build a **local Uithub clone** named **`uithub-local`**.
The tool flattens any Git repository (or plain folder) into **one plain‑text dump** that shows every file’s *relative path* followed by its *full contents*, then prints an **approximate token count** for the entire dump.

## 2 Scope & Non‑Goals

* **Scope:** command‑line interface (CLI) + importable Python package.
* **Out of scope:** web GUI, authentication, Git operations beyond simple checkout detection.

## 3 Directory Layout

```
/ (repo root)
├── src/
│   └── uithub_local/
│       ├── __init__.py
│       ├── cli.py         # `uithub` entry‑point
│       ├── walker.py      # collects file paths & metadata
│       ├── loader.py      # reads files safely, handles encodings
│       ├── renderer.py    # builds flattened dump string
│       ├── tokenizer.py   # token counting helpers
│       └── utils.py       # shared helpers
├── tests/
│   ├── test_cli.py
│   ├── test_renderer.py
│   └── test_tokenizer.py
├── pyproject.toml
└── README.md
```

## 4 Coding Conventions

* **Language:** Python ≥3.11, typed (PEP 484).
* **Style:** `ruff` + `black` (pyproject preset).
* **Docstrings:** PEP 257 + Google style.
* **Imports:** absolute within `uithub_local`.
* **Logging:** use `logging` not `print` (except CLI final dump).

## 5 CLI Contract

```
Usage: uithub [OPTIONS] <path>

Options:
  --include PATTERN [...]     Glob(s) to include (default *).
  --exclude PATTERN [...]     Glob(s) to exclude.
  --max-tokens INTEGER        Hard cap; truncate largest files first.
  --format [text|json]        Output format (default text).
  --stdout / --no-stdout      Print dump to STDOUT (default yes).
  --outfile FILE              Write dump to file.
  --version / -V              Show version.
```

## 6 Token Counting Rules

1. Prefer **`tiktoken`** (`cl100k_base`) when available.
2. Fallback: 1 token ≈ 4 characters.
3. Count tokens **after** any truncation.
4. Expose `tokenizer.approximate_tokens(text: str) -> int` and `total_tokens(files: Iterable[Path]) -> int`.

## 7 Binary Detection & File Filtering

The tool skips binary and non‑readable files automatically:

* Files containing null bytes (`\0`) are always treated as binary.
* MIME type guessing (`mimetypes.guess_type`) is used for unknown extensions.
* Common source‑code extensions (`.rs`, `.py`, `.js`, `.cpp`, etc.) are **always** treated as text regardless of MIME type. See `CODE_EXTENSIONS` in `utils.py` for the full list.
* With `--binary-strict` (default), files with >30 % non‑printable/UTF‑8 characters (excluding common whitespace) are also marked binary.
* Files matching `.gitignore` are skipped unless `--not‑ignore` is set.

## 8 Rendering Spec

For each file, output:

```text
### <relative/path/to/file.ext>
<file contents>
```

Between files there is a blank line.  Top of dump:

```text
# Uithub‑local dump – <repo name> – <ISO timestamp>
# ≈ <TOKEN_COUNT> tokens
```

## 9 Testing

* Use **`pytest`**.
* Achieve ≥90 % statement coverage.  Command:

```bash
pytest --cov=uithub_local -q
```

* Include golden‑file test for renderer output.

## 10 Programmatic Checks

Add these tasks to **`[tool.ruff]`**, **`[tool.black]`** and **`[tool.mypy]`** in *pyproject.toml*.
CI script must run: `ruff check`, `black --check`, `mypy`, `pytest`.

## 11 Pull‑Request Guidelines (for Codex‑generated PRs)

1. Title: `feat: ...`, `fix: ...`, `docs: ...` etc.
2. Description must list **changes**, **rationale**, **tests added**, **manual QA steps**.
3. One logical concern per PR.
4. All programmatic checks and tests must pass.

## 12 Security & Robustness

* Skip files >1 MiB by default unless user forces via `--include`.
* Detect binary files by `mimetypes` or null bytes and skip.
* Handle encoding errors gracefully with `errors="replace"`.

## 13 Future Extensions (placeholders only)

* HTML renderer with collapsible file sections.
* JSON output compatible with RAG loaders.

---

**End of AGENTS.md**
