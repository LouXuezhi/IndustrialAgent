import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, TypeDecorator, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type for MySQL compatibility.
    
    Uses CHAR(36) for MySQL and native UUID for PostgreSQL.
    """
    impl = String
    cache_ok = True
    length = 36

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(self.length))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


UUIDType = GUID


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    source_path: Mapped[str] = mapped_column(String(512))
    library_id: Mapped[uuid.UUID | None] = mapped_column(UUIDType, ForeignKey("document_libraries.id"), nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)  # Column name is "metadata" in DB
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document")
    library: Mapped["DocumentLibrary"] = relationship(back_populates="documents")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("documents.id"))
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)  # Column name is "metadata" in DB

    document: Mapped[Document] = relationship(back_populates="chunks")


class DocumentLibrary(Base):
    __tablename__ = "document_libraries"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False, index=True)
    owner_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # "user" | "group"
    vector_collection_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)  # 标记是否为用户的默认个人库
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)  # Column name is "metadata" in DB
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    documents: Mapped[list[Document]] = relationship(back_populates="library")
    group: Mapped["Group"] = relationship(back_populates="libraries", foreign_keys=[owner_id], primaryjoin="DocumentLibrary.owner_id==Group.id")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="operator")
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    verification_token: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    verification_token_expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)  # Column name is "metadata" in DB
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    last_login_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    rating: Mapped[int] = mapped_column()
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)  # Column name is "metadata" in DB
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)  # Column name is "metadata" in DB
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    members: Mapped[list["GroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    libraries: Mapped[list["DocumentLibrary"]] = relationship(
        back_populates="group",
        cascade="all, delete",
        primaryjoin="and_(foreign(DocumentLibrary.owner_id)==Group.id, DocumentLibrary.owner_type=='group')",
        foreign_keys="[DocumentLibrary.owner_id]",
    )


class GroupMember(Base):
    __tablename__ = "group_members"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("groups.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(16), default="member")  # owner|admin|member
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    group: Mapped[Group] = relationship(back_populates="members")

