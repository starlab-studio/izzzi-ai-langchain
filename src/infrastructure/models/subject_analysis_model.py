from sqlalchemy import Column, String, Text, Float, Integer, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid

from src.infrastructure.database.connection import Base

class SubjectAnalysisModel(Base):
    __tablename__ = "subject_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    analysis_type = Column(String(50), nullable=False, index=True)
    period_start = Column(TIMESTAMP, nullable=False)
    period_end = Column(TIMESTAMP, nullable=False)
    result = Column(JSONB, nullable=False)
    analysis_metadata = Column("metadata", JSONB, default={})  # Renamed to avoid SQLAlchemy reserved name
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())