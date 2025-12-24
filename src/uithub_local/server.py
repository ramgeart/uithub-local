from __future__ import annotations

import yaml
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .api import dump_repo
from .walker import DEFAULT_MAX_SIZE

app = FastAPI(
    title="uithub-local API",
    description="REST API for uithub-local to flatten repositories into text dumps.",
    version="0.1.7",
)

class DumpRequest(BaseModel):
    path: Optional[str] = Field(None, description="Local path or remote URL to process")
    remote_url: Optional[str] = Field(None, description="Git repo URL to download")
    local_path: Optional[str] = Field(None, description="Local directory path to process")
    private_token: Optional[str] = Field(None, description="Token for private repos")
    include: List[str] = Field(["*"], description="Glob(s) to include")
    exclude: List[str] = Field([], description="Glob(s) to exclude")
    max_size: int = Field(DEFAULT_MAX_SIZE, description="Skip files larger than this many bytes")
    max_tokens: Optional[int] = Field(None, description="Hard cap; truncate largest files first")
    format: str = Field("text", description="Output format (text, json, html)")
    binary_strict: bool = Field(True, description="Use strict binary detection")
    exclude_comments: bool = Field(False, description="Strip code comments from output")
    not_ignore: bool = Field(False, description="Do not respect .gitignore rules")

@app.post("/dump", summary="Generate a repository dump")
async def generate_dump(request: DumpRequest):
    """
    Generate a repository dump based on the provided options.
    """
    path_sources = sum([
        request.path is not None,
        request.local_path is not None,
        request.remote_url is not None
    ])
    
    if path_sources > 1:
        raise HTTPException(status_code=400, detail="Only one of path, local_path, or remote_url can be used")
    if path_sources == 0:
        raise HTTPException(status_code=400, detail="One of path, local_path, or remote_url is required")

    target = request.path or request.local_path or request.remote_url
    
    try:
        content = dump_repo(
            target,
            fmt=request.format,
            include=request.include,
            exclude=request.exclude,
            max_size=request.max_size,
            max_tokens=request.max_tokens,
            binary_strict=request.binary_strict,
            exclude_comments=request.exclude_comments,
            respect_gitignore=not request.not_ignore,
            private_token=request.private_token,
        )
        
        media_type = "text/plain"
        if request.format == "json":
            media_type = "application/json"
        elif request.format == "html":
            media_type = "text/html"
            
        return Response(content=content, media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    """
    Returns the OpenAPI specification in YAML format.
    """
    openapi_schema = app.openapi()
    yaml_schema = yaml.dump(openapi_schema, sort_keys=False)
    return Response(content=yaml_schema, media_type="text/yaml")

def save_openapi_spec(output_path: Path):
    """
    Utility to save the OpenAPI spec to a file.
    """
    openapi_schema = app.openapi()
    with open(output_path, "w") as f:
        yaml.dump(openapi_schema, f, sort_keys=False)
