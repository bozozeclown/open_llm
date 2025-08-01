# core/processing/batcher.py
from typing import List, Dict
import heapq
from dataclasses import dataclass, field
from sortedcontainers import SortedList

@dataclass(order=True)
class BatchItem:
    priority: int
    query: Dict = field(compare=False)
    created_at: float = field(default_factory=time.time, compare=False)

class AdaptiveBatcher:
    def __init__(self, max_batch_size=8, max_wait_ms=50):
        self.max_batch_size = max_batch_size
        self.max_wait = max_wait_ms / 1000
        self.pending = SortedList(key=lambda x: -x.priority)
        self.semaphore = asyncio.Semaphore(0)

    async def add_query(self, query: Dict, priority: int = 0) -> List[Dict]:
        """Add query to current batch, return completed batches if ready"""
        heapq.heappush(self.pending, BatchItem(priority, query))
        
        if len(self.pending) >= self.max_batch_size:
            return self._release_batch()
        
        await asyncio.wait_for(
            self.semaphore.acquire(),
            timeout=self.max_wait
        )
        return self._release_batch()

    def _release_batch(self) -> List[Dict]:
        """Extract queries for processing"""
        batch = [item.query for item in 
                heapq.nsmallest(self.max_batch_size, self.pending)]
        del self.pending[:len(batch)]
        return batch

    async def background_flush(self):
        """Periodically flush partial batches"""
        while True:
            await asyncio.sleep(self.max_wait)
            if self.pending:
                self.semaphore.release()