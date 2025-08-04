# core/interface.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from shared.schemas import Query, Response, FeedbackRating, FeedbackCorrection
from core.context import ContextManager
from core.orchestrator import Orchestrator
from core.validation.quality_gates import QualityValidator
import logging

logger = logging.getLogger(__name__)

class InterfaceManager:
    def __init__(self, orchestrator: Orchestrator, context: ContextManager, validator: QualityValidator):
        self.orchestrator = orchestrator
        self.context = context
        self.validator = validator
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        @self.router.post("/query", response_model=Response)
        async def process_query(query: Query):
            """Main query processing endpoint"""
            try:
                return await self.orchestrator.route_query(query)
            except Exception as e:
                logger.error(f"Query processing failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Processing failed: {str(e)}"
                )
        
        @self.router.get("/health")
        async def health_check():
            """System health status"""
            return {
                "status": "healthy",
                "components": {
                    "orchestrator": "operational",
                    "context": "operational",
                    "validator": "operational"
                }
            }
        
        @self.router.get("/stats")
        async def get_statistics():
            """System usage statistics"""
            return {
                "knowledge_graph": {
                    "nodes": len(self.context.graph.graph.nodes()),
                    "edges": len(self.context.graph.graph.edges()),
                    "interactions": len(self.context.interaction_log)
                },
                "modules": {
                    name: module.health_check()
                    for name, module in self.orchestrator.registry._instances.items()
                }
            }