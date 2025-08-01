import hashlib
import json
from typing import Dict, Any

class QueryHasher:
    @staticmethod
    def hash_query(query: Dict[str, Any]) -> str:
        """Create consistent hash for similar queries"""
        normalized = {
            "code": query.get("code", "").strip(),
            "intent": query.get("intent", ""),
            "context": sorted(query.get("context", []))
        }
        return hashlib.sha256(
            json.dumps(normalized, sort_keys=True).encode()
        ).hexdigest()