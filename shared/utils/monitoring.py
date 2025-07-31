from prometheus_client import Counter, Histogram
from time import perf_counter

REQUEST_COUNT = Counter(
    'request_count', 
    'App Request Count',
    ['module', 'status']
)

REQUEST_LATENCY = Histogram(
    'request_latency_seconds',
    'Request latency',
    ['module']
)

class Monitor:
    @staticmethod
    def track_request(module: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    REQUEST_COUNT.labels(module, "success").inc()
                    return result
                except Exception:
                    REQUEST_COUNT.labels(module, "error").inc()
                    raise
                finally:
                    REQUEST_LATENCY.labels(module).observe(perf_counter() - start_time)
            return wrapper
        return decorator