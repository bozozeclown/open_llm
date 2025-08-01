from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Dict, Literal, Optional
import warnings

Provider = Literal['openai', 'anthropic', 'ollama', 'huggingface']

class CostMonitor:
    def __init__(self, config: Dict):
        self.config = config
        self.cost_db = Path("data/cost_tracking.json")
        self._init_db()
        self.current_spend = 0.0
        self._load_current_period()

    def _init_db(self):
        """Initialize cost database with default structure"""
        if not self.cost_db.exists():
            with open(self.cost_db, 'w') as f:
                json.dump({
                    "monthly_budget": self.config.get("monthly_budget", 100.0),
                    "periods": [],
                    "provider_rates": {
                        "openai": {"gpt-4": 0.03, "gpt-3.5": 0.002},
                        "anthropic": {"claude-2": 0.0465, "claude-instant": 0.0163},
                        "ollama": {"llama2": 0.0, "mistral": 0.0},
                        "huggingface": {"default": 0.0}
                    }
                }, f)

    def _load_current_period(self):
        """Load or create current billing period"""
        with open(self.cost_db, 'r') as f:
            data = json.load(f)
        
        current_date = datetime.now().strftime("%Y-%m")
        if not data["periods"] or data["periods"][-1]["period"] != current_date:
            data["periods"].append({
                "period": current_date,
                "total_spend": 0.0,
                "breakdown": {p: 0.0 for p in data["provider_rates"].keys()}
            })
        
        self.current_period = data["periods"][-1]
        self.current_spend = self.current_period["total_spend"]

    def record_llm_call(
        self,
        provider: Provider,
        model: str,
        input_tokens: int,
        output_tokens: int
    ):
        """Calculate and record API call costs"""
        rate = self._get_rate(provider, model)
        cost = (input_tokens * rate["input"] + output_tokens * rate["output"]) / 1000
        
        with open(self.cost_db, 'r+') as f:
            data = json.load(f)
            current = data["periods"][-1]
            current["total_spend"] += cost
            current["breakdown"][provider] += cost
            self.current_spend = current["total_spend"]
            
            # Check budget threshold (80% warning)
            if current["total_spend"] > data["monthly_budget"] * 0.8:
                warnings.warn(
                    f"Approaching budget limit: {current['total_spend']:.2f}/{data['monthly_budget']}",
                    RuntimeWarning
                )
            
            f.seek(0)
            json.dump(data, f, indent=2)

    def _get_rate(self, provider: Provider, model: str) -> Dict[str, float]:
        """Get current token rates for a provider/model"""
        with open(self.cost_db, 'r') as f:
            rates = json.load(f)["provider_rates"]
            provider_rates = rates.get(provider, {})
            return {
                "input": provider_rates.get(model, provider_rates.get("default", 0.0)),
                "output": provider_rates.get(model, provider_rates.get("default", 0.0))
            }

    def get_spend_forecast(self) -> Dict:
        """Predict end-of-period spend"""
        now = datetime.now()
        days_in_month = (now.replace(month=now.month+1, day=1) - timedelta(days=1)).day
        days_elapsed = now.day
        daily_avg = self.current_spend / days_elapsed
        
        return {
            "current_spend": self.current_spend,
            "projected_spend": daily_avg * days_in_month,
            "budget_remaining": self.config["monthly_budget"] - self.current_spend,
            "burn_rate": daily_avg
        }