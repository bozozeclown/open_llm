import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from saml2 import entity, client
from saml2.config import Config as SamlConfig
import asyncio
import aiohttp

class EnterpriseAuthManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.jwt_secret = config.get("jwt_secret", secrets.token_urlsafe(32))
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = timedelta(hours=config.get("jwt_expiration_hours", 24))
        
        # Initialize OAuth providers
        self.oauth_providers = {}
        self._setup_oauth_providers()
        
        # Initialize SAML provider
        self.saml_configured = self._setup_saml_provider()
        
        # Session storage
        self.sessions = {}
        self.user_sessions = {}  # user_id -> session_ids
        
    def _setup_oauth_providers(self):
        """Setup OAuth2 providers (Google, Microsoft, GitHub)"""
        oauth_config = self.config.get("oauth", {})
        
        for provider_name, provider_config in oauth_config.items():
            if provider_config.get("enabled", False):
                oauth = OAuth(
                    config=Config(environ={
                        f"{provider_name.upper()}_CLIENT_ID": provider_config["client_id"],
                        f"{provider_name.upper()}_CLIENT_SECRET": provider_config["client_secret"],
                    })
                )
                
                self.oauth_providers[provider_name] = {
                    "client": oauth,
                    "config": provider_config,
                    "scopes": provider_config.get("scopes", ["openid", "email", "profile"])
                }
    
    def _setup_saml_provider(self) -> bool:
        """Setup SAML provider for enterprise SSO"""
        saml_config = self.config.get("saml", {})
        
        if not saml_config.get("enabled", False):
            return False
        
        try:
            sp_config = {
                "entityid": saml_config["sp_entity_id"],
                "description": "Open LLM Code Assistant",
                "service": {
                    "sp": {
                        "endpoints": {
                            "assertion_consumer_service": [
                                (saml_config["acs_url"], "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"),
                            ],
                        },
                        "allow_unsolicited": True,
                        "authn_requests_signed": False,
                        "logout_requests_signed": True,
                        "want_assertions_signed": True,
                        "want_response_signed": False,
                    },
                },
                "metadata": {
                    "local": [saml_config["idp_metadata_url"]],
                },
                "key_file": saml_config.get("sp_key_file"),
                "cert_file": saml_config.get("sp_cert_file"),
                "xmlsec_binary": saml_config.get("xmlsec_binary", "/usr/bin/xmlsec1"),
                "debug": saml_config.get("debug", False),
            }
            
            self.saml_config = SamlConfig().load(sp_config)
            self.saml_client = client.Saml2Client(config=self.saml_config)
            return True
            
        except Exception as e:
            print(f"Failed to setup SAML provider: {e}")
            return False
    
    def create_jwt_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT token for authenticated user"""
        payload = {
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "roles": user_data.get("roles", []),
            "organization": user_data.get("organization"),
            "permissions": user_data.get("permissions", []),
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + self.jwt_expiration
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    async def get_oauth_authorization_url(self, provider: str, redirect_uri: str) -> str:
        """Get OAuth authorization URL"""
        if provider not in self.oauth_providers:
            raise HTTPException(status_code=400, detail=f"Provider {provider} not configured")
        
        oauth_client = self.oauth_providers[provider]["client"]
        return await oauth_client.authorize_redirect(redirect_uri)
    
    async def handle_oauth_callback(self, provider: str, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle OAuth callback and return user data"""
        if provider not in self.oauth_providers:
            raise HTTPException(status_code=400, detail=f"Provider {provider} not configured")
        
        oauth_client = self.oauth_providers[provider]["client"]
        token = await oauth_client.authorize_access_token(redirect_uri, code)
        
        # Get user info
        async with aiohttp.ClientSession() as session:
            user_info_url = self.oauth_providers[provider]["config"]["user_info_url"]
            headers = {"Authorization": f"Bearer {token['access_token']}"}
            
            async with session.get(user_info_url, headers=headers) as response:
                user_data = await response.json()
        
        # Map provider-specific user data to standard format
        mapped_user_data = self._map_oauth_user_data(provider, user_data)
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        jwt_token = self.create_jwt_token(mapped_user_data)
        
        session_data = {
            "session_id": session_id,
            "jwt_token": jwt_token,
            "user_data": mapped_user_data,
            "provider": provider,
            "created_at": datetime.utcnow(),
            "last_accessed": datetime.utcnow()
        }
        
        self.sessions[session_id] = session_data
        
        # Update user sessions
        user_id = mapped_user_data["user_id"]
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session_id)
        
        return {
            "session_id": session_id,
            "jwt_token": jwt_token,
            "user": mapped_user_data
        }
    
    def _map_oauth_user_data(self, provider: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map OAuth provider user data to standard format"""
        mappings = {
            "google": {
                "user_id": user_data["sub"],
                "email": user_data["email"],
                "name": user_data["name"],
                "picture": user_data.get("picture"),
                "roles": ["user"],  # Default role
                "organization": user_data.get("hd")  # Google workspace domain
            },
            "microsoft": {
                "user_id": user_data["id"],
                "email": user_data["mail"] or user_data["userPrincipalName"],
                "name": user_data["displayName"],
                "roles": ["user"],
                "organization": user_data.get("tenantId")
            },
            "github": {
                "user_id": str(user_data["id"]),
                "email": user_data.get("email"),
                "name": user_data["name"] or user_data["login"],
                "picture": user_data.get("avatar_url"),
                "roles": ["user"],
                "organization": None
            }
        }
        
        return mappings.get(provider, {
            "user_id": user_data.get("id", user_data.get("sub")),
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "roles": ["user"],
            "organization": None
        })
    
    def create_saml_auth_request(self) -> str:
        """Create SAML authentication request"""
        if not self.saml_configured:
            raise HTTPException(status_code=400, detail="SAML not configured")
        
        authn_request = self.saml_client.create_authn_request(
            self.saml_config["sp"]["entityid"],
        )
        
        return authn_request
    
    def handle_saml_response(self, saml_response: str) -> Dict[str, Any]:
        """Handle SAML response and return user data"""
        if not self.saml_configured:
            raise HTTPException(status_code=400, detail="SAML not configured")
        
        try:
            authn_response = self.saml_client.parse_authn_request_response(
                saml_response,
                self.saml_config["sp"]["entityid"]
            )
            
            user_data = {
                "user_id": authn_response.name_id,
                "email": authn_response.ava.get("email", [""])[0],
                "name": authn_response.ava.get("displayName", [""])[0],
                "roles": authn_response.ava.get("roles", ["user"]),
                "organization": authn_response.ava.get("organization", [""])[0]
            }
            
            # Create session
            session_id = secrets.token_urlsafe(32)
            jwt_token = self.create_jwt_token(user_data)
            
            session_data = {
                "session_id": session_id,
                "jwt_token": jwt_token,
                "user_data": user_data,
                "provider": "saml",
                "created_at": datetime.utcnow(),
                "last_accessed": datetime.utcnow()
            }
            
            self.sessions[session_id] = session_data
            
            # Update user sessions
            user_id = user_data["user_id"]
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)
            
            return {
                "session_id": session_id,
                "jwt_token": jwt_token,
                "user": user_data
            }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"SAML response processing failed: {str(e)}")
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and return user data"""
        session = self.sessions.get(session_id)
        
        if not session:
            return None
        
        # Check if session is expired
        if datetime.utcnow() > session["created_at"] + self.jwt_expiration:
            del self.sessions[session_id]
            # Remove from user sessions
            user_id = session["user_data"]["user_id"]
            if user_id in self.user_sessions:
                self.user_sessions[user_id].remove(session_id)
            return None
        
        # Update last accessed
        session["last_accessed"] = datetime.utcnow()
        
        return session
    
    def logout(self, session_id: str) -> bool:
        """Logout user by invalidating session"""
        session = self.sessions.get(session_id)
        
        if not session:
            return False
        
        # Remove session
        del self.sessions[session_id]
        
        # Remove from user sessions
        user_id = session["user_data"]["user_id"]
        if user_id in self.user_sessions:
            self.user_sessions[user_id].remove(session_id)
        
        return True
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        session_ids = self.user_sessions.get(user_id, [])
        return [
            {
                "session_id": session_id,
                "created_at": self.sessions[session_id]["created_at"],
                "last_accessed": self.sessions[session_id]["last_accessed"],
                "provider": self.sessions[session_id]["provider"]
            }
            for session_id in session_ids
            if session_id in self.sessions
        ]