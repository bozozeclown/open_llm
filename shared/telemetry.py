# shared/telemetry.py
import psutil
from datetime import datetime

class FrameworkMetrics:
    def __init__(self):
        self.start_time = datetime.now()
        
    def collect(self):
        return {
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "memory": psutil.virtual_memory()._asdict(),
            "cpu": psutil.cpu_percent(),
            "modules": {
                mod: len(instances) 
                for mod, instances in ModuleRegistry._instances.items()
            }
        }

# Integrated into Service
class LLMService:
    def __init__(self):
        self.metrics = FrameworkMetrics()
        self.app.add_api_route("/metrics", self._get_metrics)
        
    async def _get_metrics(self):
        return self.metrics.collect()