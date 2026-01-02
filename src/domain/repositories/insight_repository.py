from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.insight import Insight, InsightPriority, InsightType

class IInsightRepository(ABC):
    """Interface for insights repository"""
    
    @abstractmethod
    async def save(self, insight: Insight) -> Insight:
        """Save an insight"""
        pass
    
    @abstractmethod
    async def find_by_subject(
        self,
        subject_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Insight]:
        """Find insights for a subject"""
        pass
    
    @abstractmethod
    async def find_by_organization(
        self,
        organization_id: UUID,
        limit: Optional[int] = None,
    ) -> List[Insight]:
        """Find insights for an organisation"""
        pass
    
    @abstractmethod
    async def find_actionable(
        self,
        subject_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
    ) -> List[Insight]:
        """Find insights with required action (high/urgent priority)"""
        pass
    
    @abstractmethod
    async def find_by_type(
        self,
        insight_type: InsightType,
        subject_id: Optional[UUID] = None,
        limit: Optional[int] = None,
    ) -> List[Insight]:
        """Find insights by type"""
        pass
    
    @abstractmethod
    async def delete(self, insight_id: UUID) -> bool:
        """Delete an insight"""
        pass

