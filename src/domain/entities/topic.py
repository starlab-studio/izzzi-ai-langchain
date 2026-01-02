from dataclasses import dataclass, field
from typing import List
from uuid import UUID

@dataclass
class Topic:
    """Theme identified from responses"""
    id: str
    label: str
    keywords: List[str] = field(default_factory=list)
    mentions: int = 0
    sentiment_score: float = 0.0
    example_quotes: List[str] = field(default_factory=list)
    response_ids: List[UUID] = field(default_factory=list)
    
    def add_mention(self, response_id: UUID, quote: str):
        """Add a mention"""
        self.mentions += 1
        self.response_ids.append(response_id)
        if len(self.example_quotes) < 5:
            self.example_quotes.append(quote)