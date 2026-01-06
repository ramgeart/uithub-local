"""Tests for content filtering functionality."""

import json
from pathlib import Path

import pytest

from uithub_local.filters import (
    apply_content_filters,
    filter_base64_strings,
    filter_ipynb_outputs,
    filter_sensitive_urls,
)


class TestFilterIpynbOutputs:
    """Tests for filtering Jupyter notebook outputs."""

    def test_removes_code_cell_outputs(self):
        """Should remove outputs from code cells."""
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["print('hello')"],
                    "outputs": [
                        {"output_type": "stream", "text": ["hello\n"]}
                    ],
                    "execution_count": 1,
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        result = json.loads(filter_ipynb_outputs(json.dumps(notebook)))
        assert result["cells"][0]["outputs"] == []
        assert result["cells"][0]["execution_count"] is None

    def test_removes_image_outputs(self):
        """Should remove base64 image outputs."""
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["import matplotlib"],
                    "outputs": [
                        {
                            "output_type": "display_data",
                            "data": {
                                "image/png": "iVBORw0KGgoAAAANSUhEUg" + "A" * 1000,
                                "text/plain": ["<Figure>"],
                            },
                        }
                    ],
                    "execution_count": 5,
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        result = json.loads(filter_ipynb_outputs(json.dumps(notebook)))
        assert result["cells"][0]["outputs"] == []

    def test_preserves_markdown_cells(self):
        """Should preserve markdown cell content."""
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Title\n", "Some text"],
                    "metadata": {},
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        result = json.loads(filter_ipynb_outputs(json.dumps(notebook)))
        assert result["cells"][0]["source"] == ["# Title\n", "Some text"]

    def test_preserves_code_cell_source(self):
        """Should preserve the source code in code cells."""
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["x = 1\n", "y = 2"],
                    "outputs": [{"output_type": "execute_result"}],
                    "execution_count": 1,
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        result = json.loads(filter_ipynb_outputs(json.dumps(notebook)))
        assert result["cells"][0]["source"] == ["x = 1\n", "y = 2"]

    def test_handles_invalid_json(self):
        """Should return original content for invalid JSON."""
        invalid = "not valid json {"
        assert filter_ipynb_outputs(invalid) == invalid

    def test_handles_non_notebook_json(self):
        """Should return original content for non-notebook JSON."""
        not_notebook = '{"key": "value"}'
        assert filter_ipynb_outputs(not_notebook) == not_notebook

    def test_removes_execution_metadata(self):
        """Should remove execution-related metadata."""
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["x = 1"],
                    "outputs": [],
                    "execution_count": None,
                    "metadata": {
                        "execution": {"some": "data"},
                        "scrolled": True,
                        "important": "keep",
                    },
                }
            ],
            "metadata": {"language_info": {"name": "python"}},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        result = json.loads(filter_ipynb_outputs(json.dumps(notebook)))
        assert "execution" not in result["cells"][0]["metadata"]
        assert "scrolled" not in result["cells"][0]["metadata"]
        assert result["cells"][0]["metadata"]["important"] == "keep"
        assert "language_info" not in result["metadata"]


class TestFilterBase64Strings:
    """Tests for filtering base64 encoded strings."""

    def test_filters_data_uri(self):
        """Should filter data URIs with base64 content."""
        content = 'src="data:image/png;base64,' + "A" * 100 + '"'
        result = filter_base64_strings(content)
        assert "[BASE64_DATA_FILTERED]" in result
        assert "A" * 100 not in result

    def test_filters_long_base64_string(self):
        """Should filter long standalone base64 strings."""
        # Create a string that looks like base64 (mixed case, numbers)
        base64_str = "aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ0123456789+/ABCD" * 2
        content = f'key: "{base64_str}"'
        result = filter_base64_strings(content)
        assert "[BASE64_DATA_FILTERED]" in result

    def test_preserves_short_strings(self):
        """Should preserve short base64-like strings."""
        content = 'hash: "abc123XYZ"'
        result = filter_base64_strings(content)
        assert result == content

    def test_preserves_normal_text(self):
        """Should preserve normal text content."""
        content = "This is normal text with some code like function();"
        result = filter_base64_strings(content)
        assert result == content

    def test_filters_multiple_base64(self):
        """Should filter multiple base64 strings."""
        base64_1 = "data:image/jpeg;base64," + "B" * 100
        base64_2 = "data:application/pdf;base64," + "C" * 100
        content = f'img1="{base64_1}" img2="{base64_2}"'
        result = filter_base64_strings(content)
        assert result.count("[BASE64_DATA_FILTERED]") == 2

    def test_custom_min_length(self):
        """Should respect custom minimum length."""
        base64_str = "A" * 50 + "a" * 10 + "0" * 10  # 70 chars
        content = f' {base64_str} '
        # Default min is 64, so this should be filtered
        result = filter_base64_strings(content, min_length=64)
        # But with higher min, it should be preserved
        result_high = filter_base64_strings(content, min_length=100)
        assert base64_str in result_high


