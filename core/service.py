# core/service.py
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

# Fixed imports
from shared.schemas import FeedbackRating, FeedbackCorrection, Query, Response
from core.integrations.manager import PluginManager  # Fixed: IntegrationManager -> PluginManager
from core.reasoning.engine import HybridEngine
from core.orchestrator import Orchestrator
from core.self_healing import SelfHealingController
from core.context import ContextManager
from core.visualization import KnowledgeVisualizer
from core.versioning import KnowledgeVersioner  # Now this will work
from modules.registry import ModuleRegistry
from core.performance.cost import CostMonitor
from core.performance.tracker import PerformanceTracker
from core.orchestration.load_balancer import LoadBalancer
from core.orchestration.sla_router import SLARouter

class AIService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.plugin_manager = PluginManager(config.get("plugins", {}))  # Fixed: IntegrationManager -> PluginManager
        self.reasoning = HybridEngine(self.context)
        
        # Initialize monitoring components
        self.cost_monitor = CostMonitor(config.get("cost", {}))
        self.performance_tracker = PerformanceTracker()
        self.load_balancer = LoadBalancer(self.performance_tracker)
        self.sla_router = SLARouter(self.cost_monitor, self.performance_tracker)
        
        self.app = FastAPI(
            title="AI Code Assistant",
            version="0.6.0",
            docs_url="/api-docs"
        )
        
        # Core systems
        self.registry = ModuleRegistry()
        self.context = ContextManager()
        self.healing = SelfHealingController(self.registry)
        self.visualizer = KnowledgeVisualizer(self.context.graph)
        self.versioner = KnowledgeVersioner(self.context.graph)  # Now this will work
        
        # Initialize orchestrator with all dependencies
        self.orchestrator = Orchestrator(
            validator=None,  # Will be set after initialization
            sla_router=self.sla_router,
            load_balancer=self.load_balancer,
            registry=self.registry,
            healing_controller=self.healing,
            context_manager=self.context,
            reasoning_engine=self.reasoning,
            monitoring=self.performance_tracker
        )
        
        # Initialize validator after orchestrator
        from core.validation.quality_gates import QualityValidator
        self.validator = QualityValidator(config.get("quality_standards", {}))
        self.orchestrator.validator = self.validator
        
        self._setup()
        
        from core.feedback.processor import FeedbackProcessor
        self.feedback_processor = FeedbackProcessor(self.context)
        
        # Start background tasks
        asyncio.create_task(self._update_weights_loop())
    
    async def _update_weights_loop(self):
        """Periodically update load balancer weights"""
        while True:
            await asyncio.sleep(self.config.get("load_balancing", {}).get("update_interval", 10))
            if len(self.load_balancer.history) >= self.config.get("load_balancing", {}).get("min_requests", 20):
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
                    for name, plugin in self.plugin_manager.plugins.items()  # Fixed: integration_manager -> plugin_manager
                }
            }
        
        self.app.include_router(knowledge_router)
        
        @self.app.get("/cost-monitoring")
        async def get_cost_metrics():
            return {
                "current": self.cost_monitor.current_spend,
                "forecast": self.cost_monitor.get_spend_forecast(),
                "budget": self.cost_monitor.config.get("monthly_budget", 100.0)
            }
            
        # Feedback routes
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
        
        # Versioning endpoints
        @self.app.get("/versions", tags=["Versioning"])
        async def list_versions():
            """List all knowledge graph versions"""
            return {
                "versions": [
                    {
                        "version_id": v.version_id,
                        "timestamp": v.timestamp.isoformat(),
                        "description": v.description,
                        "author": v.author,
                        "tags": v.tags
                    }
                    for v in self.versioner.list_versions()
                ]
            }
        
        @self.app.post("/versions", tags=["Versioning"])
        async def create_version(description: str, author: str = "system", tags: list = None):
            """Create a new version of the knowledge graph"""
            version_id = self.versioner.create_version(description, author, tags)
            return {"version_id": version_id, "status": "created"}
        
        @self.app.get("/versions/{version_id}", tags=["Versioning"])
        async def get_version(version_id: str):
            """Get a specific version"""
            version = self.versioner.get_version(version_id)
            if not version:
                raise HTTPException(status_code=404, detail="Version not found")
            return {
                "version_id": version.version_id,
                "timestamp": version.timestamp.isoformat(),
                "description": version.description,
                "author": version.author,
                "tags": version.tags,
                "snapshot": version.snapshot
            }
        
        @self.app.post("/versions/{version_id}/restore", tags=["Versioning"])
        async def restore_version(version_id: str):
            """Restore knowledge graph to a specific version"""
            success = self.versioner.restore_version(version_id)
            if not success:
                raise HTTPException(status_code=404, detail="Version not found")
            return {"status": "restored", "version_id": version_id}
    
    def _mount_static(self):
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        @self.app.get("/")
        async def serve_ui():
            return FileResponse("templates/index.html")
    
    async def start_service(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the service"""
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()