from typing import Generic, TypeVar, Optional, Callable, Dict
from datetime import datetime, timedelta
import hashlib
import pickle

T = TypeVar('T')


class CacheEntry(Generic[T]):
    """Single cache entry with TTL."""
    
    def __init__(self, value: T, ttl: timedelta):
        self.value = value
        self.expiry = datetime.now() + ttl
        self.hits = 0
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expiry
    
    def access(self) -> T:
        self.hits += 1
        return self.value


class SmartCache(Generic[T]):
    """
    Intelligent caching system with:
    - TTL support
    - LRU eviction
    - Size limits
    - Hit/miss statistics
    """
    
    def __init__(self, max_size: int = 100, default_ttl: timedelta = timedelta(minutes=5)):
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str, compute_fn: Optional[Callable[[], T]] = None) -> Optional[T]:
        """Get from cache or compute if missing."""
        # Check if exists and not expired
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                self._hits += 1
                return entry.access()
            else:
                # Expired, remove it
                del self._cache[key]
        
        self._misses += 1
        
        # Compute if function provided
        if compute_fn:
            value = compute_fn()
            self.set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: T, ttl: Optional[timedelta] = None) -> None:
        """Set cache entry with optional TTL."""
        # Evict if at capacity
        if len(self._cache) >= self._max_size:
            self._evict_lru()
        
        ttl = ttl or self._default_ttl
        self._cache[key] = CacheEntry(value, ttl)
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find LRU entry (least hits)
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].hits)
        del self._cache[lru_key]
        self._evictions += 1
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'size': len(self._cache),
            'hits': self._hits,
            'misses': self._misses,
            'evictions': self._evictions,
            'hit_rate': self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
        }
    
    @staticmethod
    def make_key(*args) -> str:
        """Create cache key from arguments."""
        key_data = pickle.dumps(args)
        return hashlib.md5(key_data).hexdigest()