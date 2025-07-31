from fastapi import FastAPI, APIRouter, HTTPException, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from shared.schemas import Query, Response
from modules.registry import ModuleRegistry
from core.orchestrator import Orchestrator
from core.self_healing import SelfHealingController
from core.context import ContextManager
from core.visualization import KnowledgeVisualizer
from core.versioning import KnowledgeVersioner
from core.collaboration import CollaborationServer
import uvicorn
import asyncio
from pathlib import Path

class LLMService:
    def __init__(self):
        self.app = FastAPI(
            title="LLM Code Assistant",
            version="0.5.0",
            docs_url="/api-docs"
        )
        self.registry = ModuleRegistry()
        self.context = ContextManager()
        self.healing = SelfHealingController(self.registry)
        self.orchestrator = Orchestrator(self.registry, self.healing, self.context)
        self.visualizer = KnowledgeVisualizer(self.context.graph)
        self.versioner = KnowledgeVersioner(self.context.graph)
        self.collab_server = CollaborationServer()
        
        self._setup()

    def _setup(self):
        """Initialize all components"""
        # Setup filesystem
        static_dir = Path("static")
        templates_dir = Path("templates")
        static_dir.mkdir(exist_ok=True)
        templates_dir.mkdir(exist_ok=True)
        
        # Initialize modules
        self.registry.discover_modules()
        for module in self.registry._instances.values():
            module.context = self.context
            module.initialize()
            
        # Start background services
        asyncio.create_task(self.healing.start_monitoring())
        asyncio.create_task(self.collab_server.process_annotations(self.context.graph))
        
        # Setup routes
        self._setup_routes()
        self._mount_static()

    def _setup_routes(self):
        # Main processing endpoint
        @self.app.post("/process")
        async def process(query: Query):
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
        
        @self.app.post("/debug")
        async def debug_code(query: Query):
            try:
                debug_module = self.registry.get_module("debug")
                return await debug_module.process(query)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
                
        @self.app.post("/completion")
        async def code_completion(query: Query):
            completion_module = self.registry.get_module("completion")
            return await completion_module.process(query)
            
        @self.app.post("/signature")
        async def signature_help(query: Query):
            signature_module = self.registry.get_module("signature")
            return await signature_module.process(query)
            
        @self.app.get("/health")
        async def health_check():
            return {
                "ollama": check_ollama(),
                "vllm": check_vllm(), 
                "status": "healthy" if all_services_up() else "degraded"
            }

    def _mount_static(self):
        """Serve static files and templates"""
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        @self.app.get("/")
        async def serve_ui():
            return FileResponse("templates/index.html")
            
        @self.app.get("/versioning")
        async def serve_versioning_ui():
            return FileResponse("templates/versioning.html")

    def start_service(host="0.0.0.0", port=8000):
        service = LLMService()
        uvicorn.run(service.app, host=host, port=port)