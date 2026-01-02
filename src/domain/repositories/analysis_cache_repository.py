from abc import ABC, abstractmethod
from typing import Optional, Any
from datetime import datetime

class IAnalysisCacheRepository(ABC):
    """Interface for analysis cache repository"""
    
    @abstractmethod
    async def get(self, cache_key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(
        self,
        cache_key: str,
        cache_value: Any,
        expires_at: datetime,
    ) -> bool:
        """Define a value in the cache"""
        pass
    
    @abstractmethod
    async def delete(self, cache_key: str) -> bool:
        """Remove a value from the cache"""
        pass
    
    @abstractmethod
    async def clear_expired(self) -> int:
        """Remove expired values from the cache"""
        pass
    
    @abstractmethod
    async def exists(self, cache_key: str) -> bool:
        """Verify if key exist in the cache"""
        pass

