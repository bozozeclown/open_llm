from typing import Dict, List
import numpy as np
from collections import deque
from ..performance.tracker import PerformanceTracker

class LoadBalancer:
    def __init__(self, tracker: PerformanceTracker):
        self.tracker = tracker
        self.weights = {}  # Provider -> weight
        self.history = deque(maxlen=100)  # Tracks last 100 routing decisions

    def update_weights(self):
        """Calculate new weights based on performance"""
        metrics = self.tracker.get_provider_metrics()
        total = sum(m['requests_per_second'] / (m['avg_latency'] + 1e-6) for m in metrics.values())
        
        self.weights = {
            provider: (m['requests_per_second'] / (m['avg_latency'] + 1e-6)) / total
            for provider, m in metrics.items()
        }

    def select_provider(self, query: Dict) -> str:
        """Select provider using weighted random choice"""
        providers = list(self.weights.keys())
        weights = list(self.weights.values())
        choice = np.random.choice(providers, p=weights)
        self.history.append((query['content'][:50], choice))
        return choice