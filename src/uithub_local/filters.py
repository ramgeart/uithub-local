"""Content filtering utilities to reduce noise and sensitive data in dumps.

This module provides filters for:
- Jupyter notebook (.ipynb) outputs
- Base64 encoded strings
- URLs with tokens, cookies, or other sensitive data
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Minimum length for a base64 string to be considered for filtering
# Short base64 strings (like short hashes) are usually fine
MIN_BASE64_LENGTH = 64

# Common sensitive URL query parameter names
SENSITIVE_PARAMS = frozenset({
    # Authentication/Authorization
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "api-key",
    "auth",
    "auth_token",
    "authorization",
    "bearer",
    "jwt",
    "session",
    "session_id",
    "sessionid",
    "sid",
    # Secrets and keys
    "secret",
    "secret_key",
    "secretkey",
    "client_secret",
    "private_key",
    "privatekey",
    "key",
    # Cookies and credentials
    "cookie",
    "cookies",
    "password",
    "passwd",
    "pwd",
    "credential",
    "credentials",
    # OAuth
    "oauth",
    "oauth_token",
    "code",
    "state",
    # AWS
    "aws_access_key_id",
    "aws_secret_access_key",
    "x-amz-security-token",
    # Other
    "signature",
    "sig",
    "sign",
    "hash",
    "nonce",
})

# Core sensitive keywords that should trigger substring matching
# These are common prefixes/suffixes that indicate sensitive data
SENSITIVE_KEYWORDS = frozenset({
    "token",
    "secret",
    "key",
    "password",
    "credential",
    "auth",
    "session",
})

# Regex pattern to match base64 data URIs (data:mime/type;base64,...)
BASE64_DATA_URI_PATTERN = re.compile(
    r"data:[a-zA-Z0-9+/.-]+;base64,[A-Za-z0-9+/=]{64,}",
    re.IGNORECASE,
)

# Regex pattern to match standalone long base64 strings
# Must be at least MIN_BASE64_LENGTH chars, only base64 chars,
# and end with = padding or end of string
BASE64_STANDALONE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9+/=])([A-Za-z0-9+/]{64,}={0,2})(?![A-Za-z0-9+/=])"
)

# Regex pattern to match URLs with potentially sensitive query parameters
URL_WITH_PARAMS_PATTERN = re.compile(
    r"(https?://[^\s\"'<>]+)\?([^\s\"'<>]+)",
    re.IGNORECASE,
)


def filter_ipynb_outputs(content: str) -> str:
    """Remove execution outputs from Jupyter notebook JSON content.
    
    This filters:
    - Cell outputs (execution results, display data, streams, errors)
    - Execution counts
    - Cell metadata that changes on each run
    
    Args:
        content: The raw JSON content of an ipynb file.
        
    Returns:
        Filtered JSON content with outputs removed.
    """
    try:
        notebook = json.loads(content)
    except json.JSONDecodeError:
        # If it's not valid JSON, return as-is
        return content
    
    if not isinstance(notebook, dict) or "cells" not in notebook:
        # Not a valid notebook structure
        return content
    
    # Process each cell
    for cell in notebook.get("cells", []):
        if not isinstance(cell, dict):
            continue
            
        # Remove outputs from code cells
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None
            
        # Clean cell metadata that changes on execution
        if "metadata" in cell and isinstance(cell["metadata"], dict):
            # Remove execution-related metadata
            cell["metadata"].pop("execution", None)
            cell["metadata"].pop("scrolled", None)
    
    # Clean notebook-level metadata
    if "metadata" in notebook and isinstance(notebook["metadata"], dict):
        # Remove kernel-specific runtime info
        notebook["metadata"].pop("language_info", None)
        
    return json.dumps(notebook, indent=1, ensure_ascii=False)


def filter_base64_strings(content: str, min_length: int = MIN_BASE64_LENGTH) -> str:
    """Replace long base64-encoded strings with a placeholder.
    
    This detects:
    - Data URIs (data:mime/type;base64,...)
    - Standalone base64 strings that are suspiciously long
    
    Args:
        content: The file content.
        min_length: Minimum length for a base64 string to be filtered.
        
    Returns:
        Content with long base64 strings replaced by placeholders.
    """
    # First, handle data URIs
    content = BASE64_DATA_URI_PATTERN.sub("[BASE64_DATA_FILTERED]", content)
    
    # Handle standalone base64 strings
    def replace_base64(match: re.Match[str]) -> str:
        b64_str = match.group(1)
        if len(b64_str) >= min_length:
            # Additional check: must look like actual base64
            # Real base64 data tends to have mix of upper/lower and numbers
            has_upper = any(c.isupper() for c in b64_str[:100])
            has_lower = any(c.islower() for c in b64_str[:100])
            has_digit = any(c.isdigit() for c in b64_str[:100])
            
            # If it has good mix, it's likely base64
            if sum([has_upper, has_lower, has_digit]) >= 2:
                return "[BASE64_DATA_FILTERED]"
        return match.group(0)
    
    content = BASE64_STANDALONE_PATTERN.sub(replace_base64, content)
    
    return content


def _is_sensitive_param(key_lower: str) -> bool:
    """Check if a parameter key is sensitive.
    
    Args:
        key_lower: Lowercase parameter key with hyphens converted to underscores.
        
    Returns:
        True if the parameter is considered sensitive.
    """
    # First check exact match (O(1) for frozenset)
    if key_lower in SENSITIVE_PARAMS:
        return True
    
    # Then check if any core keyword is contained in the key
    # This is more efficient than checking all SENSITIVE_PARAMS
    return any(keyword in key_lower for keyword in SENSITIVE_KEYWORDS)


def filter_sensitive_urls(content: str) -> str:
    """Sanitize URLs that contain potentially sensitive query parameters.
    
    This detects URLs with common sensitive parameter names like:
    - token, api_key, secret, password, session, etc.
    
    The sensitive parameter values are replaced with [FILTERED].
    
    Args:
        content: The file content.
        
    Returns:
        Content with sensitive URL parameters sanitized.
    """
    def sanitize_url(match: re.Match[str]) -> str:
        base_url = match.group(1)
        query_string = match.group(2)
        
        # Parse query parameters
        params = query_string.split("&")
        filtered_params = []
        
        for param in params:
            if "=" in param:
                key, value = param.split("=", 1)
                key_lower = key.lower().replace("-", "_")
                
                # Check if this is a sensitive parameter
                if _is_sensitive_param(key_lower):
                    filtered_params.append(f"{key}=[FILTERED]")
                else:
                    filtered_params.append(param)
            else:
                filtered_params.append(param)
        
        return f"{base_url}?{'&'.join(filtered_params)}"
    
    return URL_WITH_PARAMS_PATTERN.sub(sanitize_url, content)


def apply_content_filters(
    content: str,
    file_path: Path,
    *,
    filter_ipynb: bool = True,
    filter_base64: bool = True,
    filter_urls: bool = True,
) -> str:
    """Apply all content filters to file content.
    
    Args:
        content: The file content.
        file_path: Path to the file (used to determine file type).
        filter_ipynb: Whether to filter ipynb outputs.
        filter_base64: Whether to filter base64 strings.
        filter_urls: Whether to filter sensitive URLs.
        
    Returns:
        Filtered content.
    """
    # Apply ipynb filter for notebook files
    if filter_ipynb and file_path.suffix.lower() == ".ipynb":
        content = filter_ipynb_outputs(content)
    
    # Apply base64 filter
    if filter_base64:
        content = filter_base64_strings(content)
    
    # Apply URL filter
    if filter_urls:
        content = filter_sensitive_urls(content)
    
    return content
