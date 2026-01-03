from typing import Dict, Any, List
from uuid import UUID
import numpy as np
import warnings
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning

from src.domain.repositories.embedding_repository import IEmbeddingRepository
from src.infrastructure.frameworks.langchain_service import LangChainService
from src.core.logger import app_logger
from src.core.exceptions import InsufficientDataException

class ClusterResponsesUseCase:
    """Use case pour regrouper les réponses par thèmes (clustering)"""
    
    def __init__(
        self,
        embedding_repo: IEmbeddingRepository,
        langchain_service: LangChainService,
    ):
        self.embedding_repo = embedding_repo
        self.langchain_service = langchain_service
    
    async def execute(
        self,
        subject_id: UUID,
        n_clusters: int = 5,
    ) -> Dict[str, Any]:
        """
        Regroupe les réponses par thèmes via clustering
        
        Args:
            subject_id: ID de la matière
            n_clusters: Nombre de clusters souhaités
        
        Returns:
            {
                "clusters": [
                    {
                        "id": str,
                        "label": str,
                        "count": int,
                        "sentiment": float,
                        "keywords": List[str],
                        "examples": List[str],
                        "response_ids": List[str],
                    }
                ]
            }
        """
        app_logger.info(f"Clustering responses for subject {subject_id} (requested n_clusters={n_clusters})")
        
        dummy_embedding = [0.0] * 1536
        
        all_results = await self.embedding_repo.find_similar(
            query_embedding=dummy_embedding,
            subject_id=subject_id,
            limit=1000,
            similarity_threshold=0.0,
        )
        
        num_responses = len(all_results)
        
        # Minimum 2 responses required for clustering
        if num_responses < 2:
            raise InsufficientDataException(
                f"Not enough responses for clustering (need at least 2, got {num_responses})",
                min_required=2,
                actual=num_responses,
            )
        
        # Dynamically adjust n_clusters based on available data
        # Heuristic: use min(n_clusters, num_responses) but ensure at least 2 clusters if we have enough data
        # For very small datasets, limit to 2 clusters max
        if num_responses < 4:
            adjusted_n_clusters = 2
        elif num_responses < n_clusters:
            # If we have fewer responses than requested clusters, use all responses as potential clusters
            # But limit to a reasonable number (e.g., num_responses - 1 or num_responses // 2)
            adjusted_n_clusters = max(2, min(n_clusters, num_responses // 2))
        else:
            adjusted_n_clusters = n_clusters
        
        # Final safety check: n_clusters cannot exceed num_responses
        adjusted_n_clusters = min(adjusted_n_clusters, num_responses)
        
        if adjusted_n_clusters != n_clusters:
            app_logger.info(
                f"Adjusted n_clusters from {n_clusters} to {adjusted_n_clusters} "
                f"(available responses: {num_responses})"
            )
        
        embeddings_list = [emb.embedding for emb, _ in all_results]
        embeddings_data = np.array(embeddings_list)
        
        scaler = StandardScaler()
        embeddings_normalized = scaler.fit_transform(embeddings_data)
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            kmeans = KMeans(n_clusters=adjusted_n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings_normalized)
        

        unique_clusters = len(set(cluster_labels))
        app_logger.info(
            f"Clustering completed: {unique_clusters} unique clusters identified "
            f"(requested: {adjusted_n_clusters}, responses: {num_responses})"
        )
        
        clusters_data = {}
        for idx, (embedding, _) in enumerate(all_results):
            cluster_id = int(cluster_labels[idx])
            if cluster_id not in clusters_data:
                clusters_data[cluster_id] = {
                    "embeddings": [],
                    "texts": [],
                    "response_ids": [],
                }
            clusters_data[cluster_id]["embeddings"].append(embedding.embedding)
            clusters_data[cluster_id]["texts"].append(embedding.text_content)
            clusters_data[cluster_id]["response_ids"].append(str(embedding.response_id))
        
        clusters = []
        for cluster_id, data in clusters_data.items():
            # Calculer le sentiment moyen du cluster (simplifié)
            # En pratique, on devrait analyser chaque texte
            sentiment = 0.0  # TODO: Calculer réellement
            
            examples_text = "\n".join([f"- {text[:100]}" for text in data["texts"][:5]])
            label = await self._generate_cluster_label(examples_text)
            
            keywords = await self._extract_keywords(data["texts"][:10])
            
            clusters.append({
                "id": f"cluster_{cluster_id}",
                "label": label,
                "count": len(data["texts"]),
                "sentiment": sentiment,
                "keywords": keywords,
                "examples": data["texts"][:3],
                "response_ids": data["response_ids"],
            })
        
        app_logger.info(f"Generated {len(clusters)} cluster labels")
        
        return {
            "clusters": clusters,
            "total_responses": len(all_results),
            "n_clusters": adjusted_n_clusters,
            "requested_n_clusters": n_clusters,
        }
    
    async def _generate_cluster_label(self, examples_text: str) -> str:
        """Génère un label pour un cluster via LLM"""
        try:
            prompt = f"""
                Analyse ces réponses d'élèves et génère un label court (2-4 mots) qui décrit le thème principal.

                Réponses:
                {examples_text}

                Label (2-4 mots uniquement, en français):
            
            """
            
            result = await self.langchain_service.llm.ainvoke(prompt)
            label = result.content.strip()
            
            label = label.replace('"', '').replace("'", "").strip()
            
            return label[:50]
            
        except Exception as e:
            app_logger.warning(f"Error generating cluster label: {e}")
            return "Thème non identifié"
    
    async def _extract_keywords(self, texts: List[str]) -> List[str]:
        """Extrait des mots-clés des textes"""
        # Simplification: on pourrait utiliser du NLP plus avancé
        # Pour l'instant, on retourne une liste vide ou on utilise le LLM
        try:
            combined_text = " ".join(texts[:5])
            prompt = f"""
                Extrais 3-5 mots-clés principaux de ces réponses d'élèves.

                Réponses: {combined_text[:500]}

                Mots-clés (séparés par des virgules, en français):
            """
            
            result = await self.langchain_service.llm.ainvoke(prompt)
            keywords_text = result.content.strip()
            
            keywords = [k.strip() for k in keywords_text.split(",")][:5]
            return keywords
            
        except Exception as e:
            app_logger.warning(f"Error extracting keywords: {e}")
            return []

