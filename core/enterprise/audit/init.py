import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum
import asyncio
import aiofiles
from dataclasses import dataclass, asdict

class AuditEventType(Enum):
    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    # Team events
    TEAM_CREATED = "team_created"
    TEAM_UPDATED = "team_updated"
    TEAM_DELETED = "team_deleted"
    MEMBER_INVITED = "member_invited"
    MEMBER_JOINED = "member_joined"
    MEMBER_REMOVED = "member_removed"
    ROLE_CHANGED = "role_changed"
    
    # Resource events
    RESOURCE_CREATED = "resource_created"
    RESOURCE_UPDATED = "resource_updated"
    RESOURCE_DELETED = "resource_deleted"
    RESOURCE_SHARED = "resource_shared"
    RESOURCE_ACCESSED = "resource_accessed"
    
    # Data events
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    CONFIG_CHANGED = "config_changed"
    
    # Security events
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

@dataclass
class AuditEvent:
    event_id: str
    event_type: AuditEventType
    user_id: str
    user_email: str
    team_id: Optional[str]
    resource_id: Optional[str]
    action: str
    description: str
    metadata: Dict[str, Any]
    timestamp: datetime
    ip_address: str
    user_agent: str
    session_id: Optional[str]

class AuditLogger:
    def __init__(self, storage_path: str = "data/enterprise/audit"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_log_file = self.storage_path / f"audit_{datetime.now().strftime('%Y_%m_%d')}.jsonl"
        self._buffer = []
        self._buffer_size = 100
        self._lock = asyncio.Lock()
        
        # Start background flush task
        asyncio.create_task(self._periodic_flush())
    
    async def _periodic_flush(self):
        """Periodically flush audit buffer to disk"""
        while True:
            await asyncio.sleep(60)  # Flush every minute
            await self.flush_buffer()
    
    async def log_event(self, event_type: AuditEventType, user_id: str, user_email: str,
                       action: str, description: str, metadata: Dict[str, Any] = None,
                       team_id: str = None, resource_id: str = None, 
                       ip_address: str = None, user_agent: str = None, 
                       session_id: str = None):
        """Log an audit event"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            user_id=user_id,
            user_email=user_email,
            team_id=team_id,
            resource_id=resource_id,
            action=action,
            description=description,
            metadata=metadata or {},
            timestamp=datetime.utcnow(),
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown",
            session_id=session_id
        )
        
        async with self._lock:
            self._buffer.append(event)
            
            if len(self._buffer) >= self._buffer_size:
                await self._flush_buffer_internal()
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        random_part = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
        return f"{timestamp}_{random_part}"
    
    async def _flush_buffer_internal(self):
        """Internal method to flush buffer to disk"""
        if not self._buffer:
            return
        
        # Ensure log file exists
        if not self.current_log_file.exists():
            self.current_log_file.touch()
        
        # Write events to file
        async with aiofiles.open(self.current_log_file, mode='a') as f:
            for event in self._buffer:
                event_dict = asdict(event)
                event_dict['event_type'] = event.event_type.value
                event_dict['timestamp'] = event.timestamp.isoformat()
                await f.write(json.dumps(event_dict) + '\n')
        
        self._buffer.clear()
        
        # Rotate log file if it's too large
        if self.current_log_file.stat().st_size > 100 * 1024 * 1024:  # 100MB
            await self._rotate_log_file()
    
    async def flush_buffer(self):
        """Public method to flush buffer"""
        async with self._lock:
            await self._flush_buffer_internal()
    
    async def _rotate_log_file(self):
        """Rotate log file when it gets too large"""
        current_date = datetime.now().strftime('%Y_%m_%d')
        counter = 1
        
        while True:
            new_filename = self.storage_path / f"audit_{current_date}_{counter}.jsonl"
            if not new_filename.exists():
                break
            counter += 1
        
        self.current_log_file = new_filename
    
    async def query_events(self, start_date: datetime = None, end_date: datetime = None,
                          user_id: str = None, team_id: str = None,
                          event_types: List[AuditEventType] = None,
                          limit: int = 1000) -> List[AuditEvent]:
        """Query audit events"""
        events = []
        
        # Determine which files to search
        if start_date and end_date:
            search_files = self._get_log_files_in_range(start_date, end_date)
        else:
            search_files = list(self.storage_path.glob("audit_*.jsonl"))
        
        # Search through files
        for log_file in sorted(search_files):
            async with aiofiles.open(log_file, 'r') as f:
                async for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        
                        # Parse timestamp
                        timestamp = datetime.fromisoformat(event_data['timestamp'])
                        
                        # Apply filters
                        if start_date and timestamp < start_date:
                            continue
                        if end_date and timestamp > end_date:
                            continue
                        if user_id and event_data['user_id'] != user_id:
                            continue
                        if team_id and event_data.get('team_id') != team_id:
                            continue
                        if event_types and AuditEventType(event_data['event_type']) not in event_types:
                            continue
                        
                        # Convert back to AuditEvent
                        event = AuditEvent(
                            event_id=event_data['event_id'],
                            event_type=AuditEventType(event_data['event_type']),
                            user_id=event_data['user_id'],
                            user_email=event_data['user_email'],
                            team_id=event_data.get('team_id'),
                            resource_id=event_data.get('resource_id'),
                            action=event_data['action'],
                            description=event_data['description'],
                            metadata=event_data.get('metadata', {}),
                            timestamp=timestamp,
                            ip_address=event_data['ip_address'],
                            user_agent=event_data['user_agent'],
                            session_id=event_data.get('session_id')
                        )
                        
                        events.append(event)
                        
                        if len(events) >= limit:
                            return events[:limit]
                    
                    except (json.JSONDecodeError, KeyError, ValueError):
                        # Skip malformed entries
                        continue
        
        return events[:limit]
    
    def _get_log_files_in_range(self, start_date: datetime, end_date: datetime) -> List[Path]:
        """Get log files that might contain events in the given date range"""
        files = []
        
        # Generate all possible dates in range
        current_date = start_date.date()
        end_date_obj = end_date.date()
        
        while current_date <= end_date_obj:
            date_str = current_date.strftime('%Y_%m_%d')
            base_file = self.storage_path / f"audit_{date_str}.jsonl"
            
            if base_file.exists():
                files.append(base_file)
            
            # Check for rotated files
            counter = 1
            while True:
                rotated_file = self.storage_path / f"audit_{date_str}_{counter}.jsonl"
                if rotated_file.exists():
                    files.append(rotated_file)
                    counter += 1
                else:
                    break
            
            current_date = datetime.strptime(str(current_date), '%Y-%m-%d').date() + timedelta(days=1)
        
        return files
    
    async def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get activity summary for a user"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        events = await self.query_events(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        # Group by event type
        event_counts = {}
        for event in events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Calculate activity metrics
        active_days = len(set(event.timestamp.date() for event in events))
        total_events = len(events)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": total_events,
            "active_days": active_days,
            "event_breakdown": event_counts,
            "avg_events_per_day": total_events / days if days > 0 else 0,
            "last_activity": max(event.timestamp for event in events) if events else None
        }
    
    async def get_team_audit_summary(self, team_id: str, days: int = 30) -> Dict[str, Any]:
        """Get audit summary for a team"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        events = await self.query_events(
            start_date=start_date,
            end_date=end_date,
            team_id=team_id
        )
        
        # Group by event type
        event_counts = {}
        user_activity = {}
        
        for event in events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Track user activity
            if event.user_id not in user_activity:
                user_activity[event.user_id] = {
                    "user_email": event.user_email,
                    "event_count": 0,
                    "last_activity": event.timestamp
                }
            
            user_activity[event.user_id]["event_count"] += 1
            user_activity[event.user_id]["last_activity"] = max(
                user_activity[event.user_id]["last_activity"],
                event.timestamp
            )
        
        return {
            "team_id": team_id,
            "period_days": days,
            "total_events": len(events),
            "event_breakdown": event_counts,
            "active_users": len(user_activity),
            "user_activity": [
                {
                    "user_id": user_id,
                    "user_email": data["user_email"],
                    "event_count": data["event_count"],
                    "last_activity": data["last_activity"].isoformat()
                }
                for user_id, data in user_activity.items()
            ]
        }