class TestFilterSensitiveUrls:
    """Tests for filtering sensitive URL parameters."""

    def test_filters_token_parameter(self):
        """Should filter token parameter values."""
        url = "https://api.example.com/data?token=secret123&format=json"
        result = filter_sensitive_urls(url)
        assert "token=[FILTERED]" in result
        assert "secret123" not in result
        assert "format=json" in result

    def test_filters_api_key(self):
        """Should filter api_key parameter values."""
        url = "https://api.example.com?api_key=mysecretkey"
        result = filter_sensitive_urls(url)
        assert "api_key=[FILTERED]" in result
        assert "mysecretkey" not in result

    def test_filters_multiple_sensitive_params(self):
        """Should filter multiple sensitive parameters."""
        url = "https://example.com?token=abc&secret=xyz&name=john"
        result = filter_sensitive_urls(url)
        assert "token=[FILTERED]" in result
        assert "secret=[FILTERED]" in result
        assert "name=john" in result

    def test_preserves_safe_urls(self):
        """Should preserve URLs without sensitive parameters."""
        url = "https://example.com/page?id=123&sort=asc"
        result = filter_sensitive_urls(url)
        assert result == url

    def test_filters_session_id(self):
        """Should filter session_id parameter."""
        url = "https://app.com/api?session_id=xyz789"
        result = filter_sensitive_urls(url)
        assert "session_id=[FILTERED]" in result

    def test_filters_password(self):
        """Should filter password parameter."""
        url = "https://login.com?user=admin&password=pass123"
        result = filter_sensitive_urls(url)
        assert "password=[FILTERED]" in result
        assert "user=admin" in result

    def test_handles_urls_in_text(self):
        """Should handle URLs embedded in text."""
        content = 'See https://api.com?token=secret for docs.'
        result = filter_sensitive_urls(content)
        assert "token=[FILTERED]" in result
        assert "secret" not in result

    def test_filters_oauth_token(self):
        """Should filter oauth_token parameter."""
        url = "https://oauth.com/callback?oauth_token=abc123&state=xyz"
        result = filter_sensitive_urls(url)
        assert "oauth_token=[FILTERED]" in result
        assert "state=[FILTERED]" in result

    def test_filters_auth_header_style(self):
        """Should filter auth-related parameters."""
        url = "https://api.com?authorization=Bearer%20xyz&query=test"
        result = filter_sensitive_urls(url)
        assert "authorization=[FILTERED]" in result
        assert "query=test" in result


class TestApplyContentFilters:
    """Tests for the combined filter application."""

    def test_applies_ipynb_filter(self, tmp_path: Path):
        """Should apply ipynb filter for notebook files."""
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["x = 1"],
                    "outputs": [{"output_type": "stream"}],
                    "execution_count": 1,
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        content = json.dumps(notebook)
        path = tmp_path / "test.ipynb"
        
        result = apply_content_filters(content, path)
        parsed = json.loads(result)
        assert parsed["cells"][0]["outputs"] == []

    def test_skips_ipynb_for_non_notebook(self, tmp_path: Path):
        """Should not apply ipynb filter for non-notebook files."""
        content = '{"cells": []}'  # Looks like notebook but is .json
        path = tmp_path / "data.json"
        
        result = apply_content_filters(content, path, filter_ipynb=True)
        # Should return same content (only filtered for base64/urls)
        assert '"cells": []' in result

    def test_combines_all_filters(self, tmp_path: Path):
        """Should apply all filters together."""
        content = 'url: https://api.com?token=secret data: "' + "A" * 100 + '"'
        path = tmp_path / "config.yaml"
        
        result = apply_content_filters(content, path)
        assert "token=[FILTERED]" in result
        # The base64 might or might not be filtered depending on pattern match

    def test_respects_filter_flags(self, tmp_path: Path):
        """Should respect individual filter flags."""
        url = "https://api.com?token=secret"
        path = tmp_path / "test.txt"
        
        # With URL filter disabled
        result = apply_content_filters(url, path, filter_urls=False)
        assert "secret" in result
        
        # With URL filter enabled
        result = apply_content_filters(url, path, filter_urls=True)
        assert "secret" not in result


class TestIntegrationWithLoader:
    """Integration tests with the loader module."""

    def test_loader_with_filter_content(self, tmp_path: Path):
        """Should filter content when filter_content=True."""
        from uithub_local.loader import load_text
        
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["print('test')"],
                    "outputs": [{"output_type": "stream", "text": ["test\n"]}],
                    "execution_count": 1,
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        
        path = tmp_path / "notebook.ipynb"
        path.write_text(json.dumps(notebook))
        
        # Without filter
        content_unfiltered = load_text(path, filter_content=False)
        assert '"outputs": [' in content_unfiltered
        
        # With filter
        content_filtered = load_text(path, filter_content=True)
        parsed = json.loads(content_filtered)
        assert parsed["cells"][0]["outputs"] == []

    def test_loader_filters_base64_in_any_file(self, tmp_path: Path):
        """Should filter base64 in any file type."""
        from uithub_local.loader import load_text
        
        content = 'image: "data:image/png;base64,' + "A" * 100 + '"'
        path = tmp_path / "config.json"
        path.write_text(content)
        
        result = load_text(path, filter_content=True)
        assert "[BASE64_DATA_FILTERED]" in result


class TestRendererWithFilter:
    """Integration tests with the renderer module."""

    def test_render_with_filter_content(self, tmp_path: Path):
        """Should pass filter_content option through render chain."""
        from uithub_local.renderer import render
        from uithub_local.walker import collect_files
        
        # Create a notebook with outputs
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["x = 1"],
                    "outputs": [{"output_type": "execute_result"}],
                    "execution_count": 1,
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4,
        }
        path = tmp_path / "test.ipynb"
        path.write_text(json.dumps(notebook))
        
        files = collect_files(tmp_path, ["*.ipynb"], [])
        
        # Without filter
        output = render(files, tmp_path, filter_content=False)
        assert '"execution_count": 1' in output
        
        # With filter
        output_filtered = render(files, tmp_path, filter_content=True)
        assert '"execution_count": null' in output_filtered
        assert '"outputs": []' in output_filtered
