from typing import Dict, Any, List
from uuid import UUID
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

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
        app_logger.info(f"Clustering responses for subject {subject_id} (n_clusters={n_clusters})")
        
        dummy_embedding = [0.0] * 1536
        
        all_results = await self.embedding_repo.find_similar(
            query_embedding=dummy_embedding,
            subject_id=subject_id,
            limit=1000,
            similarity_threshold=0.0,
        )
        
        if len(all_results) < n_clusters:
            raise InsufficientDataException(
                f"Not enough responses for clustering (need at least {n_clusters}, got {len(all_results)})",
                min_required=n_clusters,
                actual=len(all_results),
            )
        
        embeddings_list = [emb.embedding for emb, _ in all_results]
        embeddings_data = np.array(embeddings_list)
        
        scaler = StandardScaler()
        embeddings_normalized = scaler.fit_transform(embeddings_data)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings_normalized)
        
        app_logger.info(f"Clustering completed: {n_clusters} clusters identified")
        
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
            "n_clusters": n_clusters,
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

