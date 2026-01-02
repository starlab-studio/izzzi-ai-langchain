from sqlalchemy import Column, String, Text, Float, Integer, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid

from src.infrastructure.database.connection import Base

class AnalysisCacheModel(Base):
    __tablename__ = "analysis_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    cache_value = Column(JSONB, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())