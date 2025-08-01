# core/prediction/warmer.py
import asyncio
from concurrent.futures import ThreadPoolExecutor

class CacheWarmer:
    def __init__(self, orchestrator, cache_predictor):
        self.orchestrator = orchestrator
        self.predictor = cache_predictor
        self.executor = ThreadPoolExecutor(2)

    async def warm_cache(self, current_query: str):
        """Pre-generate responses for predicted queries"""
        predicted = self.predictor.analyze_query_stream(current_query)
        
        # Run in background thread
        await asyncio.get_event_loop().run_in_executor(
            self.executor,
            self._generate_responses,
            predicted
        )

    def _generate_responses(self, queries: List[str]):
        for query in queries:
            self.orchestrator.route_query(Query(content=query))