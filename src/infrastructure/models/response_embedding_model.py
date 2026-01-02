from sqlalchemy import Column, String, Text, Float, Integer, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid

from src.infrastructure.database.connection import Base

class ResponseEmbeddingModel(Base):
    __tablename__ = "response_embeddings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    response_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    answer_id = Column(UUID(as_uuid=True), nullable=True)
    text_content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    embedding_metadata = Column("metadata", JSONB, default={})  # Renamed to avoid SQLAlchemy reserved name
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())