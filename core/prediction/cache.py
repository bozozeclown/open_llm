# core/prediction/cache.py
from typing import List, Dict
import numpy as np
from collections import deque

class CachePredictor:
    def __init__(self, context_manager, max_predictions=5):
        self.context = context_manager
        self.query_buffer = deque(maxlen=10)
        self.predictions = []
        
    def analyze_query_stream(self, new_query: str) -> List[str]:
        """Predict next 3 likely questions"""
        self.query_buffer.append(new_query)
        
        # 1. Get similar historical sequences
        similar_flows = self._find_similar_flows()
        
        # 2. Generate predictions (simplified example)
        return [
            "How to debug this?",
            "Better implementation?",
            "Related documentation"
        ][:max_predictions]

    def _find_similar_flows(self) -> List[Dict]:
        """Find similar query patterns in history"""
        # Implementation using your KnowledgeGraph
        return self.context.graph.find_similar_sequences(list(self.query_buffer))