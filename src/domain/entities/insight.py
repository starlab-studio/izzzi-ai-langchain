from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

class InsightType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    RECOMMENDATION = "recommendation"
    ALERT = "alert"

class InsightPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Insight:
    """Insight généré par l'IA"""
    id: UUID = field(default_factory=uuid4)
    subject_id: UUID = None
    organization_id: UUID = None
    
    type: InsightType = InsightType.RECOMMENDATION
    priority: InsightPriority = InsightPriority.MEDIUM
    
    title: str = ""
    content: str = ""
    
    # Evidence
    evidence_texts: List[str] = field(default_factory=list)
    evidence_count: int = 0
    confidence: float = 0.0
    
    # Embedding for similarity search
    embedding: Optional[List[float]] = None
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_actionable(self) -> bool:
        """Nécessite une action ?"""
        return self.priority in [InsightPriority.HIGH, InsightPriority.URGENT]