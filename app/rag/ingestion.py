import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.db.models import Chunk, Document


def _extract_text_from_file(path: Path) -> str:
    """Extract text from various file formats."""
    suffix = path.suffix.lower()
    
    if suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            text_parts = []
            total_chars = 0
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    total_chars += len(page_text.strip())
            
            # 检查是否为文本型PDF
            # 如果提取的文本很少（少于每页平均50个字符），可能是扫描型PDF
            num_pages = len(reader.pages)
            if num_pages > 0:
                avg_chars_per_page = total_chars / num_pages
                if avg_chars_per_page < 50:
                    raise ValueError(
                        f"PDF appears to be scanned/image-based (only {total_chars} characters extracted from {num_pages} pages, "
                        f"average {avg_chars_per_page:.1f} chars/page). "
                        f"Text-based PDFs are required. Please use OCR to convert scanned PDFs to text first."
                    )
            
            if not text_parts:
                raise ValueError(
                    "No text could be extracted from PDF. This may be a scanned/image-based PDF. "
                    "Text-based PDFs are required. Please use OCR to convert scanned PDFs to text first."
                )
            
            return "\n".join(text_parts)
        except ValueError:
            # Re-raise ValueError (our custom errors for scanned PDFs)
            raise
        except Exception as e:
            # Other exceptions (file read errors, etc.)
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    elif suffix in [".docx", ".doc"]:
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(path)
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        except Exception:
            return ""
    elif suffix in [".md", ".markdown"]:
        return path.read_text(encoding="utf-8", errors="ignore")
    else:
        # Fallback: try to read as text
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""


@dataclass
class IngestionReport:
    document_id: uuid.UUID
    chunk_count: int
    vectorized: bool = False
    error: str | None = None


def _resolve_chroma_path(vector_uri: str) -> str:
    """Accept formats like chroma://./chroma_store and return filesystem path."""
    prefix = "chroma://"
    if vector_uri.startswith(prefix):
        return vector_uri[len(prefix) :]
    return vector_uri


def _build_embedding_fn(settings: Settings):
    # Prefer configured embedding provider; fallback to default.
    if settings.llm_provider == "dashscope" and settings.dashscope_api_key:
        # DashScope provides an OpenAI-compatible endpoint; use api_base to direct traffic.
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.dashscope_embedding_api_key or settings.dashscope_api_key,
            model_name=settings.embedding_model,
            api_base=settings.dashscope_embedding_base_url or settings.dashscope_base_url,
        )
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    return embedding_functions.DefaultEmbeddingFunction()


class DocumentIngestor:
    """Persist documents/chunks and write embeddings into Chroma vector store."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        chroma_path = _resolve_chroma_path(self.settings.vector_db_uri)
        self._client = chromadb.PersistentClient(path=chroma_path)
        self._embedding_fn = _build_embedding_fn(self.settings)

    def _get_collection(self, library_id: uuid.UUID | None):
        name = f"library_{library_id}" if library_id else "library_default"
        return self._client.get_or_create_collection(
            name=name,
            embedding_function=self._embedding_fn,
            metadata={"library_id": str(library_id) if library_id else None},
        )

    async def vectorize_document(
        self,
        document: Document,
        session: AsyncSession,
        chunk_size: int = 800,
    ) -> IngestionReport:
        """Chunk an existing document file and write embeddings."""
        path = Path(document.source_path)
        if not path.exists():
            error_msg = f"Document file not found on disk: {path}"
            meta = dict(document.meta or {})
            meta["vectorized"] = False
            document.meta = meta
            await session.commit()
            return IngestionReport(document_id=document.id, chunk_count=0, vectorized=False, error=error_msg)

        try:
            text = _extract_text_from_file(path)
        except ValueError as e:
            # PDF text extraction errors (e.g., scanned PDFs)
            error_msg = str(e)
            meta = dict(document.meta or {})
            meta["vectorized"] = False
            document.meta = meta
            await session.commit()
            return IngestionReport(document_id=document.id, chunk_count=0, vectorized=False, error=error_msg)
        
        if not text.strip():
            error_msg = f"Could not extract text from file: {path}"
            meta = dict(document.meta or {})
            meta["vectorized"] = False
            document.meta = meta
            await session.commit()
            return IngestionReport(document_id=document.id, chunk_count=0, vectorized=False, error=error_msg)

        # Clear existing chunks to avoid duplication on re-run
        existing_chunks = await session.execute(select(Chunk).where(Chunk.document_id == document.id))
        for ch in existing_chunks.scalars().all():
            await session.delete(ch)
        await session.flush()

        # naive chunking
        chunks: list[Chunk] = []
        if not text.strip():
            text = " "

        for start in range(0, len(text), chunk_size):
            part = text[start : start + chunk_size]
            chunk = Chunk(
                id=uuid.uuid4(),  # Explicitly generate UUID
                document_id=document.id,
                content=part,
                meta={"offset": start, "length": len(part)},
            )
            chunks.append(chunk)

        session.add_all(chunks)
        await session.flush()  # Flush to ensure chunk IDs are generated
        # write embeddings (best-effort but report failures)
        vectorized = False
        error: str | None = None
        try:
            collection = self._get_collection(document.library_id)
            ids = [str(chunk.id) for chunk in chunks]
            # Ensure no None IDs
            if None in ids:
                raise ValueError("Some chunk IDs are None after flush")
            documents = [chunk.content for chunk in chunks]
            metadatas: list[dict[str, Any]] = []
            for chunk in chunks:
                meta = {"document_id": str(document.id), "offset": chunk.meta.get("offset"), "length": chunk.meta.get("length")}
                if document.library_id:
                    meta["library_id"] = str(document.library_id)
                metadatas.append(meta)
            collection.add(ids=ids, documents=documents, metadatas=metadatas)
            vectorized = True
        except Exception as exc:
            vectorized = False
            error = str(exc)

        # mark vectorized flag in meta
        meta = dict(document.meta or {})
        meta["chunk_size"] = chunk_size
        meta["vectorized"] = vectorized
        document.meta = meta
        await session.commit()
        await session.refresh(document)

        return IngestionReport(document_id=document.id, chunk_count=len(chunks), vectorized=vectorized, error=error)

