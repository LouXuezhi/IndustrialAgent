from pathlib import Path
import uuid
import zipfile
import io
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Body, Query, status
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import StandardResponse
from app.core.security import get_current_user
from app.db.models import DocumentLibrary, User, Group, GroupMember, Document, Chunk
from app.db.session import async_session
from app.deps import get_db_session
from app.core.config import get_settings
from app.rag.ingestion import DocumentIngestor, _extract_text_from_file


class LibraryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    owner_id: uuid.UUID | None = None
    owner_type: str = Field(default="user", pattern="^(user|group)$")


class LibraryResponse(BaseModel):
    id: str
    name: str
    owner_id: str
    owner_type: str
    description: str | None = None
    vector_collection_name: str | None = None


class LibraryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None


class IngestResponse(BaseModel):
    document_id: str
    chunks: int
    library_id: str | None = None
    vectorized: bool | None = None


class DocumentResponse(BaseModel):
    id: str
    title: str
    source_path: str
    library_id: str | None = None
    meta: dict = Field(default_factory=dict)
    vectorized: bool = False
    created_at: str


class LibraryStatsResponse(BaseModel):
    library_id: str
    document_count: int
    total_chunks: int
    total_size_bytes: int | None = None


class BatchDeleteRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1, max_length=100)


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    library_id: uuid.UUID | None = None
    limit: int = Field(default=20, ge=1, le=100)


class DocumentSearchResult(BaseModel):
    document_id: str
    title: str
    snippet: str
    score: float | None = None
    library_id: str | None = None


class DocumentPreviewResponse(BaseModel):
    document_id: str
    title: str
    content: str
    content_length: int
    file_type: str | None = None
    vectorized: bool | None = None


class VectorizeRequest(BaseModel):
    chunk_size: int = Field(default=800, ge=100, le=4000)


class VectorizeResponse(BaseModel):
    document_id: str
    chunks: int
    vectorized: bool


class BatchDownloadRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1, max_length=50)


router = APIRouter(prefix="/docs", tags=["docs"])


def _assert_owner_exists(session: AsyncSession, owner_id: uuid.UUID, owner_type: str):
    if owner_type == "user":
        return session.execute(select(User).where(User.id == owner_id))
    if owner_type == "group":
        return session.execute(select(Group).where(Group.id == owner_id))
    return None


async def _get_library_or_404(session: AsyncSession, library_id: uuid.UUID) -> DocumentLibrary:
    result = await session.execute(select(DocumentLibrary).where(DocumentLibrary.id == library_id))
    library = result.scalar_one_or_none()
    if not library:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Library not found")
    return library


def _collection_name(library_id: uuid.UUID | None) -> str:
    return f"library_{library_id}" if library_id else "library_default"


async def _get_or_create_personal_library(session: AsyncSession, user: User) -> DocumentLibrary:
    """Ensure the user has a personal default library; create if missing."""
    # First try to find the default library
    result = await session.execute(
        select(DocumentLibrary).where(
            DocumentLibrary.owner_id == user.id,
            DocumentLibrary.owner_type == "user",
            DocumentLibrary.is_default == True,
        )
    )
    library = result.scalar_one_or_none()
    if library:
        return library
    
    # If no default library exists, try to find any personal library
    result = await session.execute(
        select(DocumentLibrary).where(
            DocumentLibrary.owner_id == user.id,
            DocumentLibrary.owner_type == "user",
        )
    )
    library = result.scalar_one_or_none()
    if library:
        # Mark it as default if it's the only one
        library.is_default = True
        await session.commit()
        await session.refresh(library)
        return library

    library = DocumentLibrary(
        name=f"{user.full_name or user.username or user.email.split('@')[0]}的个人库",
        description="个人默认文档库",
        owner_id=user.id,
        owner_type="user",
        is_default=True,  # 标记为默认库，不允许删除
        # vector_collection_name will be set after library.id is generated
    )
    session.add(library)
    await session.flush()  # Flush to get library.id
    library.vector_collection_name = _collection_name(library.id)  # Use library.id, not user.id
    await session.commit()
    await session.refresh(library)
    return library


