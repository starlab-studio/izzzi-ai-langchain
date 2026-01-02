from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.entities.sentiment import SentimentAnalysis

class ISentimentRepository(ABC):
    """Interface for sentiment analysis"""
    
    @abstractmethod
    async def save(self, sentiment: SentimentAnalysis) -> SentimentAnalysis:
        """Save a sentiment analysis"""
        pass
    
    @abstractmethod
    async def find_by_subject(
        self,
        subject_id: UUID,
    ) -> Optional[SentimentAnalysis]:
        """Find the most recent sentiment analysis for a subject"""
        pass
    
    @abstractmethod
    async def find_latest(
        self,
        subject_id: UUID,
        limit: int = 1,
    ) -> list[SentimentAnalysis]:
        """Find recents sentiments analysis for a subject"""
        pass

