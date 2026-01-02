from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta

from src.domain.repositories.embedding_repository import IEmbeddingRepository
from src.infrastructure.repositories.postgres_response_repository import (
    PostgresResponseRepository
)
from src.infrastructure.frameworks.langchain_service import LangChainService
from src.domain.entities.sentiment import SentimentAnalysis, SentimentEvidence
from src.core.logger import app_logger
from src.core.exceptions import InsufficientDataException

class AnalyzeSubjectSentimentUseCase:
    """Use case pour analyser le sentiment d'une matière"""
    
    def __init__(
        self,
        response_repo: PostgresResponseRepository,
        embedding_repo: IEmbeddingRepository,
        langchain_service: LangChainService,
    ):
        self.response_repo = response_repo
        self.embedding_repo = embedding_repo
        self.langchain_service = langchain_service
    
    async def execute(
        self,
        subject_id: UUID,
        period_days: int = 30,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Analyse le sentiment pour une matière
        
        Args:
            subject_id: ID de la matière
            period_days: Période d'analyse en jours
            user_id: ID de l'utilisateur (pour traçabilité)
        
        Returns:
            Analyse de sentiment complète
        """
        app_logger.info(f"Analyzing sentiment for subject {subject_id} over {period_days} days")
        
        # 1. Récupérer les réponses textuelles
        period_start = datetime.now() - timedelta(days=period_days)
        responses = await self.response_repo.get_text_responses_by_subject(
            subject_id=subject_id,
            period_start=period_start,
        )
        
        if len(responses) < 5:
            raise InsufficientDataException(
                "Not enough responses for sentiment analysis",
                min_required=5,
                actual=len(responses),
            )
        
        # 2. Récupérer les notations étoiles
        star_ratings = await self.response_repo.get_star_ratings_by_subject(
            subject_id=subject_id
        )
        
        # 3. Calculer le score moyen des étoiles
        star_score = self._calculate_star_score(star_ratings)
        
        # 4. Analyser le sentiment via LLM
        text_responses = [r['value_text'] for r in responses if r.get('value_text')]
        
        # Récupérer le nom de la matière (simplification, devrait venir d'un repo)
        subject_name = "Matière"  # TODO: get from subject repository
        
        llm_analysis = await self.langchain_service.analyze_sentiment(
            subject_name=subject_name,
            responses=text_responses,
        )
        
        # 5. Combiner les scores
        combined_score = self._combine_scores(
            llm_score=llm_analysis.get('overall_score', 0),
            star_score=star_score,
        )
        
        # 6. Calculer la distribution
        distribution = self._calculate_distribution(llm_analysis, star_ratings)
        
        # 7. Comparer avec période précédente (trend)
        trend = await self._calculate_trend(subject_id, period_days, combined_score)
        
        # 8. Extraire les preuves
        positive_evidence = self._extract_evidence(
            responses, 
            llm_analysis.get('positive_points', [])
        )
        negative_evidence = self._extract_evidence(
            responses,
            llm_analysis.get('negative_points', [])
        )
        
        result = {
            "subject_id": str(subject_id),
            "period_start": period_start.isoformat(),
            "period_end": datetime.now().isoformat(),
            "overall_score": combined_score,
            "confidence": llm_analysis.get('confidence', 0.7),
            "label": self._get_label(combined_score),
            "positive_percentage": distribution['positive'],
            "neutral_percentage": distribution['neutral'],
            "negative_percentage": distribution['negative'],
            "trend_percentage": trend,
            "positive_points": llm_analysis.get('positive_points', []),
            "negative_points": llm_analysis.get('negative_points', []),
            "recommendations": llm_analysis.get('recommendations', []),
            "positive_evidence": positive_evidence,
            "negative_evidence": negative_evidence,
            "total_responses": len(responses),
            "star_average": star_score,
        }
        
        app_logger.info(f"Sentiment analysis completed: score={combined_score:.2f}")
        
        return result
    
    def _calculate_star_score(self, star_ratings: list) -> float:
        """Convertit les étoiles (1-5) en score (-1 à 1)"""
        if not star_ratings:
            return 0.0
        
        total_stars = sum(r['value_stars'] * r['count'] for r in star_ratings)
        total_count = sum(r['count'] for r in star_ratings)
        
        if total_count == 0:
            return 0.0
        
        avg_stars = total_stars / total_count
        # Convertir 1-5 en -1 à 1
        return (avg_stars - 3) / 2
    
    def _combine_scores(self, llm_score: float, star_score: float) -> float:
        """Combine le score LLM et le score étoiles"""
        # Pondération : 60% LLM (plus nuancé) + 40% étoiles (plus objectif)
        if star_score == 0:
            return llm_score
        return 0.6 * llm_score + 0.4 * star_score
    
    def _calculate_distribution(self, llm_analysis: dict, star_ratings: list) -> dict:
        """Calcule la distribution positive/neutre/négative"""
        # Combiner distribution LLM et étoiles
        # Simplification : utiliser les étoiles
        if not star_ratings:
            return {
                'positive': 50.0,
                'neutral': 30.0,
                'negative': 20.0,
            }
        
        total = sum(r['count'] for r in star_ratings)
        positive = sum(r['count'] for r in star_ratings if r['value_stars'] >= 4)
        negative = sum(r['count'] for r in star_ratings if r['value_stars'] <= 2)
        neutral = total - positive - negative
        
        return {
            'positive': (positive / total * 100) if total > 0 else 0,
            'neutral': (neutral / total * 100) if total > 0 else 0,
            'negative': (negative / total * 100) if total > 0 else 0,
        }
    
    async def _calculate_trend(
        self,
        subject_id: UUID,
        period_days: int,
        current_score: float,
    ) -> Optional[float]:
        """Calcule la tendance vs période précédente"""
        # TODO: Récupérer le score de la période précédente depuis cache/DB
        # Pour l'instant, retourner None
        return None
    
    def _extract_evidence(self, responses: list, points: list) -> list:
        """Extrait des citations comme preuves"""
        evidence = []
        for point in points[:3]:  # Top 3
            # Chercher des réponses contenant les mots-clés du point
            matching = [
                r for r in responses
                if r.get('value_text') and any(
                    keyword.lower() in r['value_text'].lower()
                    for keyword in point.split()[:3]
                )
            ]
            if matching:
                evidence.append({
                    'point': point,
                    'example': matching[0]['value_text'][:200],
                    'response_id': str(matching[0]['response_id']),
                })
        return evidence
    
    def _get_label(self, score: float) -> str:
        """Convertit le score en label"""
        if score > 0.3:
            return "positive"
        elif score < -0.3:
            return "negative"
        return "neutral"