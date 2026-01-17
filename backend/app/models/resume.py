from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import Base

# Try to import Vector, fallback to JSONB if pgvector is not available
try:
    from pgvector.sqlalchemy import Vector
    VECTOR_AVAILABLE = True
except ImportError:
    VECTOR_AVAILABLE = False
    # Use JSONB as fallback for embedding_vector
    Vector = JSONB


class ResumeStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    file_path = Column(String(512), nullable=False)  # S3 path or local path
    file_name = Column(String(255), nullable=False)
    file_size = Column(String(50), nullable=True)  # File size in bytes
    file_type = Column(String(50), nullable=False)  # pdf, doc, docx
    parsed_data_json = Column(JSONB, nullable=True)  # Extracted text, skills, experience, etc.
    # Use Vector if pgvector is available, otherwise use JSONB
    embedding_vector = Column(
        Vector(384) if VECTOR_AVAILABLE else JSONB, 
        nullable=True
    )  # BERT embedding vector (Vector(384) or JSONB)
    status = Column(Enum(ResumeStatus), default=ResumeStatus.UPLOADED, nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    uploader = relationship("User", backref="resumes")
    candidates = relationship("Candidate", back_populates="resume", cascade="all, delete-orphan")
    processing_queues = relationship("ProcessingQueue", back_populates="resume", cascade="all, delete-orphan")

    # Index for vector similarity search (only if pgvector is available)
    __table_args__ = (
        Index('ix_resume_embedding', 'embedding_vector', postgresql_using='ivfflat') if VECTOR_AVAILABLE else (),
    ) if VECTOR_AVAILABLE else ()

    def __repr__(self):
        return f"<Resume(id={self.id}, file_name={self.file_name}, status={self.status})>"

