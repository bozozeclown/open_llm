import time
from prometheus_client import start_http_server, Counter, Gauge, Histogram

class Monitoring:
    def __init__(self, port=9090):
        # Metrics Definitions
        self.REQUEST_COUNT = Counter(
            'llm_requests_total',
            'Total API requests',
            ['module', 'status']
        )
        
        self.LATENCY = Histogram(
            'llm_response_latency_seconds',
            'Response latency distribution',
            ['provider']
        )
        
        self.CACHE_HITS = Gauge(
            'cache_hit_ratio',
            'Current cache hit percentage'
        )
        
        start_http_server(port)

    def track_request(self, module: str):
        """Decorator to monitor request metrics"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    self.REQUEST_COUNT.labels(module, 'success').inc()
                    return result
                except Exception:
                    self.REQUEST_COUNT.labels(module, 'failed').inc()
                    raise
                finally:
                    self.LATENCY.labels(module).observe(time.time() - start)
            return wrapper
        return decorator

    def update_cache_metrics(self, hits: int, misses: int):
        """Update cache performance metrics"""
        self.CACHE_HITS.set(hits / max(hits + misses, 1))