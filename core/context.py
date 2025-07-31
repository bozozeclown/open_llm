from shared.knowledge.graph import KnowledgeGraph
from shared.schemas import Query, Response
from typing import Dict, Any
import numpy as np
import hashlib
from datetime import datetime

class ContextManager:
    def __init__(self):
        self.graph = KnowledgeGraph()
        self._setup_foundational_knowledge()
        self.interaction_log = []
        
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
            
    def process_interaction(self, query: Query, response: Response):
        """Learn from user interactions"""
        # Generate unique interaction ID
        interaction_id = hashlib.sha256(
            f"{datetime.now().isoformat()}:{query.content}".encode()
        ).hexdigest()
        
        # Log the interaction
        self.interaction_log.append({
            "id": interaction_id,
            "query": query.content,
            "response": response.content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Extract knowledge from both query and response
        self.graph.expand_from_text(query.content, source="query")
        self.graph.expand_from_text(response.content, source="response")
        
        # Create relationship between query and response concepts
        query_nodes = self._extract_key_nodes(query.content)
        response_nodes = self._extract_key_nodes(response.content)
        
        for q_node in query_nodes:
            for r_node in response_nodes:
                self.graph.add_relation(q_node, r_node, "elicits")
                
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