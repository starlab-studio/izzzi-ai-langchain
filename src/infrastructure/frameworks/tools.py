from typing import Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from src.application.use_cases.analyze_subject_sentiment import AnalyzeSubjectSentimentUseCase
from src.application.use_cases.semantic_search import SemanticSearchUseCase
from src.application.use_cases.cluster_responses import ClusterResponsesUseCase

# ==========================================
# Pydantic schemas pour les tools
# ==========================================

class SentimentAnalysisInput(BaseModel):
    """Input pour l'outil d'analyse de sentiment"""
    subject_id: str = Field(description="UUID de la matière à analyser")
    period_days: int = Field(default=30, description="Nombre de jours à analyser")

class SemanticSearchInput(BaseModel):
    """Input pour la recherche sémantique"""
    query: str = Field(description="Question ou texte à rechercher")
    subject_id: str = Field(description="UUID de la matière")
    limit: int = Field(default=10, description="Nombre de résultats")

class ClusterAnalysisInput(BaseModel):
    """Input pour le clustering"""
    subject_id: str = Field(description="UUID de la matière")
    n_clusters: int = Field(default=5, description="Nombre de clusters à créer")

# ==========================================
# Tools LangChain
# ==========================================

class SentimentAnalysisTool(BaseTool):
    """Outil pour analyser le sentiment d'une matière"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "analyze_subject_sentiment"
    description: str = """Utile pour analyser le sentiment général des élèves sur une matière.
    Retourne un score de sentiment (-1 à 1), la distribution positive/neutre/négative,
    et des insights sur ce qui va bien ou mal."""
    args_schema: Type[BaseModel] = SentimentAnalysisInput
    
    use_case: Optional[AnalyzeSubjectSentimentUseCase] = Field(default=None, exclude=True)
    
    def __init__(self, use_case: AnalyzeSubjectSentimentUseCase, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'use_case', use_case)
    
    async def _arun(self, subject_id: str, period_days: int = 30) -> str:
        """Exécution asynchrone"""
        from uuid import UUID
        result = await self.use_case.execute(
            subject_id=UUID(subject_id),
            period_days=period_days,
        )
        
        return f"""Analyse de sentiment :
            - Score global : {result['overall_score']:.2f} ({result['label']})
            - Distribution : {result['positive_percentage']:.0f}% positif, {result['negative_percentage']:.0f}% négatif
            - Tendance : {result.get('trend_percentage', 'N/A')}
            - Points positifs : {', '.join(result.get('positive_points', [])[:3])}
            - Points négatifs : {', '.join(result.get('negative_points', [])[:3])}
        """
    
    def _run(self, subject_id: str, period_days: int = 30) -> str:
        """Fallback synchrone (non utilisé en async)"""
        raise NotImplementedError("Use async version")

class SemanticSearchTool(BaseTool):
    """Outil pour rechercher des réponses similaires"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "search_similar_responses"
    description: str = """Utile pour trouver des réponses d'élèves similaires à une question ou un thème.
    Par exemple : "Trouve toutes les mentions du rythme du cours" ou "Cherche les commentaires sur les supports"."""
    args_schema: Type[BaseModel] = SemanticSearchInput
    
    use_case: Optional[SemanticSearchUseCase] = Field(default=None, exclude=True)
    
    def __init__(self, use_case: SemanticSearchUseCase, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'use_case', use_case)
    
    async def _arun(self, query: str, subject_id: str, limit: int = 10) -> str:
        """Exécution asynchrone"""
        from uuid import UUID
        results = await self.use_case.execute(
            query=query,
            subject_id=UUID(subject_id),
            limit=limit,
        )
        
        if not results:
            return "Aucune réponse similaire trouvée."
        
        output = f"Trouvé {len(results)} réponses pertinentes :\n\n"
        for i, result in enumerate(results[:5], 1):
            output += f"{i}. (Similarité: {result['similarity']:.2f}) {result['text'][:200]}...\n\n"
        
        return output
    
    def _run(self, query: str, subject_id: str, limit: int = 10) -> str:
        raise NotImplementedError("Use async version")

class ClusterAnalysisTool(BaseTool):
    """Outil pour identifier les thèmes récurrents"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "identify_themes"
    description: str = """Utile pour identifier automatiquement les thèmes principaux 
    qui ressortent des retours d'élèves. Regroupe les réponses similaires par thème."""
    args_schema: Type[BaseModel] = ClusterAnalysisInput
    
    use_case: Optional[ClusterResponsesUseCase] = Field(default=None, exclude=True)
    
    def __init__(self, use_case: ClusterResponsesUseCase, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'use_case', use_case)
    
    async def _arun(self, subject_id: str, n_clusters: int = 5) -> str:
        """Exécution asynchrone"""
        from uuid import UUID
        result = await self.use_case.execute(
            subject_id=UUID(subject_id),
            n_clusters=n_clusters,
        )
        
        if not result.get('clusters'):
            return "Pas assez de données pour identifier des thèmes."
        
        output = f"Identifié {len(result['clusters'])} thèmes principaux :\n\n"
        for cluster in result['clusters']:
            output += f"Thème : {cluster['label']}\n"
            output += f"- Mentions : {cluster['count']}\n"
            output += f"- Sentiment : {cluster['sentiment']:.2f}\n"
            output += f"- Exemples : {', '.join(cluster['examples'][:2])}\n\n"
        
        return output
    
    def _run(self, subject_id: str, n_clusters: int = 5) -> str:
        raise NotImplementedError("Use async version")