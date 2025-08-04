# core/versioning/__init__.py
import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class VersionInfo:
    version_id: str
    timestamp: datetime
    description: str
    snapshot: Dict[str, Any]
    author: str = "system"
    tags: List[str] = None

class KnowledgeVersioner:
    def __init__(self, knowledge_graph, storage_path: str = "data/versions"):
        self.graph = knowledge_graph
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.versions: Dict[str, VersionInfo] = {}
        self._load_versions()
    
    def _load_versions(self):
        """Load existing versions from storage"""
        if (self.storage_path / "versions.json").exists():
            with open(self.storage_path / "versions.json", 'r') as f:
                versions_data = json.load(f)
                for version_id, data in versions_data.items():
                    self.versions[version_id] = VersionInfo(
                        version_id=version_id,
                        timestamp=datetime.fromisoformat(data['timestamp']),
                        description=data['description'],
                        snapshot=data['snapshot'],
                        author=data.get('author', 'system'),
                        tags=data.get('tags', [])
                    )
    
    def create_version(self, description: str, author: str = "system", tags: List[str] = None) -> str:
        """Create a new version of the knowledge graph"""
        version_id = str(uuid.uuid4())
        snapshot = self._create_snapshot()
        
        version_info = VersionInfo(
            version_id=version_id,
            timestamp=datetime.now(),
            description=description,
            snapshot=snapshot,
            author=author,
            tags=tags or []
        )
        
        self.versions[version_id] = version_info
        self._save_version(version_info)
        self._save_versions_index()
        
        return version_id
    
    def _create_snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of the current knowledge graph state"""
        return {
            "nodes": len(self.graph.graph.nodes()),
            "edges": len(self.graph.graph.edges()),
            "node_data": {
                node_id: {
                    "type": data.get("type"),
                    "content": data.get("content"),
                    "metadata": data.get("metadata", {})
                }
                for node_id, data in self.graph.graph.nodes(data=True)
            },
            "edge_data": {
                (source, target): {
                    "type": data.get("type"),
                    "weight": data.get("weight", 1.0)
                }
                for source, target, data in self.graph.graph.edges(data=True)
            }
        }
    
    def _save_version(self, version_info: VersionInfo):
        """Save individual version to file"""
        version_file = self.storage_path / f"{version_info.version_id}.json"
        with open(version_file, 'w') as f:
            json.dump({
                "version_id": version_info.version_id,
                "timestamp": version_info.timestamp.isoformat(),
                "description": version_info.description,
                "snapshot": version_info.snapshot,
                "author": version_info.author,
                "tags": version_info.tags or []
            }, f, indent=2)
    
    def _save_versions_index(self):
        """Save the versions index"""
        versions_index = {
            version_id: {
                "timestamp": info.timestamp.isoformat(),
                "description": info.description,
                "author": info.author,
                "tags": info.tags or []
            }
            for version_id, info in self.versions.items()
        }
        
        with open(self.storage_path / "versions.json", 'w') as f:
            json.dump(versions_index, f, indent=2)
    
    def get_version(self, version_id: str) -> Optional[VersionInfo]:
        """Get a specific version by ID"""
        return self.versions.get(version_id)
    
    def list_versions(self) -> List[VersionInfo]:
        """List all versions in chronological order"""
        return sorted(self.versions.values(), key=lambda x: x.timestamp, reverse=True)
    
    def restore_version(self, version_id: str) -> bool:
        """Restore the knowledge graph to a specific version"""
        if version_id not in self.versions:
            return False
        
        version_info = self.versions[version_id]
        snapshot = version_info.snapshot
        
        # Clear current graph
        self.graph.graph.clear()
        
        # Restore nodes
        for node_id, node_data in snapshot["node_data"].items():
            self.graph.graph.add_node(node_id, **node_data)
        
        # Restore edges
        for (source, target), edge_data in snapshot["edge_data"].items():
            self.graph.graph.add_edge(source, target, **edge_data)
        
        return True
    
    def get_latest_version(self) -> Optional[VersionInfo]:
        """Get the most recent version"""
        if not self.versions:
            return None
        return max(self.versions.values(), key=lambda x: x.timestamp)
    
    def delete_version(self, version_id: str) -> bool:
        """Delete a version"""
        if version_id not in self.versions:
            return False
        
        del self.versions[version_id]
        
        # Remove version file
        version_file = self.storage_path / f"{version_id}.json"
        if version_file.exists():
            version_file.unlink()
        
        # Update index
        self._save_versions_index()
        
        return True