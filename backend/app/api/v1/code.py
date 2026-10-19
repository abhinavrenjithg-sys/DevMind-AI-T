from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.models import SourceFile, Symbol, RepositoryRevision, Repository
from app.schemas import SourceFileResponse, SymbolResponse, FileContentResponse, FileTreeNode

router = APIRouter()

@router.get("/files/{revision_id}", response_model=List[SourceFileResponse])
async def list_files(
    revision_id: str,
    layer: Optional[str] = None,
    language: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SourceFile).where(SourceFile.revision_id == revision_id)
    if layer and layer != "all":
        stmt = stmt.where(SourceFile.layer == layer)
    if language and language != "all":
        stmt = stmt.where(SourceFile.language == language)
    
    stmt = stmt.order_by(SourceFile.path.asc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/tree/{revision_id}", response_model=List[FileTreeNode])
async def get_file_tree(revision_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(SourceFile).where(SourceFile.revision_id == revision_id).order_by(SourceFile.path.asc())
    )
    files = res.scalars().all()

    # Build directory tree
    root_nodes: Dict[str, Any] = {}

    for f in files:
        parts = Path(f.path).parts
        curr = root_nodes
        accum_path = ""
        for i, part in enumerate(parts):
            accum_path = f"{accum_path}/{part}" if accum_path else part
            is_file = (i == len(parts) - 1)
            if part not in curr:
                curr[part] = {
                    "name": part,
                    "path": accum_path,
                    "type": "file" if is_file else "directory",
                    "language": f.language if is_file else None,
                    "size": f.size_bytes if is_file else None,
                    "lines": f.lines_of_code if is_file else None,
                    "symbols_count": f.symbols_count if is_file else None,
                    "children": {} if not is_file else None
                }
            if not is_file:
                curr = curr[part]["children"]

    def convert_to_list(d: Dict[str, Any]) -> List[FileTreeNode]:
        out = []
        for k, v in sorted(d.items(), key=lambda x: (x[1]["type"] == "file", x[0])):
            children_list = convert_to_list(v["children"]) if v.get("children") is not None else None
            out.append(FileTreeNode(
                name=v["name"],
                path=v["path"],
                type=v["type"],
                language=v["language"],
                size=v["size"],
                lines=v["lines"],
                symbols_count=v["symbols_count"],
                children=children_list
            ))
        return out

    return convert_to_list(root_nodes)

@router.get("/file-content/{revision_id}", response_model=FileContentResponse)
async def get_file_content(
    revision_id: str,
    path: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    # Lookup revision & repository local path
    rev_res = await db.execute(
        select(RepositoryRevision, Repository)
        .join(Repository, Repository.id == RepositoryRevision.repository_id)
        .where(RepositoryRevision.id == revision_id)
    )
    row = rev_res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Revision not found")
    rev, repo = row

    file_res = await db.execute(
        select(SourceFile).where(SourceFile.revision_id == revision_id, SourceFile.path == path)
    )
    sf = file_res.scalar_one_or_none()
    if not sf:
        raise HTTPException(status_code=404, detail="File not found in this revision")

    abs_p = (Path(repo.local_path) / path).resolve()
    if not abs_p.exists() or not str(abs_p).startswith(str(Path(repo.local_path).resolve())):
        raise HTTPException(status_code=404, detail="File content not accessible on disk")

    try:
        with open(abs_p, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")

    # Fetch symbols in this file
    syms_res = await db.execute(
        select(Symbol).where(Symbol.file_id == sf.id).order_by(Symbol.start_line.asc())
    )
    symbols = syms_res.scalars().all()
    sym_responses = []
    for s in symbols:
        sr = SymbolResponse.model_validate(s)
        sr.file_path = sf.path
        sym_responses.append(sr)

    return FileContentResponse(
        file_path=path,
        language=sf.language,
        lines_of_code=sf.lines_of_code,
        content=content,
        symbols=sym_responses
    )

@router.get("/symbols/{revision_id}", response_model=List[SymbolResponse])
async def list_symbols(
    revision_id: str,
    kind: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Symbol, SourceFile.path)
        .join(SourceFile, SourceFile.id == Symbol.file_id)
        .where(Symbol.revision_id == revision_id)
    )
    if kind and kind != "all":
        stmt = stmt.where(Symbol.kind == kind)
    if query:
        stmt = stmt.where(Symbol.name.ilike(f"%{query}%"))

    stmt = stmt.order_by(Symbol.name.asc()).limit(limit)
    res = await db.execute(stmt)
    rows = res.all()

    out = []
    for s, file_path in rows:
        sr = SymbolResponse.model_validate(s)
        sr.file_path = file_path
        out.append(sr)
    return out
