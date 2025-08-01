from fastapi import FastAPI, APIRouter, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
import asyncio
from typing import Dict, Any
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from shared.schemas import FeedbackRating, FeedbackCorrection  # Your new schemas

# Core imports
from core.integrations.manager import IntegrationManager
from core.reasoning.engine import HybridEngine
from core.orchestrator import Orchestrator
from core.self_healing import SelfHealingController
from core.context import ContextManager
from core.visualization import KnowledgeVisualizer
from core.versioning import KnowledgeVersioner

# Module system
from modules.registry import ModuleRegistry
from shared.schemas import Query

class AIService:
    def __init__(self, config: Dict[str, Any]):
        self.load_balancer = LoadBalancer(self.monitor)
        asyncio.create_task(self._update_weights_loop())
        self.config = config
        self.integration_manager = IntegrationManager(config.get("plugins", {}))
        self.reasoning = HybridEngine(self.context)
        
        self.app = FastAPI(
            title="AI Code Assistant",
            version="0.6.0",  # Bumped version
            docs_url="/api-docs"
        )
        
        # Core systems
        self.registry = ModuleRegistry()
        self.context = ContextManager()
        self.healing = SelfHealingController(self.registry)
        self.orchestrator = Orchestrator(
            registry=self.registry,
            healing=self.healing,
            context=self.context,
            reasoning=self.reasoning  # New dependency
        )
        self.visualizer = KnowledgeVisualizer(self.context.graph)
        self.versioner = KnowledgeVersioner(self.context.graph)
        
        self._setup()
        
        from core.feedback.processor import FeedbackProcessor  # Lazy import
        self.feedback_processor = FeedbackProcessor(self.context)
        
    async def _update_weights_loop(self):
        while True:
            await asyncio.sleep(self.config["load_balancing"]["update_interval"])
            self.load_balancer.update_weights()
    
    async def process_query(self, query: Dict) -> Dict:
        """Enhanced processing pipeline"""
        return await self.reasoning.process(query)

    def _setup(self):
        """Initialize all components"""
        # Setup filesystem
        Path("static").mkdir(exist_ok=True)
        Path("templates").mkdir(exist_ok=True)
        
        # Initialize modules
        self.registry.discover_modules()
        for module in self.registry._instances.values():
            module.context = self.context
            module.initialize()
            
        # Start background services
        asyncio.create_task(self.healing.start_monitoring())
        
        # Setup routes
        self._setup_routes()
        self._mount_static()

    def _setup_routes(self):
        @self.app.post("/process")
        async def process(query: Query):
            """Main processing endpoint with hybrid reasoning"""
            try:
                return await self.orchestrator.route_query(query)
            except Exception as e:
                raise HTTPException(status_code=503, detail=str(e))
                
        # Knowledge endpoints
        knowledge_router = APIRouter(prefix="/knowledge")
        
        @knowledge_router.get("")
        async def get_knowledge(concept: str = None):
            if concept:
                return self.context.graph.find_semantic_matches(concept)
            return {
                "stats": {
                    "nodes": len(self.context.graph.graph.nodes()),
                    "edges": len(self.context.graph.graph.edges()),
                    "interactions": len(self.context.interaction_log)
                }
            }
        
        # Specialized endpoints
        @self.app.post("/debug")
        async def debug_code(query: Query):
            try:
                return await self.registry.get_module("debug").process(query)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.get("/health")
        async def health_check():
            """Simplified health check"""
            return {
                "status": "healthy",
                "services": {
                    name: plugin.is_ready()
                    for name, plugin in self.integration_manager.plugins.items()
                }
            }

        self.app.include_router(knowledge_router)
        
        @self.app.get("/cost-monitoring")
        async def get_cost_metrics():
            return {
                "current": service.cost_monitor.current_spend,
                "forecast": service.cost_monitor.get_spend_forecast(),
                "budget": service.cost_monitor.config["monthly_budget"]
            }
            
        # ===== ADD FEEDBACK ROUTES HERE =====
        @self.app.post("/feedback/rate", tags=["Feedback"])
        async def record_rating(feedback: FeedbackRating):
            """Record explicit user ratings (1-5 stars)"""
            self.feedback_processor.process_feedback({
                'type': 'positive' if feedback.rating >= 3 else 'negative',
                'rating': feedback.rating / 5,  # Normalize to 0-1
                'query_node': feedback.query_hash,
                'response_node': feedback.response_hash,
                'user_comment': feedback.comment,
                'timestamp': datetime.utcnow().isoformat()
            })
            return {"status": "rating_recorded"}

        @self.app.post("/feedback/correct", tags=["Feedback"])
        async def record_correction(feedback: FeedbackCorrection):
            """Handle factual corrections from users"""
            self.feedback_processor.process_feedback({
                'type': 'correction',
                'target_node': feedback.node_id,
                'corrected_info': feedback.corrected_content,
                'severity': feedback.severity,
                'timestamp': datetime.utcnow().isoformat()
            })
            return {"status": "correction_applied"}

    def _mount_static(self):
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        @self.app.get("/")
        async def serve_ui():
            return FileResponse("templates/index.html")

    async def start_service(self, host: str = "0.0.0.0", port: int = 8000):
        """Corrected instance method"""
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()