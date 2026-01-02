from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from src.application.facades.analysis_facade import AnalysisFacade
from src.infrastructure.frameworks.langchain_service import LangChainService
from src.infrastructure.repositories.postgres_analysis_cache_repository import (
    PostgresAnalysisCacheRepository
)
from src.core.logger import app_logger
from src.core.exceptions import InsufficientDataException

class GenerateFeedbackSummaryUseCase:
    """Use case pour générer un résumé de feedback pour une matière"""
    
    def __init__(
        self,
        analysis_facade: AnalysisFacade,
        langchain_service: LangChainService,
        cache_repo: PostgresAnalysisCacheRepository,
    ):
        self.analysis_facade = analysis_facade
        self.langchain_service = langchain_service
        self.cache_repo = cache_repo
    
    async def execute(
        self,
        subject_id: UUID,
        period_days: int = 30,
        user_id: Optional[UUID] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Génère un résumé textuel des feedbacks pour une matière
        
        Args:
            subject_id: ID de la matière
            period_days: Période d'analyse
            user_id: ID de l'utilisateur
            use_cache: Utiliser le cache si disponible
        
        Returns:
            {
                "summary": str,  # Résumé court
                "full_summary": str,  # Résumé détaillé
                "generated_at": str,
            }
        """
        app_logger.info(f"Generating feedback summary for subject {subject_id}")
        
        cache_key = f"feedback_summary_{subject_id}_{period_days}"
        if use_cache:
            cached = await self.cache_repo.get(cache_key)
            if cached:
                app_logger.info(f"Using cached summary for subject {subject_id}")
                return cached
        
        try:
            insights_data = await self.analysis_facade.generate_comprehensive_insights(
                subject_id=subject_id,
                period_days=period_days,
                user_id=user_id,
            )
        except InsufficientDataException as e:
            app_logger.warning(f"Insufficient data for summary: {e}")
            return {
                "summary": "Pas assez de données pour générer un résumé.",
                "full_summary": "Pas assez de réponses d'élèves pour cette période.",
                "generated_at": datetime.now().isoformat(),
            }
        
        summary = await self._generate_text_summary(insights_data)
        full_summary = await self._generate_full_summary(insights_data)
        
        result = {
            "summary": summary,
            "full_summary": full_summary,
            "generated_at": datetime.now().isoformat(),
        }
        
        expires_at = datetime.now() + timedelta(hours=1)
        await self.cache_repo.set(cache_key, result, expires_at)
        
        return result
    
    async def _generate_text_summary(self, insights_data: Dict[str, Any]) -> str:
        """Génère un résumé court (2-3 phrases)"""
        sentiment = insights_data.get("sentiment", {})
        themes = insights_data.get("themes", [])
        insights = insights_data.get("insights", [])
        
        prompt = f"""
            Génère un résumé court (2-3 phrases) des retours d'élèves pour cette matière.

            Sentiment global: {sentiment.get('overall_score', 0):.2f} (sur -1 à 1)
            Thèmes identifiés: {len(themes)}
            Insights: {len(insights)}

            Résumé court (2-3 phrases, en français, factuel et actionnable):
        """
        
        try:
            result = await self.langchain_service.llm.ainvoke(prompt)
            return result.content.strip()
        except Exception as e:
            app_logger.error(f"Error generating text summary: {e}")
            return "Résumé non disponible."
    
    async def _generate_full_summary(self, insights_data: Dict[str, Any]) -> str:
        """Génère un résumé détaillé"""
        sentiment = insights_data.get("sentiment", {})
        themes = insights_data.get("themes", [])
        insights = insights_data.get("insights", [])
        
        prompt = f"""
            Génère un résumé détaillé des retours d'élèves pour cette matière.

            Données:
            - Sentiment global: {sentiment.get('overall_score', 0):.2f}
            - Distribution: {sentiment.get('positive_percentage', 0):.0f}% positif, {sentiment.get('negative_percentage', 0):.0f}% négatif
            - Thèmes principaux: {', '.join([t.get('label', '') for t in themes[:3]])}
            - Insights actionnables: {len([i for i in insights if i.get('priority') in ['high', 'urgent']])}

            Résumé détaillé (paragraphe structuré, en français, factuel et actionnable):
        """
        
        try:
            result = await self.langchain_service.llm.ainvoke(prompt)
            return result.content.strip()
        except Exception as e:
            app_logger.error(f"Error generating full summary: {e}")
            return "Résumé détaillé non disponible."

