# core/database/optimized_manager.py
import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncpg
from aioredis import Redis
from contextlib import asynccontextmanager

class OptimizedDatabaseManager:
    def __init__(self, postgres_url: str, redis_url: str):
        self.postgres_url = postgres_url
        self.redis_url = redis_url
        self.postgres_pool = None
        self.redis_client = None
        self.query_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def initialize(self):
        """Initialize database connections"""
        # Initialize PostgreSQL connection pool
        self.postgres_pool = await asyncpg.create_pool(
            self.postgres_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        
        # Initialize Redis client
        self.redis_client = Redis.from_url(self.redis_url)
    
    @asynccontextmanager
    async def get_postgres_connection(self):
        """Get a PostgreSQL connection from the pool"""
        async with self.postgres_pool.acquire() as connection:
            yield connection
    
    async def cache_query_result(self, cache_key: str, result: Any, ttl: int = None):
        """Cache query result in Redis"""
        if ttl is None:
            ttl = self.cache_ttl
        
        await self.redis_client.setex(
            f"query_cache:{cache_key}",
            ttl,
            json.dumps(result, default=str)
        )
    
    async def get_cached_query(self, cache_key: str) -> Optional[Any]:
        """Get cached query result from Redis"""
        cached = await self.redis_client.get(f"query_cache:{cache_key}")
        if cached:
            return json.loads(cached)
        return None
    
    async def store_events_batch_optimized(self, events: List[Dict], batch_size: int = 100):
        """Optimized batch storage of events"""
        if not events:
            return
        
        # Process in batches
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            await self._insert_events_batch(batch)
    
    async def _insert_events_batch(self, events: List[Dict]):
        """Insert a batch of events efficiently"""
        async with self.get_postgres_connection() as conn:
            # Use COPY for bulk insert
            await conn.executemany(
                """
                INSERT INTO events (event_id, event_type, timestamp, data)
                VALUES ($1, $2, $3, $4)
                """,
                [
                    (
                        event.get("event_id"),
                        event.get("event_type"),
                        event.get("timestamp", datetime.now()),
                        json.dumps(event.get("data", {}))
                    )
                    for event in events
                ]
            )
    
    async def get_analytics_data_optimized(self, time_range: timedelta) -> Dict[str, Any]:
        """Get analytics data with caching and optimization"""
        cache_key = f"analytics:{time_range.total_seconds()}"
        
        # Try cache first
        cached_result = await self.get_cached_query(cache_key)
        if cached_result:
            return cached_result
        
        # If not in cache, query database
        end_time = datetime.now()
        start_time = end_time - time_range
        
        async with self.get_postgres_connection() as conn:
            # Get event counts by type
            event_counts = await conn.fetch(
                """
                SELECT event_type, COUNT(*) as count
                FROM events
                WHERE timestamp BETWEEN $1 AND $2
                GROUP BY event_type
                """,
                start_time, end_time
            )
            
            # Get performance metrics
            performance_metrics = await conn.fetch(
                """
                SELECT 
                    AVG(EXTRACT(EPOCH FROM (response_timestamp - request_timestamp))) as avg_latency,
                    COUNT(*) as total_requests
                FROM requests
                WHERE request_timestamp BETWEEN $1 AND $2
                """,
                start_time, end_time
            )
        
        result = {
            "event_counts": dict(event_counts),
            "performance_metrics": dict(performance_metrics[0]) if performance_metrics else {},
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        }
        
        # Cache the result
        await self.cache_query_result(cache_key, result)
        
        return result
    
    async def create_indexes_optimized(self):
        """Create optimized database indexes"""
        async with self.get_postgres_connection() as conn:
            # Event indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON events(timestamp)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type_timestamp 
                ON events(event_type, timestamp)
            """)
            
            # Request indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_requests_timestamp 
                ON requests(request_timestamp)
            """)
            
            # User session indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_user_id 
                ON sessions(user_id)
            """)
            
            # Create partial indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_recent 
                ON events(timestamp) 
                WHERE timestamp > NOW() - INTERVAL '7 days'
            """)
    
    async def cleanup_old_data(self, retention_days: int = 30):
        """Clean up old data to maintain performance"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        async with self.get_postgres_connection() as conn:
            # Delete old events
            deleted_events = await conn.execute(
                "DELETE FROM events WHERE timestamp < $1",
                cutoff_date
            )
            
            # Delete old requests
            deleted_requests = await conn.execute(
                "DELETE FROM requests WHERE request_timestamp < $1",
                cutoff_date
            )
            
            # Optimize tables after deletion
            await conn.execute("VACUUM ANALYZE events")
            await conn.execute("VACUUM ANALYZE requests")
        
        return {
            "deleted_events": deleted_events,
            "deleted_requests": deleted_requests,
            "cutoff_date": cutoff_date.isoformat()
        }