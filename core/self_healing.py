from dataclasses import dataclass
from enum import Enum, auto
import time
import asyncio
from typing import Dict, List, Optional
from modules.base_module import BaseModule

class HealthStatus(Enum):
    HEALTHY = auto()
    DEGRADED = auto()
    FAILED = auto()

@dataclass
class ModuleHealth:
    module_id: str
    status: HealthStatus
    last_checked: float
    failure_count: int = 0
    last_error: Optional[str] = None

class SelfHealingController:
    def __init__(self, registry):
        self.registry = registry
        self.health_status: Dict[str, ModuleHealth] = {}
        self._monitor_task = None
        
    async def start_monitoring(self, interval=60):
        """Start periodic health checks"""
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        
    async def _monitor_loop(self, interval):
        while True:
            await self.check_all_modules()
            await asyncio.sleep(interval)
            
    async def check_all_modules(self):
        """Check health of all registered modules"""
        for module_id, module in self.registry._instances.items():
            try:
                health_data = module.health_check()
                status = (
                    HealthStatus.DEGRADED if health_data.get("degraded", False) 
                    else HealthStatus.HEALTHY
                )
                self.health_status[module_id] = ModuleHealth(
                    module_id=module_id,
                    status=status,
                    last_checked=time.time()
                )
            except Exception as e:
                self._handle_module_failure(module_id, str(e))
                
    def _handle_module_failure(self, module_id: str, error: str):
        """Process module failure and initiate recovery"""
        if module_id not in self.health_status:
            self.health_status[module_id] = ModuleHealth(
                module_id=module_id,
                status=HealthStatus.FAILED,
                last_checked=time.time(),
                failure_count=1,
                last_error=error
            )
        else:
            self.health_status[module_id].failure_count += 1
            self.health_status[module_id].last_error = error
            self.health_status[module_id].status = HealthStatus.FAILED
            
        if self.health_status[module_id].failure_count > 3:
            self._attempt_recovery(module_id)
            
    def _attempt_recovery(self, module_id: str):
        """Execute recovery procedures for failed module"""
        module = self.registry._instances[module_id]
        try:
            # Attempt reinitialization
            module.initialize()
            self.health_status[module_id].status = HealthStatus.HEALTHY
            self.health_status[module_id].failure_count = 0
        except Exception as e:
            # If recovery fails, disable module temporarily
            self.health_status[module_id].status = HealthStatus.FAILED
            # TODO: Notify operators
            
    def get_available_modules(self) -> List[str]:
        """List modules currently available for routing"""
        return [
            module_id for module_id, health in self.health_status.items()
            if health.status != HealthStatus.FAILED
        ]