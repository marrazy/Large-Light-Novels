import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from large_light_novels.db.base import Base

EMBEDDING_DIMENSIONS = 1536


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Library(TimestampMixin, Base):
    __tablename__ = "libraries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source_language: Mapped[str] = mapped_column(String(16), nullable=False)
    target_language: Mapped[str] = mapped_column(String(16), nullable=False, default="en")

    documents: Mapped[list["Document"]] = relationship(
        back_populates="library", cascade="all, delete-orphan"
    )
    entities: Mapped[list["Entity"]] = relationship(
        back_populates="library", cascade="all, delete-orphan"
    )
    glossary_entries: Mapped[list["GlossaryEntry"]] = relationship(
        back_populates="library", cascade="all, delete-orphan"
    )
    memories: Mapped[list["Memory"]] = relationship(
        back_populates="library", cascade="all, delete-orphan"
    )
    relationships: Mapped[list["Relationship"]] = relationship(
        back_populates="library", cascade="all, delete-orphan"
    )
    translation_runs: Mapped[list["TranslationRun"]] = relationship(
        back_populates="library", cascade="all, delete-orphan"
    )


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("library_id", "checksum", name="uq_documents_library_checksum"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    library_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("libraries.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_path: Mapped[str | None] = mapped_column(String(1024))
    checksum: Mapped[str | None] = mapped_column(String(64))

    library: Mapped[Library] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="Chunk.sequence_number"
    )
    translation_runs: Mapped[list["TranslationRun"]] = relationship(back_populates="document")


class Chunk(TimestampMixin, Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "sequence_number", name="uq_chunks_document_sequence"),
        Index("ix_chunks_document_sequence", "document_id", "sequence_number"),
        Index(
            "ix_chunks_source_embedding_hnsw",
            "source_embedding",
            postgresql_using="hnsw",
            postgresql_ops={"source_embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    source_embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))

    document: Mapped[Document] = relationship(back_populates="chunks")
    translations: Mapped[list["Translation"]] = relationship(
        back_populates="chunk", cascade="all, delete-orphan", order_by="Translation.version"
    )
    memories: Mapped[list["Memory"]] = relationship(back_populates="chunk")


class Translation(TimestampMixin, Base):
    __tablename__ = "translations"
    __table_args__ = (UniqueConstraint("chunk_id", "version", name="uq_translations_chunk_version"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    translated_text: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed")
    retrieved_context: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    chunk: Mapped[Chunk] = relationship(back_populates="translations")


class Entity(TimestampMixin, Base):
    __tablename__ = "entities"
    __table_args__ = (
        UniqueConstraint("library_id", "canonical_source_name", name="uq_entities_library_source_name"),
        Index("ix_entities_library_type", "library_id", "entity_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    library_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("libraries.id", ondelete="CASCADE"))
    canonical_source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    canonical_target_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    pronouns: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None]

    library: Mapped[Library] = relationship(back_populates="entities")
    aliases: Mapped[list["EntityAlias"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )
    subject_relationships: Mapped[list["Relationship"]] = relationship(
        back_populates="subject_entity", foreign_keys="Relationship.subject_entity_id"
    )
    object_relationships: Mapped[list["Relationship"]] = relationship(
        back_populates="object_entity", foreign_keys="Relationship.object_entity_id"
    )


class EntityAlias(Base):
    __tablename__ = "entity_aliases"
    __table_args__ = (
        UniqueConstraint("entity_id", "language", "alias", name="uq_entity_aliases_entity_language_alias"),
        Index("ix_entity_aliases_lookup", "language", "alias"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"))
    language: Mapped[str] = mapped_column(String(16), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), nullable=False)

    entity: Mapped[Entity] = relationship(back_populates="aliases")


class GlossaryEntry(TimestampMixin, Base):
    __tablename__ = "glossary_entries"
    __table_args__ = (UniqueConstraint("library_id", "source_term", name="uq_glossary_library_source_term"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    library_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("libraries.id", ondelete="CASCADE"))
    source_term: Mapped[str] = mapped_column(String(255), nullable=False)
    target_term: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=True)

    library: Mapped[Library] = relationship(back_populates="glossary_entries")


class Memory(TimestampMixin, Base):
    __tablename__ = "memories"
    __table_args__ = (
        Index("ix_memories_library_type", "library_id", "memory_type"),
        Index(
            "ix_memories_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    library_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("libraries.id", ondelete="CASCADE"))
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chunks.id", ondelete="SET NULL"))
    memory_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    confidence: Mapped[float | None]
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))

    library: Mapped[Library] = relationship(back_populates="memories")
    chunk: Mapped[Chunk | None] = relationship(back_populates="memories")


class Relationship(TimestampMixin, Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("library_id", "subject_entity_id", "predicate", "object_entity_id", name="uq_relationships_fact"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    library_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("libraries.id", ondelete="CASCADE"))
    subject_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"))
    predicate: Mapped[str] = mapped_column(String(128), nullable=False)
    object_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"))
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None]

    library: Mapped[Library] = relationship(back_populates="relationships")
    subject_entity: Mapped[Entity] = relationship(
        back_populates="subject_relationships", foreign_keys=[subject_entity_id]
    )
    object_entity: Mapped[Entity] = relationship(
        back_populates="object_relationships", foreign_keys=[object_entity_id]
    )


class TranslationRun(TimestampMixin, Base):
    __tablename__ = "translation_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    library_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("libraries.id", ondelete="CASCADE"))
    document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    library: Mapped[Library] = relationship(back_populates="translation_runs")
    document: Mapped[Document | None] = relationship(back_populates="translation_runs")