from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from src.application.use_cases.analyze_subject_sentiment import AnalyzeSubjectSentimentUseCase
from src.application.use_cases.semantic_search import SemanticSearchUseCase
from src.application.use_cases.cluster_responses import ClusterResponsesUseCase
from src.application.use_cases.chatbot_query import ChatbotQueryUseCase
from src.infrastructure.repositories.postgres_response_repository import (
    PostgresResponseRepository
)
from src.core.logger import app_logger
from src.core.exceptions import NotFoundException, InsufficientDataException

class AnalysisFacade:
    """
    Facade qui orchestre les analyses complexes
    Simplifie l'interface pour l'API layer
    """
    
    def __init__(
        self,
        analyze_sentiment_uc: AnalyzeSubjectSentimentUseCase,
        semantic_search_uc: SemanticSearchUseCase,
        cluster_responses_uc: ClusterResponsesUseCase,
        chatbot_query_uc: ChatbotQueryUseCase,
        response_repo: PostgresResponseRepository,
    ):
        self.analyze_sentiment_uc = analyze_sentiment_uc
        self.semantic_search_uc = semantic_search_uc
        self.cluster_responses_uc = cluster_responses_uc
        self.chatbot_query_uc = chatbot_query_uc
        self.response_repo = response_repo
    
    async def analyze_subject_sentiment(
        self,
        subject_id: UUID,
        period_days: int = 30,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Analyse complète du sentiment pour une matière
        
        Workflow :
        1. Analyse de sentiment
        2. Si données suffisantes, clustering pour identifier thèmes
        3. Cache le résultat
        """
        app_logger.info(f"Facade: Analyzing sentiment for subject {subject_id}")
        
        try:
            # 1. Analyse de sentiment
            sentiment = await self.analyze_sentiment_uc.execute(
                subject_id=subject_id,
                period_days=period_days,
                user_id=user_id,
            )
            
            # 2. Essayer d'identifier les thèmes (si assez de données)
            try:
                themes = await self.cluster_responses_uc.execute(
                    subject_id=subject_id,
                    n_clusters=5,
                )
                sentiment['themes'] = themes.get('clusters', [])
            except InsufficientDataException:
                app_logger.info("Not enough data for theme clustering")
                sentiment['themes'] = []
            
            return sentiment
            
        except Exception as e:
            app_logger.error(f"Error in sentiment analysis: {e}")
            raise
    
    async def generate_comprehensive_insights(
        self,
        subject_id: UUID,
        period_days: int = 30,
        user_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """
        Génère des insights complets combinant plusieurs analyses
        
        Workflow :
        1. Sentiment analysis
        2. Topic clustering
        3. Génération d'insights actionnables via LLM
        4. Recommandations prioritaires
        """
        app_logger.info(f"Facade: Generating comprehensive insights for subject {subject_id}")
        
        # 1. Analyse de sentiment
        sentiment = await self.analyze_sentiment_uc.execute(
            subject_id=subject_id,
            period_days=period_days,
            user_id=user_id,
        )
        
        # 2. Clustering des thèmes
        try:
            themes = await self.cluster_responses_uc.execute(
                subject_id=subject_id,
                n_clusters=5,
            )
        except InsufficientDataException:
            themes = {'clusters': []}
        
        # 3. Générer des insights via LLM
        # TODO: Créer GenerateInsightsUseCase qui utilise LangChainService
        insights = await self._generate_insights_from_data(
            sentiment=sentiment,
            themes=themes,
            subject_id=subject_id,
        )
        
        return {
            'subject_id': str(subject_id),
            'period_days': period_days,
            'sentiment': sentiment,
            'themes': themes.get('clusters', []),
            'insights': insights,
            'generated_at': datetime.now().isoformat(),
        }
    
    async def semantic_search(
        self,
        query: str,
        subject_id: UUID,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Recherche sémantique simple"""
        return await self.semantic_search_uc.execute(
            query=query,
            subject_id=subject_id,
            limit=limit,
        )
    
    async def chatbot_conversation(
        self,
        query: str,
        subject_id: UUID,
        user_id: UUID,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Conversation avec le chatbot intelligent
        L'agent décide automatiquement quels outils utiliser
        """
        return await self.chatbot_query_uc.execute(
            query=query,
            subject_id=subject_id,
            user_id=user_id,
            context=context,
        )
    
    async def compare_subjects(
        self,
        subject_ids: List[UUID],
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Compare plusieurs matières
        
        Returns:
            {
                "comparison": {
                    "subject_a": {...},
                    "subject_b": {...},
                },
                "winner": "subject_a",
                "key_differences": [...],
            }
        """
        app_logger.info(f"Facade: Comparing {len(subject_ids)} subjects")
        
        if len(subject_ids) < 2:
            raise ValueError("Need at least 2 subjects to compare")
        
        # Analyser chaque matière
        analyses = {}
        for subject_id in subject_ids:
            try:
                analysis = await self.analyze_sentiment_uc.execute(
                    subject_id=subject_id,
                    period_days=period_days,
                )
                analyses[str(subject_id)] = analysis
            except InsufficientDataException:
                app_logger.warning(f"Insufficient data for subject {subject_id}")
                continue
        
        if len(analyses) < 2:
            raise InsufficientDataException(
                "Not enough subjects with sufficient data",
                min_required=2,
                actual=len(analyses),
            )
        
        # Déterminer le "gagnant"
        winner_id = max(analyses.keys(), key=lambda k: analyses[k]['overall_score'])
        
        # Identifier les différences clés
        key_differences = self._extract_key_differences(analyses)
        
        return {
            'subjects_compared': len(analyses),
            'comparison': analyses,
            'winner': winner_id,
            'key_differences': key_differences,
        }
    
    async def predict_risks(
        self,
        subject_id: UUID,
        lookback_days: int = 90,
    ) -> Dict[str, Any]:
        """
        Analyse prédictive : détecte les signaux faibles
        
        Returns:
            {
                "risk_score": 0.35,  // 0-1
                "risk_level": "medium",
                "factors": [...],
                "recommendations": [...],
            }
        """
        app_logger.info(f"Facade: Predicting risks for subject {subject_id}")
        
        # 1. Analyser les 3 derniers mois par périodes de 30 jours
        periods = [30, 60, 90]
        historical_data = []
        
        for days in periods:
            try:
                analysis = await self.analyze_sentiment_uc.execute(
                    subject_id=subject_id,
                    period_days=30,  # Toujours 30j mais décalé
                )
                historical_data.append({
                    'period': f"Last {days} days",
                    'score': analysis['overall_score'],
                    'response_count': analysis['total_responses'],
                })
            except InsufficientDataException:
                continue
        
        if len(historical_data) < 2:
            raise InsufficientDataException(
                "Not enough historical data for prediction",
                min_required=2,
                actual=len(historical_data),
            )
        
        # 2. Calculer les tendances
        scores = [d['score'] for d in historical_data]
        trend = self._calculate_trend_slope(scores)
        
        # 3. Calculer le risk score
        risk_factors = []
        risk_score = 0.0
        
        # Facteur 1: Tendance négative
        if trend < -0.1:
            risk_score += 0.3
            risk_factors.append(f"Tendance à la baisse ({trend:.2f})")
        
        # Facteur 2: Score absolu bas
        current_score = scores[-1]
        if current_score < -0.2:
            risk_score += 0.3
            risk_factors.append(f"Score actuel bas ({current_score:.2f})")
        
        # Facteur 3: Baisse du nombre de réponses
        response_counts = [d['response_count'] for d in historical_data]
        if len(response_counts) >= 2 and response_counts[-1] < response_counts[-2] * 0.7:
            risk_score += 0.2
            risk_factors.append("Baisse du taux de réponse (-30%)")
        
        # Facteur 4: Volatilité
        if len(scores) >= 3:
            volatility = self._calculate_volatility(scores)
            if volatility > 0.3:
                risk_score += 0.2
                risk_factors.append(f"Forte volatilité ({volatility:.2f})")
        
        risk_score = min(risk_score, 1.0)
        
        # 4. Niveau de risque
        if risk_score >= 0.7:
            risk_level = "critical"
        elif risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # 5. Recommandations
        recommendations = self._generate_risk_recommendations(risk_factors, risk_level)
        
        return {
            'subject_id': str(subject_id),
            'risk_score': risk_score,
            'risk_level': risk_level,
            'confidence': 0.75,
            'factors': risk_factors,
            'recommendations': recommendations,
            'historical_data': historical_data,
            'trend': trend,
        }
    
    # === Private helpers ===
    
    async def _generate_insights_from_data(
        self,
        sentiment: Dict[str, Any],
        themes: Dict[str, Any],
        subject_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Génère des insights actionnables"""
        insights = []
        
        # Insight 1: Sentiment global
        if sentiment['overall_score'] > 0.5:
            insights.append({
                'type': 'positive',
                'priority': 'low',
                'title': 'Excellent sentiment général',
                'content': f"Les élèves sont très satisfaits (score: {sentiment['overall_score']:.2f})",
                'evidence': sentiment.get('positive_evidence', []),
            })
        elif sentiment['overall_score'] < -0.3:
            insights.append({
                'type': 'alert',
                'priority': 'high',
                'title': 'Sentiment négatif détecté',
                'content': f"Attention : le sentiment est négatif (score: {sentiment['overall_score']:.2f})",
                'evidence': sentiment.get('negative_evidence', []),
            })
        
        # Insight 2: Tendance
        if sentiment.get('trend_percentage'):
            if sentiment['trend_percentage'] < -15:
                insights.append({
                    'type': 'alert',
                    'priority': 'urgent',
                    'title': 'Baisse significative du sentiment',
                    'content': f"Le sentiment a baissé de {abs(sentiment['trend_percentage']):.0f}% vs période précédente",
                    'evidence': [],
                })
        
        # Insight 3: Thèmes négatifs
        negative_themes = [
            t for t in themes.get('clusters', [])
            if t.get('sentiment', 0) < -0.3
        ]
        
        for theme in negative_themes[:2]:  # Top 2 thèmes négatifs
            insights.append({
                'type': 'negative',
                'priority': 'high',
                'title': f"Problème identifié : {theme['label']}",
                'content': f"{theme['count']} élèves mentionnent des problèmes liés à {theme['label']}",
                'evidence': [{'text': ex} for ex in theme.get('examples', [])[:3]],
            })
        
        # Insight 4: Recommandations
        for rec in sentiment.get('recommendations', [])[:3]:
            insights.append({
                'type': 'recommendation',
                'priority': 'medium',
                'title': 'Recommandation',
                'content': rec,
                'evidence': [],
            })
        
        return insights
    
    def _extract_key_differences(self, analyses: Dict[str, Any]) -> List[str]:
        """Identifie les différences clés entre analyses"""
        differences = []
        
        # Comparer les scores
        scores = {k: v['overall_score'] for k, v in analyses.items()}
        max_score = max(scores.values())
        min_score = min(scores.values())
        
        if max_score - min_score > 0.3:
            differences.append(f"Écart de sentiment significatif : {max_score - min_score:.2f}")
        
        # Comparer les thèmes
        # TODO: Analyser les thèmes récurrents vs uniques
        
        return differences
    
    def _calculate_trend_slope(self, scores: List[float]) -> float:
        """Calcule la pente de la tendance"""
        import numpy as np
        
        if len(scores) < 2:
            return 0.0
        
        x = np.arange(len(scores))
        y = np.array(scores)
        
        # Régression linéaire simple
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        
        return float(slope)
    
    def _calculate_volatility(self, scores: List[float]) -> float:
        """Calcule la volatilité (écart-type)"""
        import numpy as np
        return float(np.std(scores))
    
    def _generate_risk_recommendations(
        self,
        risk_factors: List[str],
        risk_level: str,
    ) -> List[str]:
        """Génère des recommandations basées sur les facteurs de risque"""
        recommendations = []
        
        if risk_level in ['critical', 'high']:
            recommendations.append("Organiser une session de feedback avec les élèves sous 48h")
            recommendations.append("Analyser les thèmes négatifs en détail")
        
        if "Tendance à la baisse" in str(risk_factors):
            recommendations.append("Revoir le contenu et la pédagogie du cours")
        
        if "taux de réponse" in str(risk_factors):
            recommendations.append("Relancer l'engagement des élèves (rappels, incentives)")
        
        if not recommendations:
            recommendations.append("Continuer le monitoring régulier")
        
        return recommendations