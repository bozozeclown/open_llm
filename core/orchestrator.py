from typing import Dict, List
from shared.schemas import Query, Response
from modules.base_module import BaseModule
from core.self_healing import SelfHealingController
from core.context import ContextManager
from core.validation.quality_gates import QualityValidator
from core.orchestration.sla_router import SLARouter
from core.orchestration.load_balancer import LoadBalancer
from core.reasoning.engine import HybridEngine
from core.prediction.warmer import CacheWarmer
from core.monitoring.service import Monitoring
from core.processing.batcher import AdaptiveBatcher
import logging
import asyncio
import numpy as np

class Orchestrator:
    def __init__(
        self,
        validator: QualityValidator,
        sla_router: SLARouter,
        load_balancer: LoadBalancer,
        registry,
        healing_controller: SelfHealingController,
        context_manager: ContextManager,
        reasoning_engine: HybridEngine,
        monitoring: Monitoring
    ):
        self.validator = validator
        self.sla_router = sla_router
        self.load_balancer = load_balancer
        self.registry = registry
        self.healing = healing_controller
        self.context = context_manager
        self.reasoning = reasoning_engine
        self.monitor = monitoring
        self.logger = logging.getLogger("orchestrator")
        self.cache_warmer = CacheWarmer(self, self.context.cache_predictor)
        self.batcher = AdaptiveBatcher(
            max_batch_size=self.context.config.get("batching.max_size", 8),
            max_wait_ms=self.context.config.get("batching.max_wait_ms", 50)
        )
        self._setup_fallback_strategies()
        asyncio.create_task(self.batcher.background_flush())
        asyncio.create_task(self._update_balancer_weights())

    def _setup_fallback_strategies(self):
        self.fallback_map = {
            "python": "code_generic",
            "csharp": "code_generic",
            "math": "math_basic",
            "chat": "generic"
        }

    async def _update_balancer_weights(self):
        """Periodically update load balancer weights"""
        while True:
            await asyncio.sleep(
                self.context.config.get("load_balancing.update_interval", 10)
            )
            if len(self.load_balancer.history) >= self.context.config.get("load_balancing.min_requests", 20):
                self.load_balancer.update_weights()

    @self.monitor.track_request('orchestrator')
    async def route_query(self, query: Query) -> Response:
        """Enhanced query processing pipeline"""
        try:
            # 1. Get context and routing info
            pre_context = self.context.get_context(query.content)
            
            # Dynamic provider selection (NEW)
            if query.metadata.get("priority", 0) > 0:
                # High-priority uses SLA routing
                routing_decision = self.sla_router.select_provider({
                    "content": query.content,
                    "context": pre_context,
                    "user_priority": query.metadata.get("priority", "normal")
                })
                provider = routing_decision["provider"]
            else:
                # Normal traffic uses load balancing
                provider = self.load_balancer.select_provider({
                    "content": query.content,
                    "context": pre_context,
                    "priority": query.metadata.get("priority", 0)
                })
                routing_decision = {"provider": provider, "tier": "balanced"}
            
            query.provider = provider

            # 2. Hybrid reasoning
            reasoning_result = await self.reasoning.process({
                "query": query.content,
                "context": pre_context,
                "llm_preference": provider
            })

            # 3. Module processing with quality gates
            module = self._select_module(
                query,
                pre_context,
                reasoning_source=reasoning_result.get("source")
            )
            enriched_query = query.with_additional_context(reasoning_result)
            
            # Process with batching if enabled
            if query.metadata.get("allow_batching", True):
                batch = await self.batcher.add_query(
                    enriched_query.model_dump(),
                    priority=query.metadata.get("priority", 0)
                )
                if len(batch) > 1:
                    return await self._batch_process(batch)

            raw_response = await module.process(enriched_query)

            # 4. Validate and enhance response
            validation = self.validator.validate(raw_response)
            if not validation["passed"]:
                return await self._handle_quality_failure(enriched_query, validation)

            final_response = self._augment_response(
                validation["original_response"],
                pre_context,
                reasoning_metadata={
                    "sla_tier": routing_decision["tier"],
                    "provider": provider,
                    "reasoning_path": reasoning_result["source"]
                }
            )

            # 5. Learn and cache
            self.context.process_interaction(
                query,
                final_response,
                metadata={
                    "sla_tier": routing_decision["tier"],
                    "reasoning_source": reasoning_result["source"],
                    "provider": provider
                }
            )
            asyncio.create_task(self.cache_warmer.warm_cache(query.content))

            return final_response

        except Exception as e:
            self.logger.error(f"Routing failed: {str(e)}")
            return await self._handle_failure(query, e)

    async def _batch_process(self, batch: List[Dict]) -> Response:
        """Process batched queries through LLM"""
        try:
            # Get first provider that supports batching
            provider = next(
                p for p in {
                    query.get("provider") for query in batch
                } 
                if (plugin := self.context.plugin_manager.get_plugin(p)) 
                and plugin.supports_batching
            )
            
            llm = self.context.plugin_manager.get_plugin(provider)
            combined = [q["content"] for q in batch]
            responses = await llm.batch_complete(combined)
            
            # Return only the response for our original query
            original_query = batch[0]["content"]
            return next(
                Response(content=r) 
                for q, r in zip(combined, responses)
                if q == original_query
            )
        except Exception as e:
            self.logger.warning(f"Batch processing failed: {str(e)}")
            return await self.route_query(Query(**batch[0]))

    async def _handle_quality_failure(self, query: Query, validation: Dict) -> Response:
        """Process failed quality checks"""
        self.logger.warning(f"Quality check failed: {validation['checks']}")
        return await self._retry_with_stricter_llm(query)

    def _select_module(self, query: Query, context: dict, reasoning_source: str = None) -> BaseModule:
        """Enhanced module selection"""
        if reasoning_source == "graph":
            return self.registry.get_module("knowledge")
        
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
        
    def _augment_response(self, response: Response, context: dict, reasoning_metadata: dict = None) -> Response:
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
            },
            "processing": reasoning_metadata or {}
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

    async def _retry_with_stricter_llm(self, query: Query) -> Response:
        """Fallback strategy for quality failures"""
        query.metadata["require_quality"] = True
        return await self.route_query(query)