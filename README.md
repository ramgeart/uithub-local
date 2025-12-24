# uithub-local

Flatten a local Git repository into a single text dump with an approximate token count.

## About
Uithub-local packages repository contents into plain text, JSON or HTML dumps. Use it to prep code for large-context LLMs or save lightweight archives. It now includes a built-in REST API and Docker support.

## Quick Start

```bash
pip install .

# Process local repository (PATH argument or --local-path option)
uithub path/to/repo --include "*.py" --exclude "tests/"
uithub --local-path path/to/repo --include "*.py" --exclude "tests/"

# Process remote repository
uithub --remote-url https://github.com/owner/repo

# Start the REST API server
uithub --serve --port 8000
```

## Usage

Run `uithub --help` for all options. The dump can be printed to STDOUT or saved to a file. JSON output is available using `--format json`. Use `--format html` for a self-contained HTML dump with collapsible sections. 

### CLI Options

- `PATH` or `--local-path`: Local directory to process.
- `--remote-url`: Git repository URL to download.
- `--include`/`--exclude`: Glob patterns (now supports comma-separated strings).
- `--max-size`: Skip files larger than this many bytes (default: 1MB).
- `--max-tokens`: Hard token cap for the entire dump.
- `--split`: Split output into multiple files of N tokens each.
- `--format`: Output format (`text`, `json`, `html`).
- `--exclude-comments`: Strip code comments.
- `--not-ignore`: Do not respect `.gitignore` rules.
- `--serve`: Start the REST API server.
- `--host`/`--port`: Server configuration for the API.

### REST API

You can start a REST API server to expose the `uithub-local` functionality over network:

```bash
uithub --serve --host 0.0.0.0 --port 8000
```

The API strictly supports remote repositories via `remote_url`.

#### Authentication
The API supports both a `private_token` parameter and standard **HTTP Bearer** authentication. If a Bearer token is provided in the `Authorization` header, it will take precedence.

#### Endpoints
- `POST /dump`: Accepts a JSON body with processing options.
- `GET /dump`: Accepts processing options as query parameters.
- `GET /dump/{user}/{repo}`: Directly process a GitHub repository.
    - Example: `GET /dump/google/gemini-cli?exclude=*.py`
- `POST /dump/{user}/{repo}`: Process a GitHub repository with optional JSON body for overrides.

#### Splitting and Formats
- **Splitting**: Provide a `split` parameter (integer) to receive a JSON response containing multiple parts.
- **Formats**: Supports `text`, `json`, and `html`.
    - If `format=json` is used without `split`, the response is a single JSON object with the dump content.
    - If `format=text` or `html`, the raw content is returned with the appropriate media type.

#### Interactive Documentation
Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`
- OpenAPI Spec (YAML): `http://localhost:8000/openapi.yaml`

### Docker Support

Uithub-local can be run as a containerized service:

```bash
# Build the image
docker build -t uithub-local .

# Run the API server
docker run -p 8000:8000 uithub-local
```

### Respecting .gitignore

By default, uithub respects `.gitignore` rules. Use `--not-ignore` to disable this:

```bash
uithub path/to/repo --not-ignore
```

### Excluding comments

Use `--exclude-comments` to strip code comments from the output:

```bash
uithub path/to/repo --exclude-comments
```

### Splitting large outputs

Use `--split N` to divide output into multiple files of ~$N$ tokens:

```bash
uithub path/to/repo --split 30000 --outfile output.txt
```

## Changelog

### 0.1.8 (Unreleased)
- Added `--serve` option to start a FastAPI REST API server.
- Added `--host` and `--port` options for server configuration.
- Added `Dockerfile` and GitHub Action for GHCR publishing.
- Added OpenAPI 3.1.0 specification support.
- Added `--local-path` option as an explicit alternative to the PATH argument.

### 0.1.7
- Added `.gitignore` support: files matching patterns in `.gitignore` are now excluded by default.
- Added `--not-ignore` flag to disable `.gitignore` processing.

### 0.1.6
- Added support for comma-separated patterns in `--include` and `--exclude` options.
- Example: `--exclude "*.html,*.js,*.css"` is now equivalent to multiple flags.

### 0.1.5
- Added `--split N` option to divide output into multiple files of N tokens each.
- Split works with all formats (text, JSON, HTML).

### 0.1.4
- Added `--exclude-comments` flag to strip code comments from output.
- Supports 20+ languages with intelligent string literal preservation.

### 0.1.3
- Directory patterns now match recursively.
- `.git/` is excluded automatically unless explicitly included.
- Correct repo name shown when dumping `.`.

### 0.1.2
- Added `--encoding` option for file output.
- Fixed UTF-8 writes when saving dumps.

### 0.1.1
- HTML export improvements.
- Programmatic `dump_repo` helper function.
- Coverage gate at 90%.

### 0.1.0
- Initial release.
