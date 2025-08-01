from typing import Dict, Literal
from dataclasses import dataclass
from ..performance.cost import CostMonitor
from ..performance.tracker import PerformanceTracker
import numpy as np

@dataclass
class SLATier:
    name: str
    min_accuracy: float
    max_latency: float  # seconds
    allowed_providers: list
    cost_multiplier: float = 1.0

class SLARouter:
    def __init__(self, cost_monitor: CostMonitor, perf_tracker: PerformanceTracker):
        self.cost = cost_monitor
        self.performance = perf_tracker
        
        # Define service tiers
        self.tiers = {
            "critical": SLATier(
                name="critical",
                min_accuracy=0.95,
                max_latency=1.5,
                allowed_providers=["gpt-4", "claude-2", "vllm"],
                cost_multiplier=2.0
            ),
            "standard": SLATier(
                name="standard",
                min_accuracy=0.85,
                max_latency=3.0,
                allowed_providers=["gpt-3.5", "claude-instant", "llama2"]
            ),
            "economy": SLATier(
                name="economy",
                min_accuracy=0.70,
                max_latency=5.0,
                allowed_providers=["llama2", "local"]
            )
        }

    def select_provider(self, query: Dict) -> Dict[str, str]:
        """Select optimal provider based on SLA and budget"""
        # Determine SLA tier
        tier = self._determine_tier(query)
        
        # Get eligible providers
        candidates = [
            p for p in self.performance.get_available_providers()
            if p in tier.allowed_providers
        ]
        
        # Rank by performance/cost tradeoff
        ranked = sorted(
            candidates,
            key=lambda p: self._score_provider(p, tier)
        )
        
        return {
            "provider": ranked[0],
            "tier": tier.name,
            "reason": f"Best match for {tier.name} SLA"
        }

    def _determine_tier(self, query: Dict) -> SLATier:
        """Auto-select SLA tier based on query properties"""
        if query.get("user_priority") == "high":
            return self.tiers["critical"]
        
        # Auto-detect critical queries
        if ("error" in query.get("intent", "") or 
            "production" in query.get("context", "")):
            return self.tiers["critical"]
            
        # Budget-aware fallback
        budget_status = self.cost.get_spend_forecast()
        if budget_status["burn_rate"] > budget_status["budget_remaining"] / 10:
            return self.tiers["economy"]
            
        return self.tiers["standard"]

    def _score_provider(self, provider: str, tier: SLATier) -> float:
        """Score providers (0-1) based on SLA fit"""
        metrics = self.performance.get_provider_metrics(provider)
        
        # Normalized performance score (higher better)
        accuracy_score = metrics["accuracy"] / tier.min_accuracy
        latency_score = tier.max_latency / max(metrics["latency"], 0.1)
        
        # Cost penalty (lower better)
        cost_rate = self.cost._get_rate(provider.split('-')[0], provider)
        cost_penalty = cost_rate["input"] * tier.cost_multiplier
        
        return np.mean([accuracy_score, latency_score]) / cost_penalty