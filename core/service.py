# core/service.py
from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import uvicorn
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
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
from core.offline import OfflineManager  # Added: Offline support
from core.voice import VoiceAssistant  # Added: Voice support
# Enterprise features imports
from core.enterprise.auth import EnterpriseAuthManager
from core.enterprise.teams import TeamManager, TeamRole, Permission
from core.enterprise.audit import AuditLogger, AuditEventType

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
        
        # Initialize offline support
        self.offline_manager = OfflineManager()
        
        # Initialize voice assistant
        self.voice_assistant = VoiceAssistant()
        
        # Initialize enterprise features
        self.enterprise_auth = EnterpriseAuthManager(config.get("enterprise", {}))
        self.team_manager = TeamManager()
        self.audit_logger = AuditLogger()
        
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
        asyncio.create_task(self._cleanup_offline_cache_loop())  # Added: Offline cache cleanup
        asyncio.create_task(self._periodic_audit_flush())  # Added: Audit log flush
    
    async def _update_weights_loop(self):
        """Periodically update load balancer weights"""
        while True:
            await asyncio.sleep(self.config.get("load_balancing", {}).get("update_interval", 10))
            if len(self.load_balancer.history) >= self.config.get("load_balancing", {}).get("min_requests", 20):
                self.load_balancer.update_weights()
    
    async def _cleanup_offline_cache_loop(self):
        """Periodically clean up expired offline cache entries"""
        while True:
            await asyncio.sleep(3600)  # Run every hour
            self.orchestrator.cleanup_offline_cache()
    
    async def _periodic_audit_flush(self):
        """Periodically flush audit logs"""
        while True:
            await asyncio.sleep(300)  # Flush every 5 minutes
            await self.audit_logger.flush_buffer()
    
    async def process_query(self, query: Dict) -> Dict:
        """Enhanced processing pipeline"""
        return await self.reasoning.process(query)
    
    def _setup(self):
        """Initialize all components"""
        # Setup filesystem
        Path("static").mkdir(exist_ok=True)
        Path("templates").mkdir(exist_ok=True)
        Path("data/enterprise").mkdir(parents=True, exist_ok=True)  # Enterprise data
        
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
            # Verify JWT token
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

        @self.app.post("/enterprise/teams/{team_id}/members")
        async def invite_member(
            team_id: str,
            invitee_email: str,
            invitee_name: str,
            role: str = "member",
            authorization: Optional[str] = Header(None)
        ):
            """Invite a member to a team"""
            user_data = self._verify_enterprise_token(authorization)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            try:
                success = self.team_manager.invite_member(
                    team_id,
                    user_data["user_id"],
                    invitee_email,
                    invitee_name,
                    TeamRole(role)
                )
                
                if success:
                    await self.audit_logger.log_event(
                        AuditEventType.MEMBER_INVITED,
                        user_data["user_id"],
                        user_data["email"],
                        "invite_member",
                        f"Invited {invitee_email} to team",
                        {"team_id": team_id, "invitee_email": invitee_email, "role": role},
                        team_id=team_id
                    )
                
                return {"success": success}
            
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.delete("/enterprise/teams/{team_id}/members/{member_id}")
        async def remove_member(
            team_id: str,
            member_id: str,
            authorization: Optional[str] = Header(None)
        ):
            """Remove a member from a team"""
            user_data = self._verify_enterprise_token(authorization)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            try:
                success = self.team_manager.remove_member(team_id, user_data["user_id"], member_id)
                
                if success:
                    await self.audit_logger.log_event(
                        AuditEventType.MEMBER_REMOVED,
                        user_data["user_id"],
                        user_data["email"],
                        "remove_member",
                        f"Removed member {member_id} from team",
                        {"team_id": team_id, "removed_member_id": member_id},
                        team_id=team_id
                    )
                
                return {"success": success}
            
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

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
            
            # Check permissions
            if not self._check_enterprise_permission(user_data, team_id, Permission.VIEW_ANALYTICS):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            try:
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

        @self.app.get("/enterprise/audit/summary/{team_id}")
        async def get_team_audit_summary(
            team_id: str,
            days: int = 30,
            authorization: Optional[str] = Header(None)
        ):
            """Get audit summary for a team"""
            user_data = self._verify_enterprise_token(authorization)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Check permissions
            if not self._check_enterprise_permission(user_data, team_id, Permission.VIEW_ANALYTICS):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            try:
                summary = await self.audit_logger.get_team_audit_summary(team_id, days)
                return summary
            
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.get("/enterprise/audit/user/{user_id}/summary")
        async def get_user_audit_summary(
            user_id: str,
            days: int = 30,
            authorization: Optional[str] = Header(None)
        ):
            """Get audit summary for a user"""
            user_data = self._verify_enterprise_token(authorization)
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Users can only view their own summary unless they have admin permissions
            if user_data["user_id"] != user_id and not self._has_admin_permission(user_data):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            
            try:
                summary = await self.audit_logger.get_user_activity_summary(user_id, days)
                return summary
            
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
    
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
    
    # Enterprise helper methods
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
    
    def _check_enterprise_permission(self, user_data: Dict[str, Any], team_id: Optional[str], permission: Permission) -> bool:
        """Check if user has specific enterprise permission"""
        if not team_id:
            # For organization-level permissions, check if user has admin role
            return self._has_admin_permission(user_data)
        
        return self.team_manager.check_permission(user_data["user_id"], team_id, permission)
    
    def _has_admin_permission(self, user_data: Dict[str, Any]) -> bool:
        """Check if user has admin permissions"""
        return "admin" in user_data.get("roles", []) or "owner" in user_data.get("roles", [])