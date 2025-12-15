from pathlib import Path
import uuid
import zipfile
import io
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Body, Query, status
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import StandardResponse
from app.core.security import get_current_user
from app.db.models import DocumentLibrary, User, Group, GroupMember, Document, Chunk
from app.db.session import async_session
from app.deps import get_db_session, get_retriever
from app.core.config import get_settings
from app.rag.ingestion import DocumentIngestor, _extract_text_from_file
from app.rag.retriever import LangchainRetriever
from app.core.cache import (
    generate_search_cache_key,
    get_cached_search_result,
    cache_search_result,
    record_cache_stats,
    calculate_cache_ttl,
)


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
    owner_type = payload.owner_type or "user"

    if owner_type == "user":
        # For user libraries, use current user's ID
        owner_id = current_user.id
    elif owner_type == "group":
        # For group libraries, owner_id (group_id) must be provided
        if not payload.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="owner_id (group_id) is required when owner_type is 'group'"
            )
        owner_id = payload.owner_id
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

    # 如果向量化成功，清除对应库的 BM25 缓存（如果使用混合检索）
    if vectorized and document.library_id:
        try:
            from app.rag.retriever import HybridRetriever
            from app.deps import get_retriever
            retriever = get_retriever(use_hybrid=True)
            if isinstance(retriever, HybridRetriever):
                retriever.invalidate_bm25_cache(document.library_id)
        except Exception:
            # 忽略缓存清除错误，不影响主流程
            pass
        
        # 清除搜索缓存（文档向量化后，相关查询结果可能已变化）
        try:
            settings = get_settings()
            if settings.enable_search_cache and settings.redis_url:
                import redis.asyncio as redis
                redis_client = redis.from_url(settings.redis_url, decode_responses=False)
                try:
                    from app.core.cache import invalidate_search_cache
                    await invalidate_search_cache(redis_client, library_id=str(document.library_id))
                finally:
                    await redis_client.aclose()
        except Exception as e:
            logger.warning(f"清除搜索缓存失败: {e}")

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
    
    # 清除搜索缓存（库删除后，相关查询结果已失效）
    try:
        if settings.enable_search_cache and settings.redis_url:
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.redis_url, decode_responses=False)
            try:
                from app.core.cache import invalidate_search_cache
                await invalidate_search_cache(redis_client, library_id=str(library_id))
            finally:
                await redis_client.aclose()
    except Exception as e:
        logger.warning(f"清除搜索缓存失败: {e}")

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
    library_ids_affected = set()
    for document in documents:
        if document.library_id:
            library_ids_affected.add(document.library_id)
        await session.delete(document)
    
    await session.commit()
    
    # 清除受影响库的 BM25 缓存
    if library_ids_affected:
        try:
            from app.rag.retriever import HybridRetriever
            from app.deps import get_retriever
            retriever = get_retriever(use_hybrid=True)
            if isinstance(retriever, HybridRetriever):
                for lib_id in library_ids_affected:
                    retriever.invalidate_bm25_cache(lib_id)
        except Exception:
            pass
        
        # 清除搜索缓存（批量删除文档后，相关查询结果已失效）
        try:
            settings = get_settings()
            if settings.enable_search_cache and settings.redis_url:
                import redis.asyncio as redis
                redis_client = redis.from_url(settings.redis_url, decode_responses=False)
                try:
                    from app.core.cache import invalidate_search_cache
                    for lib_id in library_ids_affected:
                        await invalidate_search_cache(redis_client, library_id=str(lib_id))
                finally:
                    await redis_client.aclose()
        except Exception as e:
            logger.warning(f"清除搜索缓存失败: {e}")
    
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
    library_id = document.library_id
    await session.delete(document)
    await session.commit()
    
    # TODO: Remove from vector store (best-effort)
    
    # 清除受影响库的 BM25 缓存
    if library_id:
        try:
            from app.rag.retriever import HybridRetriever
            from app.deps import get_retriever
            retriever = get_retriever(use_hybrid=True)
            if isinstance(retriever, HybridRetriever):
                retriever.invalidate_bm25_cache(library_id)
        except Exception:
            pass
    
    # 清除搜索缓存（文档删除后，相关查询结果可能已失效）
    try:
        settings = get_settings()
        if settings.enable_search_cache and settings.redis_url:
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.redis_url, decode_responses=False)
            try:
                from app.core.cache import invalidate_search_cache
                await invalidate_search_cache(redis_client, library_id=str(library_id) if library_id else None)
            finally:
                await redis_client.aclose()
    except Exception as e:
        logger.warning(f"清除搜索缓存失败: {e}")
    
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
    retriever: LangchainRetriever = Depends(get_retriever),
) -> StandardResponse[list[DocumentSearchResult]]:
    """
    使用混合检索（向量 + BM25）搜索文档，支持缓存。
    
    优化评分系统：
    - 向量相似度分数（主要）
    - 标题匹配权重（增强）
    - 匹配次数（多次匹配更相关）
    
    缓存策略：
    - 缓存键包含查询、库ID、限制和用户ID（权限隔离）
    - 动态 TTL：根据结果数量和查询长度调整
    - 缓存命中时直接返回，未命中时执行检索并缓存结果
    """
    from app.rag.retriever import RetrievedChunk
    from app.core.config import get_settings
    
    settings = get_settings()
    redis_client = None
    cache_key = None
    
    # 1. 尝试从缓存获取（如果启用缓存）
    if settings.enable_search_cache and settings.redis_url:
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.redis_url, decode_responses=False)
            cache_key = generate_search_cache_key(
                query=payload.query,
                library_id=str(payload.library_id) if payload.library_id else None,
                limit=payload.limit,
                user_id=str(current_user.id)
            )
            
            cached_result = await get_cached_search_result(redis_client, cache_key)
            if cached_result is not None:
                # 记录缓存命中
                await record_cache_stats(redis_client, hit=True)
                logger.info(f"搜索缓存命中: {cache_key}")
                await redis_client.aclose()
                return StandardResponse(data=cached_result)
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
            if redis_client:
                try:
                    await redis_client.aclose()
                except:
                    pass
                redis_client = None
    
    # 2. 使用混合检索获取相关 chunks
    library_ids = [payload.library_id] if payload.library_id else None
    # 获取更多候选结果，用于后续聚合和评分
    chunks = await retriever.search(
        query=payload.query,
        top_k=payload.limit * 5,  # 获取更多候选，用于文档聚合
        library_ids=library_ids,
        use_hybrid=True
    )
    
    if not chunks:
        return StandardResponse(data=[])
    
    # 2. 按文档聚合结果，收集所有匹配的 chunks 和分数
    doc_chunks: dict[str, list[RetrievedChunk]] = {}
    doc_vector_scores: dict[str, list[float]] = {}
    
    for chunk in chunks:
        doc_id = chunk.document_id
        if doc_id not in doc_chunks:
            doc_chunks[doc_id] = []
            doc_vector_scores[doc_id] = []
        doc_chunks[doc_id].append(chunk)
        doc_vector_scores[doc_id].append(chunk.score)
    
    # 3. 获取所有相关文档信息（批量查询，避免 N+1）
    doc_ids = list(doc_chunks.keys())
    docs_result = await session.execute(
        select(Document).where(Document.id.in_([uuid.UUID(doc_id) for doc_id in doc_ids]))
    )
    docs_dict = {str(doc.id): doc for doc in docs_result.scalars().all()}
    
    # 4. 计算文档综合分数
    query_lower = payload.query.lower()
    doc_final_scores: dict[str, float] = {}
    
    for doc_id, chunks_list in doc_chunks.items():
        doc = docs_dict.get(doc_id)
        if not doc:
            continue
        
        # 权限检查
        has_access = False
        if doc.library_id:
            try:
                library = await _get_library_or_404(session, doc.library_id)
                if library.owner_type == "user":
                    has_access = library.owner_id == current_user.id
                elif library.owner_type == "group":
                    try:
                        await _assert_group_member(
                            session, group_id=library.owner_id, user_id=current_user.id, 
                            allowed_roles=("owner", "admin", "member")
                        )
                        has_access = True
                    except HTTPException:
                        has_access = False
            except HTTPException:
                has_access = False
        else:
            # Documents without library are accessible to owner
            has_access = True
        
        if not has_access:
            continue
        
        # 计算综合分数
        # 基础分数：向量检索的最高分（或加权平均）
        vector_score = max(doc_vector_scores[doc_id]) if doc_vector_scores[doc_id] else 0.0
        
        # 标题匹配增强（完全匹配权重更高）
        title_score = 0.0
        title_lower = doc.title.lower()
        if query_lower == title_lower:
            title_score = 0.5  # 完全匹配
        elif query_lower in title_lower:
            title_score = 0.3  # 部分匹配
        elif any(word in title_lower for word in query_lower.split() if len(word) > 1):
            title_score = 0.1  # 关键词匹配
        
        # 匹配次数增强（多次匹配说明更相关）
        match_count_boost = min(0.2, len(chunks_list) * 0.05)  # 最多增加 0.2
        
        # 综合分数 = 向量分数（归一化到 0-1） + 标题匹配 + 匹配次数增强
        # 向量分数已经是归一化的，直接使用
        final_score = vector_score + title_score + match_count_boost
        
        doc_final_scores[doc_id] = final_score
    
    # 5. 按分数排序并限制数量
    sorted_doc_ids = sorted(
        doc_final_scores.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:payload.limit]
    
    # 6. 构建响应
    results: list[DocumentSearchResult] = []
    for doc_id, score in sorted_doc_ids:
        doc = docs_dict.get(doc_id)
        if not doc:
            continue
        
        # 获取最佳匹配的 chunk 作为 snippet
        best_chunk = max(doc_chunks[doc_id], key=lambda c: c.score)
        snippet = best_chunk.text
        
        # 如果 snippet 太长，截取并添加省略号
        if len(snippet) > 200:
            # 尝试在查询词附近截取
            query_pos = snippet.lower().find(query_lower)
            if query_pos >= 0:
                start = max(0, query_pos - 80)
                end = min(len(snippet), query_pos + len(payload.query) + 80)
                snippet = snippet[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(best_chunk.text):
                    snippet = snippet + "..."
            else:
                snippet = snippet[:200] + "..."
        
        results.append(
            DocumentSearchResult(
                document_id=doc_id,
                title=doc.title,
                snippet=snippet,
                score=round(score, 4),  # 保留4位小数
                library_id=str(doc.library_id) if doc.library_id else None,
            )
        )
    
    # 7. 缓存结果（如果启用缓存）
    if settings.enable_search_cache and settings.redis_url and results:
        try:
            if not redis_client:
                import redis.asyncio as redis
                redis_client = redis.from_url(settings.redis_url, decode_responses=False)
                cache_key = generate_search_cache_key(
                    query=payload.query,
                    library_id=str(payload.library_id) if payload.library_id else None,
                    limit=payload.limit,
                    user_id=str(current_user.id)
                )
            
            # 转换为可序列化的格式
            cache_data = [
                {
                    "document_id": r.document_id,
                    "title": r.title,
                    "snippet": r.snippet,
                    "score": r.score,
                    "library_id": r.library_id
                }
                for r in results
            ]
            
            # 动态计算 TTL
            ttl = calculate_cache_ttl(
                result_count=len(results),
                query_length=len(payload.query)
            )
            # 使用配置的 TTL 作为上限
            ttl = min(ttl, settings.search_cache_ttl)
            
            await cache_search_result(redis_client, cache_key, cache_data, ttl)
            # 记录缓存未命中
            await record_cache_stats(redis_client, hit=False)
            logger.debug(f"搜索缓存写入: {cache_key}, TTL: {ttl}s")
        except Exception as e:
            logger.warning(f"缓存写入失败: {e}")
        finally:
            if redis_client:
                try:
                    await redis_client.aclose()
                except:
                    pass
    
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

