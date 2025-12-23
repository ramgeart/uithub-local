# uithub-local

Flatten a local Git repository into a single text dump with an approximate token count.

## About
Uithub-local packages repository contents into plain text, JSON or HTML dumps. Use it to prep code for large-context LLMs or save lightweight archives.

## Quick Start

```bash
pip install .

# trailing slash means recursive
uithub path/to/repo --include "*.py" --exclude "tests/"
uithub --remote-url https://github.com/owner/repo

# Comma-separated patterns (new in 0.1.6)
uithub path/to/repo --exclude "*.html,*.js,*.css"
uithub path/to/repo --include "*.py,*.js,*.md"
```

## Usage

Run `uithub --help` for all options. The dump can be printed to STDOUT or saved to a file. JSON output is available using `--format json`. Use `--format html` for a self-contained HTML dump with collapsible sections. Remote repositories can be processed with `--remote-url`; provide `--private-token` or set `GITHUB_TOKEN` for private repos. Use `--max-size` to skip files larger than the given number of bytes (default 1048576).
`.git/` directories are skipped automatically unless explicitly included.

Both `--include` and `--exclude` options support comma-separated patterns for convenience. For example, `--exclude "*.html,*.js"` is equivalent to `--exclude "*.html" --exclude "*.js"`.

### Respecting .gitignore

By default, uithub respects `.gitignore` rules and excludes files matching patterns in the `.gitignore` file. This helps exclude common build artifacts, dependencies, and temporary files:

```bash
# Default behavior: respects .gitignore
uithub path/to/repo

# Disable .gitignore: include all files
uithub path/to/repo --not-ignore
```

### Excluding comments

Use `--exclude-comments` to strip code comments from the output, reducing token count by 30-50% on typical codebases:

```bash
uithub path/to/repo --exclude-comments
```

This feature intelligently removes comments based on file extensions while preserving string literals. Supported languages include Python, JavaScript/TypeScript, Java, C/C++, Go, Rust, Ruby, SQL, HTML/CSS, Lua, Haskell, Lisp, and more.

### Splitting large outputs

Use `--split N` to divide output into multiple files, each with approximately N tokens. This is useful when working with LLMs that have context window limits:

```bash
uithub path/to/repo --split 30000 --outfile output.txt
```

This creates files named `<reponame>_1.txt`, `<reponame>_2.txt`, etc., each containing up to 30,000 tokens. The `--split` option works with all formats (text, JSON, HTML) and requires `--outfile` so it can determine the output directory from the provided file path.

### HTML and JSON output

To save an HTML dump and open it in your default browser:

```bash
uithub path/to/repo --format html --outfile dump.html && xdg-open dump.html
```

The generated HTML arranges files in collapsible "file cards" styled for a dark
theme. Cards sit on a charcoal background with light text and a bright blue
accent. A small chevron rotates when a card is opened, and file paths truncate
in the middle to keep extensions visible. Code blocks scroll horizontally and
cards are stacked in a centred container with a subtle drop shadow.

Save a plain text dump with explicit encoding:

```bash
uithub path/to/repo --outfile dump.txt --encoding utf-8
```

### Running the test-suite

Install development dependencies and run tests with coverage:

```bash
pip install .[test]
pytest --cov=uithub_local -q
```

### Adjusting file size limit

The `--max-size` option expects bytes. Raise it if needed, e.g.:

```bash
uithub path/to/repo --max-size $((2 * 1048576))
```

## Changelog

### 0.1.7
- Added `.gitignore` support: files matching patterns in `.gitignore` are now excluded by default.
- Added `--not-ignore` flag to disable `.gitignore` processing and include all files.

### 0.1.6
- Added support for comma-separated patterns in `--include` and `--exclude` options.
- Example: `--exclude "*.html,*.js,*.css"` is now equivalent to multiple `--exclude` flags.

### 0.1.5
- Added `--split N` option to divide output into multiple files of N tokens each.
- Split works with all formats (text, JSON, HTML).
- Useful for working with LLM context window limits.

### 0.1.4
- Added `--exclude-comments` flag to strip code comments from output.
- Supports 20+ languages with intelligent string literal preservation.
- Improved escape sequence handling for backslashes in strings.

### 0.1.3
- Directory patterns now match recursively ("dir/" excludes everything under it).
- `.git/` is excluded automatically unless explicitly included.
- Correct repo name shown when dumping `.`.
### 0.1.2
- Added ``--encoding`` option for file output.
- Fixed UTF-8 writes when saving dumps.

### 0.1.1
- HTML export improvements (lang attribute, mobile viewport, truncated summaries).
- Programmatic `dump_repo` helper function.
- Coverage gate at 90%.

### 0.1.0
- Initial release.
