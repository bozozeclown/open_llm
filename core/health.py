from typing import Dict
import requests

class HealthChecker:
    @staticmethod
    def check_endpoint(url: str) -> Dict[str, bool]:
        try:
            resp = requests.get(f"{url}/health", timeout=3)
            return {
                "online": resp.status_code == 200,
                "models_loaded": resp.json().get("models_loaded", 0)
            }
        except:
            return {"online": False}
            
    def check_ollama(base_url="http://localhost:11434"):
        try:
            resp = requests.get(f"{base_url}/api/tags", timeout=3)
            return {
                "status": "online",
                "models": [m['name'] for m in resp.json().get('models', [])]
            }
        except Exception as e:
            return {"status": "error", "details": str(e)}

