from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class ISubjectAnalysisRepository(ABC):
    """Interface for subject analysis repository"""
    
    @abstractmethod
    async def save(
        self,
        subject_id: UUID,
        organization_id: UUID,
        analysis_type: str,
        period_start: datetime,
        period_end: datetime,
        result: dict,
        created_by_user_id: Optional[UUID] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Save a subject analysis"""
        pass
    
    @abstractmethod
    async def find_by_subject(
        self,
        subject_id: UUID,
        analysis_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        """Find subject analysis for a subject"""
        pass
    
    @abstractmethod
    async def find_by_period(
        self,
        subject_id: UUID,
        period_start: datetime,
        period_end: datetime,
        analysis_type: Optional[str] = None,
    ) -> List[dict]:
        """Find subject analysis by period"""
        pass
    
    @abstractmethod
    async def find_latest(
        self,
        subject_id: UUID,
        analysis_type: Optional[str] = None,
    ) -> Optional[dict]:
        """Find the most recent subject analysis"""
        pass

