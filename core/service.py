
## Updated core/service.py (Complete)

```python
# core/service.py
from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
import asyncio
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import core components
from shared.schemas import Query, Response, FeedbackRating, FeedbackCorrection
from core.integrations.manager import PluginManager
from core.reasoning.engine import HybridEngine
from core.orchestrator import Orchestrator
from core.self_healing import SelfHealingController
from core.context import ContextManager
from core.validation.quality_gates import QualityValidator
from core.orchestration.load_balancer import LoadBalancer
from core.orchestration.sla_router import SLARouter
from core.offline import OfflineManager
from core.voice import VoiceAssistant
from core.enterprise.auth import EnterpriseAuthManager
from core.enterprise.teams import TeamManager
from core.enterprise.audit import AuditLogger, AuditEventType
from modules.registry import ModuleRegistry
from core.performance.cost import CostMonitor
from core.performance.tracker import PerformanceTracker
from core.analytics.dashboard import AnalyticsDashboard
from core.database.optimized_manager import OptimizedDatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_environment():
    """Validate required environment variables and services"""
    required_vars = ['DATABASE_URL', 'REDIS_URL', 'SECRET_KEY', 'JWT_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please copy .env.example to .env and configure your environment")
        sys.exit(1)

class AIService:
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the AI Service with all components"""
        self.config = config or {}
        
        # Validate environment first
        validate_environment()
        
        # Initialize core systems
        self.plugin_manager = PluginManager(self.config.get("plugins", {}))
        self.reasoning = HybridEngine(self.context)
        
        # Initialize monitoring components
        self.cost_monitor = CostMonitor(self.config.get("cost", {}))
        self.performance_tracker = PerformanceTracker()
        self.load_balancer = LoadBalancer(self.performance_tracker)
        self.sla_router = SLARouter(self.cost_monitor, self.performance_tracker)
        
        # Initialize support systems
        self.offline_manager = OfflineManager()
        self.voice_assistant = VoiceAssistant()
        
        # Initialize enterprise features
        self.enterprise_auth = EnterpriseAuthManager(self.config.get("enterprise", {}))
        self.team_manager = TeamManager()
        self.audit_logger = AuditLogger()
        
        # Create FastAPI application
        self.app = FastAPI(
            title="AI Code Assistant",
            version="0.1.0",
            docs_url="/api-docs",
            description="AI-powered coding assistant with multi-LLM support"
        )
        
        # Core systems
        self.registry = ModuleRegistry()
        self.context = ContextManager()
        self.healing = SelfHealingController(self.registry)
        self.visualizer = None  # Will be initialized if needed
        self.versioner = None  # Will be initialized if needed
        
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
        self.validator = QualityValidator(self.config.get("quality_standards", {}))
        self.orchestrator.validator = self.validator
        
        # Initialize additional components
        self.feedback_processor = None  # Will be initialized if needed
        self.analytics_dashboard = None  # Will be initialized if needed
        self.db_manager = None  # Will be initialized if needed
        
        # Initialize components
        self._initialize_components()
        
        # Start background tasks
        self._start_background_tasks()
        
        # Setup routes
        self._setup_routes()
        
        # Mount static files
        self._mount_static()
        
        logger.info("AI Service initialized successfully")
    
    def _initialize_components(self):
        """Initialize all service components"""
        try:
            # Initialize modules
            self.registry.discover_modules()
            for module in self.registry._instances.values():
                module.context = self.context
                module.initialize()
            
            # Initialize feedback processor
            from core.feedback.processor import FeedbackProcessor
            self.feedback_processor = FeedbackProcessor(self.context)
            
            # Initialize analytics dashboard
            self.analytics_dashboard = AnalyticsDashboard(self.db_manager, self._get_redis_client())
            
            # Initialize database manager
            db_url = os.getenv('DATABASE_URL')
            redis_url = os.getenv('REDIS_URL')
            if db_url and redis_url:
                self.db_manager = OptimizedDatabaseManager(db_url, redis_url)
                asyncio.create_task(self.db_manager.initialize())
            
            # Initialize versioning if needed
            from core.versioning import KnowledgeVersioner
            self.versioner = KnowledgeVersioner(self.context.graph)
            
            # Initialize visualizer if needed
            from core.visualization import KnowledgeVisualizer
            self.visualizer = KnowledgeVisualizer(self.context.graph)
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def _get_redis_client(self):
        """Get Redis client for caching"""
        try:
            import redis
            return redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        except ImportError:
            logger.warning("Redis not available, caching disabled")
            return None
    
    def _start_background_tasks(self):
        """Start background tasks and services"""
        try:
            # Start self-healing monitoring
            asyncio.create_task(self.healing.start_monitoring())
            
            # Start load balancer weight updates
            asyncio.create_task(self._update_weights_loop())
            
            # Start offline cache cleanup
            asyncio.create_task(self._cleanup_offline_cache_loop())
            
            # Start audit log flushing
            asyncio.create_task(self._periodic_audit_flush())
            
            logger.info("Background tasks started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
    
    async def _update_weights_loop(self):
        """Periodically update load balancer weights"""
        while True:
            try:
                await asyncio.sleep(
                    self.config.get("load_balancing", {}).get("update_interval", 10)
                )
                if len(self.load_balancer.history) >= self.config.get("load_balancing", {}).get("min_requests", 20):
                    self.load_balancer.update_weights()
            except Exception as e:
                logger.error(f"Error in weight update loop: {e}")
    
    async def _cleanup_offline_cache_loop(self):
        """Periodically clean up expired offline cache entries"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                self.orchestrator.cleanup_offline_cache()
            except Exception as e:
                logger.error(f"Error in offline cache cleanup: {e}")
    
    async def _periodic_audit_flush(self):
        """Periodically flush audit logs"""
        while True:
            try:
                await asyncio.sleep(300)  # Flush every 5 minutes
                await self.audit_logger.flush_buffer()
            except Exception as e:
                logger.error(f"Error in audit log flush: {e}")
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        @self.app.post("/process")
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
        
        @self.app.get("/health")
        async def health_check():
            """System health status"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    name: plugin.is_ready()
                    for name, plugin in self.plugin_manager.plugins.items()
                },
                "components": {
                    "orchestrator": "operational",
                    "context": "operational",
                    "validator": "operational",
                    "database": "connected" if self.db_manager else "disconnected",
                    "redis": "connected" if self._get_redis_client() else "disconnected"
                }
            }
        
        @self.app.get("/stats")
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
                    for name, module in self.registry._instances.items()
                }
            }
        
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
        
        self.app.include_router(knowledge_router)
        
        # Cost monitoring
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
            if self.feedback_processor:
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
            if self.feedback_processor:
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
            if self.versioner:
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
            return {"versions": []}
        
        @self.app.post("/versions", tags=["Versioning"])
        async def create_version(description: str, author: str = "system", tags: List[str] = None):
            """Create a new version of the knowledge graph"""
            if self.versioner:
                version_id = self.versioner.create_version(description, author, tags)
                return {"version_id": version_id, "status": "created"}
            return {"error": "Versioning not available"}
        
        @self.app.get("/versions/{version_id}", tags=["Versioning"])
        async def get_version(version_id: str):
            """Get a specific version"""
            if self.versioner:
                version = self.versioner.get_version(version_id)
                if version:
                    return {
                        "version_id": version.version_id,
                        "timestamp": version.timestamp.isoformat(),
                        "description": version.description,
                        "author": version.author,
                        "tags": version.tags,
                        "snapshot": version.snapshot
                    }
            raise HTTPException(status_code=404, detail="Version not found")
        
        @self.app.post("/versions/{version_id}/restore", tags=["Versioning"])
        async def restore_version(version_id: str):
            """Restore knowledge graph to a specific version"""
            if self.versioner:
                success = self.versioner.restore_version(version_id)
                if success:
                    return {"status": "restored", "version_id": version_id}
            raise HTTPException(status_code=404, detail="Version not found")
        
        # Offline support endpoints
        @self.app.get("/offline/stats", tags=["Offline"])
        async def get_offline_stats():
            """Get offline cache statistics"""
            return self.orchestrator.get_offline_stats()
        
        @self.app.post("/offline/cleanup", tags=["Offline"])
        async def cleanup_offline_cache():
            """Clean up expired offline cache entries"""
            self.orchestrator.cleanup_offline_cache()
            return {"status": "cache_cleaned"}
        
        # Voice command endpoints
        @self.app.post("/voice/command", tags=["Voice"])
        async def voice_command():
            """Start listening for voice commands"""
            def handle_voice_command(command: str):
                try:
                    response = asyncio.run(self.orchestrator.process_voice_command(command))
                    self.voice_assistant.speak(response.content)
                except Exception as e:
                    error_response = f"Sorry, I encountered an error: {str(e)}"
                    self.voice_assistant.speak(error_response)
            
            self.voice_assistant.listen_for_wake_word(handle_voice_command)
            return {
                "status": "listening",
                "wake_word": self.voice_assistant.wake_word,
                "message": f"Say '{self.voice_assistant.wake_word}' followed by your command"
            }
        
        @self.app.post("/voice/stop", tags=["Voice"])
        async def stop_voice_listening():
            """Stop voice command listening"""
            self.voice_assistant.stop_listening()
            return {"status": "stopped"}
        
        @self.app.post("/voice/speak", tags=["Voice"])
        async def speak_text(text: str):
            """Convert text to speech"""
            self.voice_assistant.speak(text)
            return {"status": "speaking", "text": text}
        
        @self.app.post("/voice/query", tags=["Voice"])
        async def voice_query(command: str):
            """Process a single voice command"""
            try:
                response = await self.orchestrator.process_voice_command(command)
                return {
                    "command": command,
                    "response": response.content,
                    "metadata": response.metadata
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Enterprise authentication routes
        @self.app.get("/enterprise/auth/{provider}/authorize")
        async def get_oauth_authorization(provider: str, redirect_uri: str):
            """Get OAuth authorization URL"""
            try:
                url = await self.enterprise_auth.get_oauth_authorization_url(provider, redirect_uri)
                return {"authorization_url": url}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/enterprise/auth/{provider}/callback")
        async def handle_oauth_callback(provider: str, code: str, redirect_uri: str):
            """Handle OAuth callback"""
            try:
                result = await self.enterprise_auth.handle_oauth_callback(provider, code, redirect_uri)
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/enterprise/auth/saml/authn")
        async def create_saml_auth_request():
            """Create SAML authentication request"""
            try:
                authn_request = self.enterprise_auth.create_saml_auth_request()
                return {"authn_request": authn_request}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/enterprise/auth/saml/response")
        async def handle_saml_response(saml_response: str):
            """Handle SAML response"""
            try:
                result = self.enterprise_auth.handle_saml_response(saml_response)
                return result
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/enterprise/auth/logout")
        async def enterprise_logout(session_id: str):
            """Enterprise logout"""
            success = self.enterprise_auth.logout(session_id)
            return {"success": success}
        
        # Team management routes
        @self.app.post("/enterprise/teams")
        async def create_team(
            name: str,
            description: str,
            settings: Optional[Dict[str, Any]] = None,
            authorization: Optional[str] = Header(None)
        ):
            """Create a new team"""
            user_data = self._verify_enterprise_token(authorization)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            try:
                team = self.team_manager.create_team(
                    name=name,
                    description=description,
                    owner_id=user_data["user_id"],
                    owner_email=user_data["email"],
                    owner_name=user_data["name"],
                    settings=settings
                )
                
                # Log audit event
                await self.audit_logger.log_event(
                    AuditEventType.TEAM_CREATED,
                    user_data["user_id"],
                    user_data["email"],
                    "create_team",
                    f"Created team: {name}",
                    {"team_id": team.team_id, "team_name": name},
                    team_id=team.team_id
                )
                
                return {"team_id": team.team_id, "name": team.name}
            
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/enterprise/teams")
        async def get_user_teams(authorization: Optional[str] = Header(None)):
            """Get teams for current user"""
            user_data = self._verify_enterprise_token(authorization)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            teams = self.team_manager.get_user_teams(user_data["user_id"])
            return {
                "teams": [
                    {
                        "team_id": team.team_id,
                        "name": team.name,
                        "description": team.description,
                        "role": team.members[user_data["user_id"]].role.value,
                        "member_count": len(team.members),
                        "created_at": team.created_at.isoformat()
                    }
                    for team in teams
                ]
            }
        
        # Audit routes
        @self.app.get("/enterprise/audit/events")
        async def get_audit_events(
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
            user_id: Optional[str] = None,
            team_id: Optional[str] = None,
            event_types: Optional[List[str]] = None,
            limit: int = 1000,
            authorization: Optional[str] = Header(None)
        ):
            """Get audit events"""
            user_data = self._verify_enterprise_token(authorization)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            if not self._check_enterprise_permission(user_data, team_id, "view_analytics"):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            try:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_date) if start_date else None
                end_dt = datetime.fromisoformat(end_date) if end_date else None
                
                event_types_enum = [AuditEventType(et) for et in event_types] if event_types else None
                
                events = await self.audit_logger.query_events(
                    start_date=start_dt,
                    end_date=end_dt,
                    user_id=user_id,
                    team_id=team_id,
                    event_types=event_types_enum,
                    limit=limit
                )
                
                return {
                    "events": [
                        {
                            "event_id": event.event_id,
                            "event_type": event.event_type.value,
                            "user_id": event.user_id,
                            "user_email": event.user_email,
                            "team_id": event.team_id,
                            "resource_id": event.resource_id,
                            "action": event.action,
                            "description": event.description,
                            "metadata": event.metadata,
                            "timestamp": event.timestamp.isoformat(),
                            "ip_address": event.ip_address,
                            "session_id": event.session_id
                        }
                        for event in events
                    ]
                }
            
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Analytics dashboard
        if self.analytics_dashboard:
            self.app.include_router(self.analytics_dashboard.router)
    
    def _verify_enterprise_token(self, authorization: Optional[str]) -> Optional[Dict[str, Any]]:
        """Verify enterprise JWT token"""
        if not authorization:
            return None
        
        try:
            scheme, token = authorization.split()
            if scheme.lower() != 'bearer':
                return None
            
            return self.enterprise_auth.verify_jwt_token(token)
        
        except Exception:
            return None
    
    def _check_enterprise_permission(self, user_data: Dict[str, Any], team_id: Optional[str], permission: str) -> bool:
        """Check if user has specific enterprise permission"""
        if not team_id:
            return self._has_admin_permission(user_data)
        
        return self.team_manager.check_permission(user_data["user_id"], team_id, permission)
    
    def _has_admin_permission(self, user_data: Dict[str, Any]) -> bool:
        """Check if user has admin permissions"""
        return "admin" in user_data.get("roles", []) or "owner" in user_data.get("roles", [])
    
    def _mount_static(self):
        """Mount static files and serve the main UI"""
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        @self.app.get("/")
        async def serve_ui():
            return FileResponse("static/templates/index.html")
    
    async def start_service(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the service"""
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="info",
            reload=self.config.get("debug", False)
        )
        server = uvicorn.Server(config)
        logger.info(f"Starting AI Service on {host}:{port}")
        await server.serve()

def main():
    """Main entry point for the service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Open LLM Code Assistant Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = {}
    if args.config:
        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    
    # Create and start service
    service = AIService(config)
    
    # Run the service
    uvicorn.run(
        service.app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()