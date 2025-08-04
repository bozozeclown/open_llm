# core/context.py
from shared.knowledge.graph import KnowledgeGraph
from shared.schemas import Query, Response
from typing import Dict, Any, List, Optional
import numpy as np
import hashlib
from datetime import datetime
import json
from pathlib import Path

class ContextManager:
    def __init__(self):
        self.graph = KnowledgeGraph()
        self._setup_foundational_knowledge()
        self.interaction_log = []
        self.routing_history = []
        self.config = {}
        self.cache_predictor = None  # Will be initialized by orchestrator
        
    def _setup_foundational_knowledge(self):
        """Initialize with programming fundamentals"""
        foundations = [
            ("variable", "named storage location", ["storage", "memory"]),
            ("function", "reusable code block", ["abstraction", "parameters"]),
            ("loop", "iteration construct", ["repetition", "termination"]),
            ("class", "object blueprint", ["inheritance", "encapsulation"])
        ]
        
        for concept, desc, tags in foundations:
            node_id = self.graph.add_entity(
                content=concept,
                type="concept",
                metadata={
                    "description": desc,
                    "tags": tags,
                    "source": "system"
                }
            )
    
    def process_interaction(
        self, 
        query: Query, 
        response: Response,
        metadata: Optional[Dict] = None
    ):
        """
        Learn from user interactions with routing context
        Args:
            metadata: {
                "sla_tier": str,       # critical/standard/economy
                "reasoning_source": str, # graph/rule/llm
                "provider": str         # gpt-4/llama2/etc
            }
        """
        # Generate unique interaction ID
        interaction_id = hashlib.sha256(
            f"{datetime.now().isoformat()}:{query.content}".encode()
        ).hexdigest()
        
        # Enhanced logging
        log_entry = {
            "id": interaction_id,
            "query": query.content,
            "response": response.content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.interaction_log.append(log_entry)
        
        # Track routing decisions separately
        if metadata:
            self.routing_history.append({
                "timestamp": datetime.now().isoformat(),
                "query_hash": hashlib.sha256(query.content.encode()).hexdigest()[:8],
                **metadata
            })
        
        # Extract knowledge from both query and response
        self.graph.expand_from_text(
            query.content, 
            source="query",
            metadata={"sla_tier": metadata.get("sla_tier")} if metadata else None
        )
        
        self.graph.expand_from_text(
            response.content,
            source="response",
            metadata={"provider": metadata.get("provider")} if metadata else None
        )
        
        # Create relationship between query and response concepts
        query_nodes = self._extract_key_nodes(query.content)
        response_nodes = self._extract_key_nodes(response.content)
        
        for q_node in query_nodes:
            for r_node in response_nodes:
                self.graph.add_relation(
                    q_node, 
                    r_node, 
                    "elicits",
                    metadata=metadata
                )
    
    def get_routing_context(self, query_content: str) -> Dict[str, Any]:
        """
        Get context specifically for routing decisions
        Returns:
            {
                "is_production": bool,
                "similar_past_queries": List[Dict],
                "preferred_llm": Optional[str],
                "complexity_score": float
            }
        """
        # Existing semantic matching
        matches = self.graph.find_semantic_matches(query_content)
        
        # Calculate complexity
        complexity = min(len(query_content.split()) / 10, 1.0)  # 0-1 scale
        
        return {
            "is_production": any(
                "production" in node["content"].lower() 
                for node in matches[:3]
            ),
            "similar_past_queries": [
                {
                    "query": self.graph.graph.nodes[m["node_id"]]["content"],
                    "source": self.graph.graph.nodes[m["node_id"]].get("source"),
                    "success": self._get_interaction_success(m["node_id"])
                }
                for m in matches[:3]
            ],
            "complexity_score": complexity,
            "preferred_llm": self._detect_preferred_provider(query_content)
        }
    
    def _get_interaction_success(self, node_id: str) -> bool:
        """Check if previous interactions with this node were successful"""
        edges = list(self.graph.graph.edges(node_id, data=True))
        return any(
            e[2].get("metadata", {}).get("success", True)
            for e in edges
        )
    
    def _detect_preferred_provider(self, query: str) -> Optional[str]:
        """Detect if query suggests a preferred provider"""
        query_lower = query.lower()
        if "openai" in query_lower:
            return "gpt-4"
        elif "local" in query_lower:
            return "llama2"
        return None
    
    def _extract_key_nodes(self, text: str) -> List[str]:
        """Identify most important nodes in text"""
        matches = self.graph.find_semantic_matches(text)
        return [m["node_id"] for m in matches[:3]]  # Top 3 matches
        
    def get_context(self, text: str) -> Dict[str, Any]:
        """Get relevant context for given text"""
        matches = self.graph.find_semantic_matches(text)
        context_nodes = set()
        
        # Get related nodes for each match
        for match in matches[:5]:  # Top 5 matches
            neighbors = list(self.graph.graph.neighbors(match["node_id"]))
            context_nodes.update(neighbors)
            
        return {
            "matches": matches,
            "related": [
                {"id": n, **self.graph.graph.nodes[n]}
                for n in context_nodes
            ]
        }
    
    def get_interaction_history(self, limit: int = 10) -> List[Dict]:
        """Get recent interaction history"""
        return self.interaction_log[-limit:]
    
    def get_relevant_context(self, query: Dict) -> Dict[str, Any]:
        """Get context relevant to a specific query"""
        context = self.get_context(query.get("content", ""))
        
        # Add routing-specific context
        routing_context = self.get_routing_context(query.get("content", ""))
        
        return {
            **context,
            "routing": routing_context,
            "recent_history": self.get_interaction_history(5)
        }