async def _assert_group_member(
    session: AsyncSession,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    allowed_roles: tuple[str, ...] = ("owner", "admin", "member"),
) -> GroupMember:
    result = await session.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
            GroupMember.role.in_(allowed_roles),
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return member


@router.post("/libraries", response_model=StandardResponse[LibraryResponse])
async def create_library(
    payload: LibraryCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[LibraryResponse]:
    owner_id = payload.owner_id or current_user.id
    owner_type = payload.owner_type or "user"

    if owner_type == "user":
        if owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    elif owner_type == "group":
        # Only group owner/admin can create library under group
        await _assert_group_member(session, group_id=owner_id, user_id=current_user.id, allowed_roles=("owner", "admin"))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid owner_type")

    library = DocumentLibrary(
        name=payload.name,
        description=payload.description,
        owner_id=owner_id,
        owner_type=owner_type,
        # vector_collection_name will be set after library.id is generated
    )
    session.add(library)
    await session.flush()  # Flush to get library.id
    library.vector_collection_name = _collection_name(library.id)  # Use library.id, not owner_id
    await session.commit()
    await session.refresh(library)

    data = LibraryResponse(
        id=str(library.id),
        name=library.name,
        owner_id=str(library.owner_id),
        owner_type=library.owner_type,
        description=library.description,
        vector_collection_name=library.vector_collection_name,
    )
    return StandardResponse(data=data)


@router.get("/libraries", response_model=StandardResponse[list[LibraryResponse]])
async def list_libraries(
    owner_id: uuid.UUID | None = Query(default=None),
    owner_type: str = Query(default="user", pattern="^(user|group)$"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[LibraryResponse]]:
    resolved_owner_id = owner_id or current_user.id
    if owner_type == "user":
        if resolved_owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    elif owner_type == "group":
        await _assert_group_member(
            session, group_id=resolved_owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid owner_type")

    query = select(DocumentLibrary).where(
        DocumentLibrary.owner_id == resolved_owner_id, DocumentLibrary.owner_type == owner_type
    )
    result = await session.execute(query)
    libraries = result.scalars().all()
    data = [
        LibraryResponse(
            id=str(lib.id),
            name=lib.name,
            owner_id=str(lib.owner_id),
            owner_type=lib.owner_type,
            description=lib.description,
            vector_collection_name=lib.vector_collection_name,
        )
        for lib in libraries
    ]
    return StandardResponse(data=data)


@router.post("/ingest", response_model=StandardResponse[IngestResponse])
async def ingest_document(
    file: UploadFile = File(...),
    library_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
) -> StandardResponse[IngestResponse]:
    settings = get_settings()
    storage_dir = Path(settings.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    # prefix with uuid to avoid filename collisions
    target_path = storage_dir / f"{uuid.uuid4()}_{file.filename}"
    target_path.write_bytes(await file.read())

    async with async_session() as session:
        resolved_library_id = library_id
        if resolved_library_id:
            library = await _get_library_or_404(session, resolved_library_id)
            if library.owner_type == "user":
                if library.owner_id != current_user.id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
            elif library.owner_type == "group":
                await _assert_group_member(
                    session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
                )
        else:
            library = await _get_or_create_personal_library(session, current_user)
            resolved_library_id = library.id

        # persist document metadata only; vectorization is opt-in via separate endpoint
        file_size = target_path.stat().st_size if target_path.exists() else 0
        file_type = target_path.suffix.lower()
        document = Document(
            title=file.filename,
            source_path=str(target_path),
            library_id=resolved_library_id,
            meta={
                "file_type": file_type,
                "file_size": file_size,
                "vectorized": False,
            },
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)

    return StandardResponse(
        data=IngestResponse(
            document_id=str(document.id),
            chunks=0,
                library_id=str(resolved_library_id) if resolved_library_id else None,
            vectorized=False,
        )
    )


@router.post("/reindex")
async def reindex_corpus() -> StandardResponse[dict[str, str]]:
    # Hook for kicking off an offline rebuild job (Celery, Prefect, etc.)
    return StandardResponse(data={"status": "queued"})


@router.post("/documents/{document_id}/vectorize", response_model=StandardResponse[VectorizeResponse])
async def vectorize_document(
    document_id: uuid.UUID,
    payload: VectorizeRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[VectorizeResponse]:
    """Trigger vectorization for a single document."""
    document = await session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # permission check
    if document.library_id:
        library = await _get_library_or_404(session, document.library_id)
        if library.owner_type == "user":
            if library.owner_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        elif library.owner_type == "group":
            await _assert_group_member(
                session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
            )

    ingestor = DocumentIngestor(settings=get_settings())
    report = await ingestor.vectorize_document(document=document, session=session, chunk_size=payload.chunk_size)
    await session.refresh(document)

    vectorized = bool((document.meta or {}).get("vectorized", False))
    code = 0 if vectorized else 1
    message = "success" if vectorized else f"vectorization failed: {report.error or 'unknown error'}"

    data = VectorizeResponse(
        document_id=str(document_id),
        chunks=report.chunk_count,
        vectorized=vectorized,
    )
    return StandardResponse(data=data, code=code, message=message)


@router.get("/libraries/{library_id}", response_model=StandardResponse[LibraryResponse])
async def get_library(
    library_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[LibraryResponse]:
    library = await _get_library_or_404(session, library_id)
    if library.owner_type == "user":
        if library.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    elif library.owner_type == "group":
        await _assert_group_member(
            session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
        )
    data = LibraryResponse(
        id=str(library.id),
        name=library.name,
        owner_id=str(library.owner_id),
        owner_type=library.owner_type,
        description=library.description,
        vector_collection_name=library.vector_collection_name,
    )
    return StandardResponse(data=data)


@router.put("/libraries/{library_id}", response_model=StandardResponse[LibraryResponse])
async def update_library(
    library_id: uuid.UUID,
    payload: LibraryUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[LibraryResponse]:
    library = await _get_library_or_404(session, library_id)
    if library.owner_type == "user":
        if library.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    elif library.owner_type == "group":
        await _assert_group_member(
            session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin")
        )

    if payload.name is not None:
        library.name = payload.name
    if payload.description is not None:
        library.description = payload.description

    await session.commit()
    await session.refresh(library)

    data = LibraryResponse(
        id=str(library.id),
        name=library.name,
        owner_id=str(library.owner_id),
        owner_type=library.owner_type,
        description=library.description,
        vector_collection_name=library.vector_collection_name,
    )
    return StandardResponse(data=data)


@router.delete("/libraries/{library_id}", response_model=StandardResponse[dict])
async def delete_library(
    library_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    library = await _get_library_or_404(session, library_id)
    
    # 检查是否为默认库，默认库不允许删除
    if library.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default personal library"
        )
    
    if library.owner_type == "user":
        if library.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    elif library.owner_type == "group":
        await _assert_group_member(
            session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin")
        )

    collection_name = library.vector_collection_name or _collection_name(library.id)
    await session.delete(library)
    await session.commit()

    # best-effort delete vector collection
    try:
        settings = get_settings()
        ingestor = DocumentIngestor(settings=settings)
        ingestor._client.delete_collection(name=collection_name)
    except Exception:
        pass

    return StandardResponse(data={"deleted": True})


@router.get("/libraries/{library_id}/documents", response_model=StandardResponse[list[DocumentResponse]])
async def list_documents(
    library_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[DocumentResponse]]:
    """List documents in a library with pagination."""
    library = await _get_library_or_404(session, library_id)
    
    # Check permissions
    if library.owner_type == "user":
        if library.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    elif library.owner_type == "group":
        await _assert_group_member(
            session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
        )
    
    # Query documents
    query = (
        select(Document)
        .where(Document.library_id == library_id)
        .order_by(Document.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(query)
    documents = result.scalars().all()
    
    data = [
        DocumentResponse(
            id=str(doc.id),
            title=doc.title,
            source_path=doc.source_path,
            library_id=str(doc.library_id) if doc.library_id else None,
            meta=doc.meta or {},
            vectorized=bool((doc.meta or {}).get("vectorized", False)),
            created_at=doc.created_at.isoformat() if doc.created_at else "",
        )
        for doc in documents
    ]
    return StandardResponse(data=data)


@router.get("/documents", response_model=StandardResponse[list[DocumentResponse]])
async def list_all_documents(
    library_id: uuid.UUID | None = Query(default=None, description="Optional: filter by library ID"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[DocumentResponse]]:
    """List all documents accessible by the current user."""
    # Get user's accessible libraries
    user_libraries_query = select(DocumentLibrary).where(
        and_(
            DocumentLibrary.owner_type == "user",
            DocumentLibrary.owner_id == current_user.id
        )
    )
    user_libs_result = await session.execute(user_libraries_query)
    user_library_ids = [lib.id for lib in user_libs_result.scalars().all()]
    
    # Get group libraries where user is a member
    group_members_query = select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)
    group_members_result = await session.execute(group_members_query)
    group_ids = [gm for gm in group_members_result.scalars().all()]
    
    group_libraries_query = select(DocumentLibrary).where(
        and_(
            DocumentLibrary.owner_type == "group",
            DocumentLibrary.owner_id.in_(group_ids)
        )
    )
    group_libs_result = await session.execute(group_libraries_query)
    group_library_ids = [lib.id for lib in group_libs_result.scalars().all()]
    
    # Combine all accessible library IDs
    accessible_library_ids = user_library_ids + group_library_ids
    
    # Build query
    query = select(Document).order_by(Document.created_at.desc())
    
    if library_id:
        # Filter by specific library if provided
        if library_id not in accessible_library_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        query = query.where(Document.library_id == library_id)
    else:
        # Filter by all accessible libraries
        if accessible_library_ids:
            query = query.where(Document.library_id.in_(accessible_library_ids))
        else:
            # No accessible libraries, return empty list
            return StandardResponse(data=[])
    
    query = query.limit(limit).offset(offset)
    result = await session.execute(query)
    documents = result.scalars().all()
    
    data = [
        DocumentResponse(
            id=str(doc.id),
            title=doc.title,
            source_path=doc.source_path,
            library_id=str(doc.library_id) if doc.library_id else None,
            meta=doc.meta or {},
            vectorized=bool((doc.meta or {}).get("vectorized", False)),
            created_at=doc.created_at.isoformat() if doc.created_at else "",
        )
        for doc in documents
    ]
    return StandardResponse(data=data)


@router.post("/documents/batch-delete", response_model=StandardResponse[dict])
async def batch_delete_documents(
    payload: BatchDeleteRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    """Batch delete multiple documents."""
    document_ids = [uuid.UUID(doc_id) for doc_id in payload.document_ids]
    
    # Fetch all documents and check permissions
    result = await session.execute(select(Document).where(Document.id.in_(document_ids)))
    documents = result.scalars().all()
    
    if len(documents) != len(document_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Some documents not found")
    
    # Check permissions for each document
    for document in documents:
        if document.library_id:
            library = await _get_library_or_404(session, document.library_id)
            if library.owner_type == "user":
                if library.owner_id != current_user.id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Forbidden: document {document.id}")
            elif library.owner_type == "group":
                await _assert_group_member(
                    session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin")
                )
    
    # Delete chunks
    chunk_result = await session.execute(select(Chunk).where(Chunk.document_id.in_(document_ids)))
    chunks = chunk_result.scalars().all()
    for chunk in chunks:
        await session.delete(chunk)
    
    # Delete documents
    for document in documents:
        await session.delete(document)
    
    await session.commit()
    
    return StandardResponse(data={"deleted": len(documents), "document_ids": payload.document_ids})


@router.post("/documents/batch-download")
async def batch_download_documents(
    payload: BatchDownloadRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Download multiple documents as a zip file."""
    document_ids = [uuid.UUID(doc_id) for doc_id in payload.document_ids]
    
    # Fetch all documents and check permissions
    result = await session.execute(select(Document).where(Document.id.in_(document_ids)))
    documents = result.scalars().all()
    
    if len(documents) != len(document_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Some documents not found")
    
    # Check permissions for each document
    accessible_docs = []
    for document in documents:
        has_access = False
        if document.library_id:
            library = await _get_library_or_404(session, document.library_id)
            if library.owner_type == "user":
                has_access = library.owner_id == current_user.id
            elif library.owner_type == "group":
                try:
                    await _assert_group_member(
                        session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
                    )
                    has_access = True
                except HTTPException:
                    has_access = False
        else:
            has_access = True
        
        if has_access:
            accessible_docs.append(document)
    
    if not accessible_docs:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No accessible documents")
    
    # Create zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for document in accessible_docs:
            path = Path(document.source_path)
            if path.exists():
                try:
                    zip_file.write(path, arcname=document.title)
                except Exception:
                    # Skip files that can't be read
                    continue
    
    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=documents.zip"},
    )


@router.get("/documents/{document_id}", response_model=StandardResponse[DocumentResponse])
async def get_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[DocumentResponse]:
    """Get document details."""
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Check library permissions
    if document.library_id:
        library = await _get_library_or_404(session, document.library_id)
        if library.owner_type == "user":
            if library.owner_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        elif library.owner_type == "group":
            await _assert_group_member(
                session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
            )
    
    data = DocumentResponse(
        id=str(document.id),
        title=document.title,
        source_path=document.source_path,
        library_id=str(document.library_id) if document.library_id else None,
        meta=document.meta or {},
        vectorized=bool((document.meta or {}).get("vectorized", False)),
        created_at=document.created_at.isoformat() if document.created_at else "",
    )
    return StandardResponse(data=data)


@router.delete("/documents/{document_id}", response_model=StandardResponse[dict])
async def delete_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    """Delete a document and its chunks."""
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Check library permissions (need write access)
    if document.library_id:
        library = await _get_library_or_404(session, document.library_id)
        if library.owner_type == "user":
            if library.owner_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        elif library.owner_type == "group":
            await _assert_group_member(
                session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin")
            )
    
    # Delete chunks first (cascade should handle this, but explicit is better)
    chunk_result = await session.execute(select(Chunk).where(Chunk.document_id == document_id))
    chunks = chunk_result.scalars().all()
    for chunk in chunks:
        await session.delete(chunk)
    
    # Delete document
    await session.delete(document)
    await session.commit()
    
    # TODO: Remove from vector store (best-effort)
    
    return StandardResponse(data={"deleted": True, "document_id": str(document_id)})


@router.get("/libraries/{library_id}/stats", response_model=StandardResponse[LibraryStatsResponse])
async def get_library_stats(
    library_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[LibraryStatsResponse]:
    """Get library statistics (document count, chunk count, etc.)."""
    library = await _get_library_or_404(session, library_id)
    
    # Check permissions
    if library.owner_type == "user":
        if library.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    elif library.owner_type == "group":
        await _assert_group_member(
            session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
        )
    
    # Count documents
    doc_count_result = await session.execute(
        select(func.count(Document.id)).where(Document.library_id == library_id)
    )
    document_count = doc_count_result.scalar() or 0
    
    # Count chunks
    chunk_count_result = await session.execute(
        select(func.count(Chunk.id))
        .join(Document)
        .where(Document.library_id == library_id)
    )
    total_chunks = chunk_count_result.scalar() or 0
    
    data = LibraryStatsResponse(
        library_id=str(library_id),
        document_count=document_count,
        total_chunks=total_chunks,
        total_size_bytes=None,  # TODO: Calculate from source_path if files are stored
    )
    return StandardResponse(data=data)


@router.post("/documents/search", response_model=StandardResponse[list[DocumentSearchResult]])
async def search_documents(
    payload: DocumentSearchRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[DocumentSearchResult]]:
    """Search documents by title and content."""
    query_lower = payload.query.lower()
    
    # Build base query
    base_query = select(Document)
    if payload.library_id:
        base_query = base_query.where(Document.library_id == payload.library_id)
    
    # Get all matching documents
    result = await session.execute(base_query)
    all_docs = result.scalars().all()
    
    # Filter by permissions and search query
    matching_docs: list[tuple[Document, float]] = []
    for doc in all_docs:
        # Check permissions
        has_access = False
        if doc.library_id:
            library = await _get_library_or_404(session, doc.library_id)
            if library.owner_type == "user":
                has_access = library.owner_id == current_user.id
            elif library.owner_type == "group":
                try:
                    await _assert_group_member(
                        session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
                    )
                    has_access = True
                except HTTPException:
                    has_access = False
        else:
            # Documents without library are accessible to owner
            has_access = True
        
        if not has_access:
            continue
        
        # Search in title
        score = 0.0
        if query_lower in doc.title.lower():
            score += 2.0  # Title match has higher weight
        
        # Search in chunks content
        chunk_result = await session.execute(
            select(Chunk).where(Chunk.document_id == doc.id)
        )
        chunks = chunk_result.scalars().all()
        for chunk in chunks:
            if query_lower in chunk.content.lower():
                score += 1.0
                break
        
        if score > 0:
            matching_docs.append((doc, score))
    
    # Sort by score and limit
    matching_docs.sort(key=lambda x: x[1], reverse=True)
    matching_docs = matching_docs[:payload.limit]
    
    # Build response with snippets
    results: list[DocumentSearchResult] = []
    for doc, score in matching_docs:
        # Get snippet from first chunk
        chunk_result = await session.execute(
            select(Chunk).where(Chunk.document_id == doc.id).limit(1)
        )
        chunk = chunk_result.scalar_one_or_none()
        snippet = ""
        if chunk:
            content = chunk.content
            query_pos = content.lower().find(query_lower)
            if query_pos >= 0:
                start = max(0, query_pos - 50)
                end = min(len(content), query_pos + len(payload.query) + 50)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
            else:
                snippet = content[:200] + "..." if len(content) > 200 else content
        
        results.append(
            DocumentSearchResult(
                document_id=str(doc.id),
                title=doc.title,
                snippet=snippet,
                score=score,
                library_id=str(doc.library_id) if doc.library_id else None,
            )
        )
    
    return StandardResponse(data=results)


@router.get("/documents/{document_id}/preview", response_model=StandardResponse[DocumentPreviewResponse])
async def preview_document(
    document_id: uuid.UUID,
    max_length: int = Query(default=5000, ge=100, le=50000),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[DocumentPreviewResponse]:
    """Preview document content."""
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Check permissions
    if document.library_id:
        library = await _get_library_or_404(session, document.library_id)
        if library.owner_type == "user":
            if library.owner_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        elif library.owner_type == "group":
            await _assert_group_member(
                session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
            )
    
    # Get document content
    path = Path(document.source_path)
    if path.exists():
        try:
            content = _extract_text_from_file(path)
        except Exception:
            content = ""
    else:
        # Fallback: get from chunks
        chunk_result = await session.execute(
            select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.id)
        )
        chunks = chunk_result.scalars().all()
        content = "\n\n".join(chunk.content for chunk in chunks)
    
    # Truncate if needed
    content_length = len(content)
    if len(content) > max_length:
        content = content[:max_length] + "\n\n... (truncated)"
    
    file_type = document.meta.get("file_type", "") if document.meta else None
    vectorized = bool((document.meta or {}).get("vectorized", False))
    
    data = DocumentPreviewResponse(
        document_id=str(document_id),
        title=document.title,
        content=content,
        content_length=content_length,
        file_type=file_type,
        vectorized=vectorized,
    )
    return StandardResponse(data=data)


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Download a single document as a file."""
    result = await session.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Check permissions
    if document.library_id:
        library = await _get_library_or_404(session, document.library_id)
        if library.owner_type == "user":
            if library.owner_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        elif library.owner_type == "group":
            await _assert_group_member(
                session, group_id=library.owner_id, user_id=current_user.id, allowed_roles=("owner", "admin", "member")
            )
    
    path = Path(document.source_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")
    
    def generate():
        with open(path, "rb") as f:
            yield from f
    
    return StreamingResponse(
        generate(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{document.title}"'},
    )

