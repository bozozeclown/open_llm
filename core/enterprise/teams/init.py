import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import json
from pathlib import Path

class TeamRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    GUEST = "guest"

class Permission(Enum):
    # Team permissions
    CREATE_TEAM = "create_team"
    DELETE_TEAM = "delete_team"
    INVITE_MEMBER = "invite_member"
    REMOVE_MEMBER = "remove_member"
    UPDATE_TEAM = "update_team"
    
    # Resource permissions
    CREATE_RESOURCE = "create_resource"
    READ_RESOURCE = "read_resource"
    UPDATE_RESOURCE = "update_resource"
    DELETE_RESOURCE = "delete_resource"
    SHARE_RESOURCE = "share_resource"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_BILLING = "manage_billing"
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"

@dataclass
class TeamMember:
    user_id: str
    email: str
    name: str
    role: TeamRole
    permissions: List[Permission]
    joined_at: datetime
    last_active: datetime
    invited_by: Optional[str] = None

@dataclass
class Team:
    team_id: str
    name: str
    description: str
    owner_id: str
    members: Dict[str, TeamMember]  # user_id -> TeamMember
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    billing_info: Dict[str, Any] = None

class TeamManager:
    def __init__(self, storage_path: str = "data/enterprise"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.teams_file = self.storage_path / "teams.json"
        self.teams: Dict[str, Team] = {}
        self._load_teams()
        
        # Role permissions mapping
        self.role_permissions = {
            TeamRole.OWNER: list(Permission),  # All permissions
            TeamRole.ADMIN: [
                Permission.CREATE_RESOURCE,
                Permission.READ_RESOURCE,
                Permission.UPDATE_RESOURCE,
                Permission.DELETE_RESOURCE,
                Permission.SHARE_RESOURCE,
                Permission.INVITE_MEMBER,
                Permission.REMOVE_MEMBER,
                Permission.UPDATE_TEAM,
                Permission.VIEW_ANALYTICS
            ],
            TeamRole.MEMBER: [
                Permission.CREATE_RESOURCE,
                Permission.READ_RESOURCE,
                Permission.UPDATE_RESOURCE,
                Permission.SHARE_RESOURCE
            ],
            TeamRole.GUEST: [
                Permission.READ_RESOURCE
            ]
        }
    
    def _load_teams(self):
        """Load teams from storage"""
        if self.teams_file.exists():
            with open(self.teams_file, 'r') as f:
                teams_data = json.load(f)
                
                for team_id, team_data in teams_data.items():
                    # Convert members back to TeamMember objects
                    members = {}
                    for user_id, member_data in team_data["members"].items():
                        members[user_id] = TeamMember(
                            user_id=member_data["user_id"],
                            email=member_data["email"],
                            name=member_data["name"],
                            role=TeamRole(member_data["role"]),
                            permissions=[Permission(p) for p in member_data["permissions"]],
                            joined_at=datetime.fromisoformat(member_data["joined_at"]),
                            last_active=datetime.fromisoformat(member_data["last_active"]),
                            invited_by=member_data.get("invited_by")
                        )
                    
                    self.teams[team_id] = Team(
                        team_id=team_id,
                        name=team_data["name"],
                        description=team_data["description"],
                        owner_id=team_data["owner_id"],
                        members=members,
                        settings=team_data["settings"],
                        created_at=datetime.fromisoformat(team_data["created_at"]),
                        updated_at=datetime.fromisoformat(team_data["updated_at"]),
                        billing_info=team_data.get("billing_info")
                    )
    
    def _save_teams(self):
        """Save teams to storage"""
        teams_data = {}
        
        for team_id, team in self.teams.items():
            teams_data[team_id] = {
                "name": team.name,
                "description": team.description,
                "owner_id": team.owner_id,
                "members": {
                    user_id: {
                        "user_id": member.user_id,
                        "email": member.email,
                        "name": member.name,
                        "role": member.role.value,
                        "permissions": [p.value for p in member.permissions],
                        "joined_at": member.joined_at.isoformat(),
                        "last_active": member.last_active.isoformat(),
                        "invited_by": member.invited_by
                    }
                    for user_id, member in team.members.items()
                },
                "settings": team.settings,
                "created_at": team.created_at.isoformat(),
                "updated_at": team.updated_at.isoformat(),
                "billing_info": team.billing_info
            }
        
        with open(self.teams_file, 'w') as f:
            json.dump(teams_data, f, indent=2)
    
    def create_team(self, name: str, description: str, owner_id: str, 
                   owner_email: str, owner_name: str, 
                   settings: Dict[str, Any] = None) -> Team:
        """Create a new team"""
        team_id = str(uuid.uuid4())
        
        # Create owner member
        owner_member = TeamMember(
            user_id=owner_id,
            email=owner_email,
            name=owner_name,
            role=TeamRole.OWNER,
            permissions=self.role_permissions[TeamRole.OWNER],
            joined_at=datetime.utcnow(),
            last_active=datetime.utcnow()
        )
        
        team = Team(
            team_id=team_id,
            name=name,
            description=description,
            owner_id=owner_id,
            members={owner_id: owner_member},
            settings=settings or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.teams[team_id] = team
        self._save_teams()
        
        return team
    
    def get_team(self, team_id: str) -> Optional[Team]:
        """Get team by ID"""
        return self.teams.get(team_id)
    
    def get_user_teams(self, user_id: str) -> List[Team]:
        """Get all teams for a user"""
        return [team for team in self.teams.values() if user_id in team.members]
    
    def invite_member(self, team_id: str, inviter_id: str, 
                    invitee_email: str, invitee_name: str, 
                    role: TeamRole = TeamRole.MEMBER) -> bool:
        """Invite a member to a team"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        # Check if inviter has permission to invite
        inviter = team.members.get(inviter_id)
        if not inviter or Permission.INVITE_MEMBER not in inviter.permissions:
            return False
        
        # Check if user is already a member
        for member in team.members.values():
            if member.email == invitee_email:
                return False
        
        # Create temporary member (will be confirmed when user accepts)
        temp_user_id = f"temp_{uuid.uuid4()}"
        new_member = TeamMember(
            user_id=temp_user_id,
            email=invitee_email,
            name=invitee_name,
            role=role,
            permissions=self.role_permissions[role],
            joined_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
            invited_by=inviter_id
        )
        
        team.members[temp_user_id] = new_member
        team.updated_at = datetime.utcnow()
        self._save_teams()
        
        # TODO: Send invitation email
        # self._send_invitation_email(team, new_member)
        
        return True
    
    def accept_invitation(self, team_id: str, user_id: str, user_email: str) -> bool:
        """Accept team invitation"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        # Find temporary member
        temp_member = None
        for member_id, member in team.members.items():
            if member.email == user_email and member.user_id.startswith("temp_"):
                temp_member = member
                temp_member_id = member_id
                break
        
        if not temp_member:
            return False
        
        # Replace temporary member with real user
        del team.members[temp_member_id]
        
        new_member = TeamMember(
            user_id=user_id,
            email=user_email,
            name=temp_member.name,
            role=temp_member.role,
            permissions=temp_member.permissions,
            joined_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
            invited_by=temp_member.invited_by
        )
        
        team.members[user_id] = new_member
        team.updated_at = datetime.utcnow()
        self._save_teams()
        
        return True
    
    def remove_member(self, team_id: str, remover_id: str, member_id: str) -> bool:
        """Remove a member from a team"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        # Check if remover has permission
        remover = team.members.get(remover_id)
        if not remover or Permission.REMOVE_MEMBER not in remover.permissions:
            return False
        
        # Cannot remove owner
        if member_id == team.owner_id:
            return False
        
        if member_id in team.members:
            del team.members[member_id]
            team.updated_at = datetime.utcnow()
            self._save_teams()
            return True
        
        return False
    
    def update_member_role(self, team_id: str, updater_id: str, 
                          member_id: str, new_role: TeamRole) -> bool:
        """Update member role"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        # Check if updater has permission
        updater = team.members.get(updater_id)
        if not updater or Permission.UPDATE_TEAM not in updater.permissions:
            return False
        
        # Cannot change owner role
        if member_id == team.owner_id:
            return False
        
        if member_id in team.members:
            team.members[member_id].role = new_role
            team.members[member_id].permissions = self.role_permissions[new_role]
            team.updated_at = datetime.utcnow()
            self._save_teams()
            return True
        
        return False
    
    def check_permission(self, user_id: str, team_id: str, permission: Permission) -> bool:
        """Check if user has specific permission in a team"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        member = team.members.get(user_id)
        if not member:
            return False
        
        return permission in member.permissions
    
    def get_team_resources(self, team_id: str) -> Dict[str, Any]:
        """Get team resources and settings"""
        team = self.teams.get(team_id)
        if not team:
            return {}
        
        return {
            "team_id": team_id,
            "name": team.name,
            "settings": team.settings,
            "member_count": len(team.members),
            "billing_info": team.billing_info
        }
    
    def update_team_settings(self, team_id: str, updater_id: str, 
                           settings: Dict[str, Any]) -> bool:
        """Update team settings"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        # Check if updater has permission
        updater = team.members.get(updater_id)
        if not updater or Permission.UPDATE_TEAM not in updater.permissions:
            return False
        
        team.settings.update(settings)
        team.updated_at = datetime.utcnow()
        self._save_teams()
        
        return True
    
    def delete_team(self, team_id: str, deleter_id: str) -> bool:
        """Delete a team"""
        team = self.teams.get(team_id)
        if not team:
            return False
        
        # Only owner can delete team
        if deleter_id != team.owner_id:
            return False
        
        del self.teams[team_id]
        self._save_teams()
        
        return True