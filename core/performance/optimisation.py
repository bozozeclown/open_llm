# core/performance/optimizations.py
import asyncio
import aioredis
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import time
from functools import wraps

class ConnectionPool:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.connections = asyncio.Queue(maxsize=max_connections)
        self.created_connections = 0
    
    async def get_connection(self):
        """Get a connection from the pool"""
        if self.connections.empty() and self.created_connections < self.max_connections:
            # Create new connection
            conn = await self._create_connection()
            self.created_connections += 1
            return conn
        
        return await self.connections.get()
    
    async def release_connection(self, conn):
        """Release a connection back to the pool"""
        await self.connections.put(conn)
    
    async def _create_connection(self):
        """Create a new connection (example for Redis)"""
        return await aioredis.create_redis_pool('redis://localhost')
    
    @asynccontextmanager
    async def get_connection_context(self):
        """Context manager for connection handling"""
        conn = await self.get_connection()
        try:
            yield conn
        finally:
            await self.release_connection(conn)

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    def track_performance(self, metric_name: str):
        """Decorator to track performance metrics"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Update metrics
                    if metric_name not in self.metrics:
                        self.metrics[metric_name] = []
                    self.metrics[metric_name].append(execution_time)
                    
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    # Track error metrics
                    error_metric = f"{metric_name}_errors"
                    if error_metric not in self.metrics:
                        self.metrics[error_metric] = []
                    self.metrics[error_metric].append(execution_time)
                    
                    raise e
            
            return wrapper
        return decorator
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        result = {}
        for metric_name, times in self.metrics.items():
            if times:
                result[metric_name] = {
                    "count": len(times),
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times)
                }
        return result

# Enhanced knowledge graph with caching
class CachedKnowledgeGraph:
    def __init__(self, base_graph, redis_pool: ConnectionPool):
        self.base_graph = base_graph
        self.redis_pool = redis_pool
        self.cache_ttl = 3600  # 1 hour
    
    async def find_semantic_matches(self, query: str, threshold: float = 0.7):
        """Cached version of semantic matching"""
        cache_key = f"semantic_match:{hash(query)}"
        
        async with self.redis_pool.get_connection_context() as conn:
            # Try to get from cache
            cached_result = await conn.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Compute result
            result = self.base_graph.find_semantic_matches(query, threshold)
            
            # Cache the result
            await conn.setex(cache_key, self.cache_ttl, json.dumps(result))
            
            return result