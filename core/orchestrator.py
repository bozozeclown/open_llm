from typing import Dict, List
from shared.schemas import Query, Response
from modules.base_module import BaseModule
from core.self_healing import SelfHealingController
from core.context import ContextManager
import logging

class Orchestrator:
    def __init__(self, registry, healing_controller, context_manager):
        self.registry = registry
        self.healing = healing_controller
        self.context = context_manager
        self.logger = logging.getLogger("orchestrator")
        self._setup_fallback_strategies()
        
    def _setup_fallback_strategies(self):
        self.fallback_map = {
            "python": "code_generic",
            "csharp": "code_generic",
            "math": "math_basic",
            "chat": "generic"
        }
        
    async def route_query(self, query: Query) -> Response:
        """Process query with knowledge-enhanced routing"""
        try:
            # Get context before processing
            pre_context = self.context.get_context(query.content)
            
            # Route to appropriate module
            module = self._select_module(query, pre_context)
            response = await module.process(query)
            
            # Learn from interaction
            self.context.process_interaction(query, response)
            
            # Enhance response with context
            return self._augment_response(response, pre_context)
            
        except Exception as e:
            self.logger.error(f"Routing failed: {str(e)}")
            return await self._handle_failure(query, e)
            
    def _select_module(self, query: Query, context: dict) -> BaseModule:
        """Select module using context-aware routing"""
        # Use knowledge matches to influence routing
        if any(match["type"] == "code" for match in context["matches"]):
            lang = self._detect_language(context["matches"])
            return self.registry.get_module(f"code_{lang}")
            
        return self.registry.get_module("chat")
        
    def _detect_language(self, matches: List[dict]) -> str:
        """Detect programming language from knowledge matches"""
        lang_keywords = {
            "python": ["def", "import", "lambda"],
            "csharp": ["var", "using", "namespace"]
        }
        
        for match in matches:
            content = match.get("content", "").lower()
            for lang, keywords in lang_keywords.items():
                if any(kw in content for kw in keywords):
                    return lang
        return "generic"
        
    def _augment_response(self, response: Response, context: dict) -> Response:
        """Enhance response with contextual knowledge"""
        if not response.metadata:
            response.metadata = {}
            
        response.metadata.update({
            "context": {
                "matched_concepts": [
                    {"id": m["node_id"], "content": m["content"]}
                    for m in context["matches"][:3]
                ],
                "related_concepts": [
                    {"id": n["id"], "content": n["content"]}
                    for n in context["related"][:5]
                ]
            }
        })
        return response
        
    async def _handle_failure(self, query: Query, error: Exception) -> Response:
        """Handle routing failures with fallback logic"""
        module_id = query.content_type.split("_")[-1]
        fallback_id = self.fallback_map.get(module_id, "generic")
        
        if fallback := self.registry.get_module(fallback_id):
            response = await fallback.process(query)
            self.context.process_interaction(query, response)
            return response
            
        raise RuntimeError("All fallback strategies failed")