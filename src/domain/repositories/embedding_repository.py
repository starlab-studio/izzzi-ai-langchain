from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID

from src.domain.entities.embedding import ResponseEmbedding

class IEmbeddingRepository(ABC):
    """Interface for embeddings repository"""
    
    @abstractmethod
    async def save(self, embedding: ResponseEmbedding) -> ResponseEmbedding:
        """Save an embedding"""
        pass
    
    @abstractmethod
    async def save_batch(self, embeddings: List[ResponseEmbedding]) -> int:
        """Save a batch of multiple embeddings"""
        pass
    
    @abstractmethod
    async def find_similar(
        self,
        query_embedding: List[float],
        subject_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        limit: int = 20,
        similarity_threshold: float = 0.7,
    ) -> List[Tuple[ResponseEmbedding, float]]:
        """Vector search with pgvector"""
        pass
    
    @abstractmethod
    async def get_unindexed_responses(self, limit: int = 1000) -> List[dict]:
        """Retrive non indexed text"""
        pass
    
    @abstractmethod
    async def count_by_subject(self, subject_id: UUID) -> int:
        """Count embeddings for a subject"""
        pass

