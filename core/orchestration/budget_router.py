from typing import Dict, Literal
from ..performance.cost import CostMonitor

class BudgetRouter:
    def __init__(self, cost_monitor: CostMonitor):
        self.cost = cost_monitor

    def select_llm(self, query: Dict) -> Literal['premium', 'standard', 'local']:
        """Choose LLM tier based on budget and query criticality"""
        forecast = self.cost.get_spend_forecast()
        criticality = query.get("criticality", 0.5)
        
        if forecast["burn_rate"] > forecast["budget_remaining"] / 7:  # Weekly burn
            return 'local'
        elif criticality > 0.8 and forecast["budget_remaining"] > 50:
            return 'premium'
        else:
            return 'standard'