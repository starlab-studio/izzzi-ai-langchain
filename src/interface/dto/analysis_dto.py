from pydantic import BaseModel, Field, UUID4
from typing import List, Optional, Dict, Any
from datetime import datetime

# === Request Schemas ===

class AnalyzeSentimentRequest(BaseModel):
    """Requête pour analyser le sentiment"""
    subject_id: UUID4 = Field(..., description="UUID de la matière")
    period_days: int = Field(30, ge=7, le=365, description="Période d'analyse en jours")

class SemanticSearchRequest(BaseModel):
    """Requête pour recherche sémantique"""
    query: str = Field(..., min_length=3, max_length=500, description="Question ou texte à rechercher")
    subject_id: UUID4 = Field(..., description="UUID de la matière")
    limit: int = Field(20, ge=1, le=100, description="Nombre de résultats")

class GenerateInsightsRequest(BaseModel):
    """Requête pour générer des insights"""
    subject_id: UUID4
    period_days: int = Field(30, ge=7, le=365)

class ChatbotQueryRequest(BaseModel):
    """Requête pour le chatbot"""
    query: str = Field(..., min_length=5, max_length=1000)
    subject_id: UUID4
    context: Optional[Dict[str, Any]] = None

class CompareSubjectsRequest(BaseModel):
    """Requête pour comparer des matières"""
    subject_ids: List[UUID4] = Field(..., min_items=2, max_items=10)
    period_days: int = Field(30, ge=7, le=365)

class PredictRisksRequest(BaseModel):
    """Requête pour analyse prédictive"""
    subject_id: UUID4
    lookback_days: int = Field(90, ge=30, le=365)

# === Response Schemas ===

class SentimentEvidenceResponse(BaseModel):
    """Preuve d'un sentiment"""
    point: str
    example: str
    response_id: str

class ThemeResponse(BaseModel):
    """Thème identifié"""
    id: str
    label: str
    count: int
    sentiment: float
    keywords: List[str]
    examples: List[str]

class SentimentAnalysisResponse(BaseModel):
    """Réponse analyse de sentiment"""
    subject_id: str
    period_start: str
    period_end: str
    overall_score: float = Field(..., ge=-1, le=1)
    confidence: float = Field(..., ge=0, le=1)
    label: str  # positive, neutral, negative
    positive_percentage: float
    neutral_percentage: float
    negative_percentage: float
    trend_percentage: Optional[float] = None
    positive_points: List[str]
    negative_points: List[str]
    recommendations: List[str]
    positive_evidence: List[SentimentEvidenceResponse]
    negative_evidence: List[SentimentEvidenceResponse]
    themes: List[ThemeResponse] = []
    total_responses: int
    star_average: float

class SemanticSearchResultResponse(BaseModel):
    """Résultat de recherche sémantique"""
    text: str
    similarity: float = Field(..., ge=0, le=1)
    response_id: str
    answer_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: str

class InsightResponse(BaseModel):
    """Insight généré"""
    type: str  # positive, negative, recommendation, alert
    priority: str  # low, medium, high, urgent
    title: str
    content: str
    evidence: List[Dict[str, Any]]
    confidence: Optional[float] = None

class ComprehensiveInsightsResponse(BaseModel):
    """Insights complets"""
    subject_id: str
    period_days: int
    sentiment: SentimentAnalysisResponse
    themes: List[ThemeResponse]
    insights: List[InsightResponse]
    generated_at: str

class ChatbotResponse(BaseModel):
    """Réponse du chatbot"""
    query: str
    answer: str
    tools_used: List[str]
    intermediate_steps: List[Dict[str, Any]] = []

class ComparisonResponse(BaseModel):
    """Comparaison de matières"""
    subjects_compared: int
    comparison: Dict[str, SentimentAnalysisResponse]
    winner: str
    key_differences: List[str]

class RiskPredictionResponse(BaseModel):
    """Prédiction de risques"""
    subject_id: str
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: str  # low, medium, high, critical
    confidence: float
    factors: List[str]
    recommendations: List[str]
    historical_data: List[Dict[str, Any]]
    trend: float