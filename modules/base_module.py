from abc import ABC, abstractmethod
from typing import List, Optional
from enum import Enum
from shared.schemas import Query, Response
from core.orchestrator import Capability

class BaseModule(ABC):
    MODULE_ID: str
    VERSION: str
    CAPABILITIES: List[Capability]
    PRIORITY: int = 0
    
    def __init__(self):
        self.context = None  # Will be set by service
        self._usage_count = 0
        
    @classmethod
    def get_metadata(cls) -> dict:
        return {
            "id": cls.MODULE_ID,
            "version": cls.VERSION,
            "capabilities": [cap.value for cap in cls.CAPABILITIES],
            "priority": cls.PRIORITY
        }
    
    async def initialize(self):
        """Initialize with module-specific knowledge"""
        self._load_domain_knowledge()
        self._ready = True
        
    @abstractmethod
    def _load_domain_knowledge(self):
        """Preload module-specific knowledge"""
        pass
        
    @abstractmethod
    async def process(self, query: Query) -> Response:
        """Process query using contextual knowledge"""
        pass
        
    def health_check(self) -> dict:
        """Report health including knowledge metrics"""
        return {
            "status": "ready" if self._ready else "loading",
            "version": self.VERSION,
            "usage": self._usage_count,
            "knowledge": self._get_knowledge_stats()
        }
        
    def _get_knowledge_stats(self) -> dict:
        """Get module-specific knowledge metrics"""
        if not self.context:
            return {}
            
        return {
            "nodes": len([
                n for n in self.context.graph.graph.nodes()
                if self.context.graph.graph.nodes[n].get("module") == self.MODULE_ID
            ]),
            "relationships": len([
                e for e in self.context.graph.graph.edges()
                if self.context.graph.graph.edges[e].get("module") == self.MODULE_ID
            ])
        }