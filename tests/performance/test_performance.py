# tests/performance/test_performance.py
import pytest
import asyncio
import time
import psutil
import statistics
from concurrent.futures import ThreadPoolExecutor
from core.orchestrator import Orchestrator
from shared.schemas import Query

class PerformanceTestSuite:
    def __init__(self):
        self.results = {}
    
    async def test_query_throughput(self, orchestrator, num_queries=100):
        """Test query processing throughput"""
        queries = [
            Query(content=f"How to reverse a list in Python? {i}")
            for i in range(num_queries)
        ]
        
        start_time = time.time()
        tasks = [orchestrator.route_query(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        successful_queries = sum(1 for r in results if not isinstance(r, Exception))
        throughput = successful_queries / (end_time - start_time)
        
        self.results["query_throughput"] = {
            "total_queries": num_queries,
            "successful_queries": successful_queries,
            "time_seconds": end_time - start_time,
            "queries_per_second": throughput
        }
        
        return throughput
    
    async def test_concurrent_users(self, orchestrator, num_users=50):
        """Test system performance under concurrent load"""
        async def user_session(user_id):
            queries = [
                Query(content=f"User {user_id} query {i}")
                for i in range(5)
            ]
            
            for query in queries:
                start = time.time()
                try:
                    await orchestrator.route_query(query)
                    yield time.time() - start
                except Exception:
                    yield float('inf')  # Mark failed requests
        
        start_time = time.time()
        all_latencies = []
        
        # Simulate concurrent users
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            loop = asyncio.get_event_loop()
            futures = []
            
            for user_id in range(num_users):
                future = loop.run_in_executor(
                    executor, 
                    lambda uid=user_id: list(asyncio.run(user_session(uid)))
                )
                futures.append(future)
            
            for future in futures:
                user_latencies = future.result()
                all_latencies.extend(user_latencies)
        
        end_time = time.time()
        
        # Calculate metrics
        valid_latencies = [l for l in all_latencies if l != float('inf')]
        avg_latency = statistics.mean(valid_latencies) if valid_latencies else float('inf')
        p95_latency = statistics.quantiles(valid_latencies, n=20)[18] if len(valid_latencies) > 20 else float('inf')
        
        self.results["concurrent_users"] = {
            "num_users": num_users,
            "total_time": end_time - start_time,
            "avg_latency_seconds": avg_latency,
            "p95_latency_seconds": p95_latency,
            "success_rate": len(valid_latencies) / len(all_latencies)
        }
        
        return avg_latency
    
    def test_memory_usage(self, orchestrator, duration=60):
        """Test memory usage over time"""
        process = psutil.Process()
        memory_samples = []
        
        def sample_memory():
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # MB
        
        start_time = time.time()
        while time.time() - start_time < duration:
            memory_samples.append(sample_memory())
            time.sleep(1)
        
        self.results["memory_usage"] = {
            "duration_seconds": duration,
            "samples": len(memory_samples),
            "avg_memory_mb": statistics.mean(memory_samples),
            "max_memory_mb": max(memory_samples),
            "min_memory_mb": min(memory_samples)
        }
        
        return statistics.mean(memory_samples)
    
    def get_results(self):
        """Get all performance test results"""
        return self.results

@pytest.mark.asyncio
async def test_performance_suite():
    """Run complete performance test suite"""
    # This would be integrated with your actual orchestrator
    # orchestrator = get_test_orchestrator()
    
    performance_suite = PerformanceTestSuite()
    
    # Run tests
    # await performance_suite.test_query_throughput(orchestrator)
    # await performance_suite.test_concurrent_users(orchestrator)
    # performance_suite.test_memory_usage(orchestrator)
    
    results = performance_suite.get_results()
    
    # Assert performance thresholds
    # assert results["query_throughput"]["queries_per_second"] > 10
    # assert results["concurrent_users"]["avg_latency_seconds"] < 2.0
    # assert results["memory_usage"]["max_memory_mb"] < 1024  # 1GB
    
    print("Performance test results:", results)