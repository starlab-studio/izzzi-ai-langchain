from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

@dataclass
class ResponseEmbedding:
    """Embedding for one student answer"""
    id: UUID = field(default_factory=uuid4)
    response_id: UUID = field(default=None)
    answer_id: Optional[UUID] = None
    text_content: str = ""
    embedding: List[float] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def similarity_to(self, other_embedding: List[float]) -> float:
        """Calcule la similarité cosinus"""
        import numpy as np
        a = np.array(self.embedding)
        b = np.array(other_embedding)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))