from datetime import datetime
from pathlib import Path
import json
import statistics
from typing import Dict, List, Literal

SolutionSource = Literal['graph', 'rule', 'llm', 'learned_rule']

class PerformanceTracker:
    def __init__(self):
        self.metrics_path = Path("data/performance_metrics.json")
        self._init_storage()
        self.session_metrics: List[Dict] = []

    def _init_storage(self):
        self.metrics_path.parent.mkdir(exist_ok=True)
        if not self.metrics_path.exists():
            with open(self.metrics_path, 'w') as f:
                json.dump({"sessions": []}, f)

    def record_metric(
        self,
        source: SolutionSource,
        latency: float,
        success: bool,
        query_hash: str
    ):
        """Record performance metrics for each solution"""
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "latency_ms": latency * 1000,
            "success": success,
            "query_hash": query_hash[:8]  # Truncated for privacy
        }
        self.session_metrics.append(metric)

    def get_recommended_source(self, query_hash: str) -> SolutionSource:
        """Determine optimal solution source based on history"""
        history = self._load_history()
        
        # Check for identical past queries
        if query_hash:
            for m in reversed(history):
                if m['query_hash'] == query_hash:
                    if m['success']:
                        return m['source']
                    break

        # Calculate source effectiveness
        success_rates = {}
        latencies = {}
        
        for source in ['graph', 'rule', 'llm', 'learned_rule']:
            source_metrics = [m for m in history if m['source'] == source]
            if source_metrics:
                success_rates[source] = sum(
                    1 for m in source_metrics if m['success']
                ) / len(source_metrics)
                latencies[source] = statistics.median(
                    [m['latency_ms'] for m in source_metrics]
                )

        # Prioritize by success then speed
        if success_rates:
            best_source = max(
                success_rates.keys(),
                key=lambda k: (success_rates[k], -latencies[k])
            )
            return best_source
        return 'llm'  # Default fallback

    def _load_history(self) -> List[Dict]:
        """Load historical metrics"""
        with open(self.metrics_path, 'r') as f:
            data = json.load(f)
            return data['sessions'] + self.session_metrics
            
    def get_provider_metrics(self) -> Dict[str, Dict]:
        """Calculate real-time performance metrics"""
        history = self._load_history()
        window = [m for m in history if m['timestamp'] > time.time() - 60]  # Last 60s
        
        metrics = {}
        for provider in set(m['source'] for m in window):
            provider_metrics = [m for m in window if m['source'] == provider]
            metrics[provider] = {
                'requests_per_second': len(provider_metrics) / 60,
                'avg_latency': np.mean([m['latency_ms'] for m in provider_metrics]) / 1000,
                'error_rate': sum(1 for m in provider_metrics if not m['success']) / len(provider_metrics)
            }
        return metrics

    def get_available_providers(self) -> List[str]:
        """List all currently enabled providers"""
        return ["gpt-4", "gpt-3.5", "claude-2", "llama2", "local"]  # From config