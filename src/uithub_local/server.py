from __future__ import annotations

import yaml
from pathlib import Path
from typing import List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import Response, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from .api import dump_repo, dump_repo_split
from .walker import DEFAULT_MAX_SIZE

app = FastAPI(
    title="uithub-local API",
    description="REST API for uithub-local to flatten repositories into text dumps.",
    version="0.1.8",
)

security = HTTPBearer(auto_error=False)

class DumpRequest(BaseModel):
    remote_url: str = Field(..., description="Git repo URL to download")
    private_token: Optional[str] = Field(None, description="Token for private repos")
    include: List[str] = Field(["*"], description="Glob(s) to include")
    exclude: List[str] = Field([], description="Glob(s) to exclude")
    max_size: int = Field(DEFAULT_MAX_SIZE, description="Skip files larger than this many bytes")
    max_tokens: Optional[int] = Field(None, description="Hard cap; truncate largest files first")
    split: Optional[int] = Field(None, description="Split output into multiple parts, each with N tokens")
    format: str = Field("text", description="Output format (text, json, html)")
    binary_strict: bool = Field(True, description="Use strict binary detection")
    exclude_comments: bool = Field(False, description="Strip code comments from output")
    not_ignore: bool = Field(False, description="Do not respect .gitignore rules")

async def _handle_dump(
    remote_url: str,
    private_token: Optional[str] = None,
    include: List[str] = ["*"],
    exclude: List[str] = [],
    max_size: int = DEFAULT_MAX_SIZE,
    max_tokens: Optional[int] = None,
    split: Optional[int] = None,
    fmt: str = "text",
    binary_strict: bool = True,
    exclude_comments: bool = False,
    not_ignore: bool = False,
    auth: Optional[HTTPAuthorizationCredentials] = None,
):
    # Use Bearer token if provided, otherwise fallback to private_token
    token = (auth.credentials if auth else None) or private_token
    
    try:
        if split:
            parts = dump_repo_split(
                remote_url,
                split,
                fmt=fmt,
                include=include,
                exclude=exclude,
                max_size=max_size,
                max_tokens=max_tokens,
                binary_strict=binary_strict,
                exclude_comments=exclude_comments,
                respect_gitignore=not not_ignore,
                private_token=token,
            )
            return JSONResponse(content={
                "status": "success",
                "parts": [{"filename": f, "content": c} for f, c in parts]
            })

        content = dump_repo(
            remote_url,
            fmt=fmt,
            include=include,
            exclude=exclude,
            max_size=max_size,
            max_tokens=max_tokens,
            binary_strict=binary_strict,
            exclude_comments=exclude_comments,
            respect_gitignore=not not_ignore,
            private_token=token,
        )
        
        if fmt == "json":
            return JSONResponse(content={"status": "success", "content": content})
            
        media_type = "text/plain"
        if fmt == "html":
            media_type = "text/html"
            
        return Response(content=content, media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dump", summary="Generate a repository dump (POST)")
async def generate_dump_post(
    request: DumpRequest,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    return await _handle_dump(
        remote_url=request.remote_url,
        private_token=request.private_token,
        include=request.include,
        exclude=request.exclude,
        max_size=request.max_size,
        max_tokens=request.max_tokens,
        split=request.split,
        fmt=request.format,
        binary_strict=request.binary_strict,
        exclude_comments=request.exclude_comments,
        not_ignore=request.not_ignore,
        auth=auth,
    )

@app.get("/dump", summary="Generate a repository dump (GET)")
async def generate_dump_get(
    remote_url: str = Query(..., description="Git repo URL to download"),
    private_token: Optional[str] = Query(None, description="Token for private repos"),
    include: List[str] = Query(["*"], description="Glob(s) to include"),
    exclude: List[str] = Query([], description="Glob(s) to exclude"),
    max_size: int = Query(DEFAULT_MAX_SIZE, description="Skip files larger than this many bytes"),
    max_tokens: Optional[int] = Query(None, description="Hard cap; truncate largest files first"),
    split: Optional[int] = Query(None, description="Split output into multiple parts"),
    format: str = Query("text", description="Output format (text, json, html)"),
    binary_strict: bool = Query(True, description="Use strict binary detection"),
    exclude_comments: bool = Query(False, description="Strip code comments from output"),
    not_ignore: bool = Query(False, description="Do not respect .gitignore rules"),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    return await _handle_dump(
        remote_url=remote_url,
        private_token=private_token,
        include=include,
        exclude=exclude,
        max_size=max_size,
        max_tokens=max_tokens,
        split=split,
        fmt=format,
        binary_strict=binary_strict,
        exclude_comments=exclude_comments,
        not_ignore=not_ignore,
        auth=auth,
    )

@app.get("/dump/{user}/{repo}", summary="Generate a repository dump for a GitHub user/repo (GET)")
async def generate_dump_github_get(
    user: str,
    repo: str,
    private_token: Optional[str] = Query(None, description="Token for private repos"),
    include: List[str] = Query(["*"], description="Glob(s) to include"),
    exclude: List[str] = Query([], description="Glob(s) to exclude"),
    max_size: int = Query(DEFAULT_MAX_SIZE, description="Skip files larger than this many bytes"),
    max_tokens: Optional[int] = Query(None, description="Hard cap; truncate largest files first"),
    split: Optional[int] = Query(None, description="Split output into multiple parts"),
    format: str = Query("text", description="Output format (text, json, html)"),
    binary_strict: bool = Query(True, description="Use strict binary detection"),
    exclude_comments: bool = Query(False, description="Strip code comments from output"),
    not_ignore: bool = Query(False, description="Do not respect .gitignore rules"),
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    remote_url = f"https://github.com/{user}/{repo}"
    return await _handle_dump(
        remote_url=remote_url,
        private_token=private_token,
        include=include,
        exclude=exclude,
        max_size=max_size,
        max_tokens=max_tokens,
        split=split,
        fmt=format,
        binary_strict=binary_strict,
        exclude_comments=exclude_comments,
        not_ignore=not_ignore,
        auth=auth,
    )

@app.post("/dump/{user}/{repo}", summary="Generate a repository dump for a GitHub user/repo (POST)")
async def generate_dump_github_post(
    user: str,
    repo: str,
    request: Optional[DumpRequest] = None,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    remote_url = f"https://github.com/{user}/{repo}"
    if request:
        return await _handle_dump(
            remote_url=remote_url,
            private_token=request.private_token,
            include=request.include,
            exclude=request.exclude,
            max_size=request.max_size,
            max_tokens=request.max_tokens,
            split=request.split,
            fmt=request.format,
            binary_strict=request.binary_strict,
            exclude_comments=request.exclude_comments,
            not_ignore=request.not_ignore,
            auth=auth,
        )
    return await _handle_dump(
        remote_url=remote_url,
        auth=auth,
    )

@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    openapi_schema = app.openapi()
    yaml_schema = yaml.dump(openapi_schema, sort_keys=False)
    return Response(content=yaml_schema, media_type="text/yaml")

def save_openapi_spec(output_path: Path):
    openapi_schema = app.openapi()
    with open(output_path, "w") as f:
        yaml.dump(openapi_schema, f, sort_keys=False)
