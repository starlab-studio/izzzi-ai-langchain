from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
from uuid import UUID, uuid4

class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

@dataclass
class SentimentEvidence:
    """Preuve d'un sentiment"""
    text: str
    response_id: UUID
    created_at: datetime
    confidence: float

@dataclass
class SentimentAnalysis:
    """Sentiment analysis for on subject"""
    id: UUID = field(default_factory=uuid4)
    subject_id: UUID = None
    organization_id: UUID = None
    
    # Scores
    overall_score: float = 0.0  # -1 à 1
    confidence: float = 0.0
    
    # Distribution
    positive_percentage: float = 0.0
    neutral_percentage: float = 0.0
    negative_percentage: float = 0.0
    
    # Trend
    trend_percentage: Optional[float] = None
    previous_score: Optional[float] = None
    
    # Evidence
    positive_evidence: List[SentimentEvidence] = field(default_factory=list)
    negative_evidence: List[SentimentEvidence] = field(default_factory=list)
    
    # Metadata
    total_responses: int = 0
    period_start: datetime = None
    period_end: datetime = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_label(self) -> SentimentLabel:
        """Return the dominant lable"""
        if self.overall_score > 0.3:
            return SentimentLabel.POSITIVE
        elif self.overall_score < -0.3:
            return SentimentLabel.NEGATIVE
        return SentimentLabel.NEUTRAL
    
    def is_trending_up(self) -> bool:
        """Sentiment is trending up ?"""
        return self.trend_percentage is not None and self.trend_percentage > 0