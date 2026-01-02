from sqlalchemy import Column, String, Text, Float, Integer, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid

from src.infrastructure.database.connection import Base

class InsightModel(Base):
    __tablename__ = "insights"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    insight_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    evidence = Column(JSONB, default={})
    confidence = Column(Float, nullable=True)
    priority = Column(String(20), nullable=True)
    insight_metadata = Column("metadata", JSONB, default={})  # Renamed to avoid SQLAlchemy reserved name
    created_at = Column(TIMESTAMP, server_default=func.now())