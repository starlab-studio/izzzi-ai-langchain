from sqlalchemy import Column, String, Text, Float, Integer, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid

from src.infrastructure.database.connection import Base

class ChatbotConversationModel(Base):
    __tablename__ = "chatbot_conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    subject_id = Column(UUID(as_uuid=True), nullable=True)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    sources = Column(JSONB, default=[])
    conversation_metadata = Column("metadata", JSONB, default={})
    created_at = Column(TIMESTAMP, server_default=func.now())