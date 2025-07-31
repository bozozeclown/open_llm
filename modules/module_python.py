from modules.base_module import BaseModule
from shared.schemas import Response, Query
from core.orchestrator import Capability

class PythonModule(BaseModule):
    MODULE_ID = "python"
    VERSION = "0.2.0"
    CAPABILITIES = [
        Capability.CODE_COMPLETION,
        Capability.DEBUGGING,
        Capability.DOCSTRING
    ]
    PRIORITY = 10
    
    async def initialize(self):
        self._ready = True
        # Initialize with Python-specific knowledge
        self._init_python_knowledge()
        
    def _init_python_knowledge(self):
        """Preload Python-specific concepts"""
        python_concepts = [
            ("list", "mutable sequence"),
            ("dict", "key-value mapping"),
            ("generator", "iterator creator"),
            ("decorator", "function wrapper")
        ]
        
        for concept, desc in python_concepts:
            self.context.graph.add_entity(
                content=concept,
                type="python_concept",
                metadata={
                    "description": desc,
                    "language": "python"
                }
            )
        
    async def process(self, query: Query) -> Response:
        """Process Python queries with knowledge context"""
        # Extract context from query metadata
        context = query.context.get("knowledge_graph", {})
        
        # Generate response using contextual knowledge
        response_content = self._generate_response(query.content, context)
        
        return Response(
            content=response_content,
            metadata={
                "module": self.MODULE_ID,
                "capabilities": [cap.value for cap in self.CAPABILITIES],
                "context_used": bool(context)
            },
            metrics={"python_processing": 0.42}
        )
        
    def _generate_response(self, content: str, context: dict) -> str:
        """Generate response using available knowledge"""
        # Simplified response generation
        if "def " in content:
            return f"Python function suggestion based on {len(context.get('nodes', []))} related concepts..."
        return f"Python code solution referencing {context.get('edges', [])[:2]}..."
        
    def health_check(self) -> dict:
        return {
            "status": "ready",
            "version": self.VERSION,
            "knowledge_nodes": len([
                n for n in self.context.graph.graph.nodes()
                if self.context.graph.graph.nodes[n]['type'] == "python_concept"
            ])
        }
    
    async def process(self, query: Query) -> Response:
        """Enhanced processing with visualization support"""
        # Generate standard response
        response = await super().process(query)
        
        # Add visualization if requested
        if "visualize" in query.tags:
            graph_data = self._extract_relevant_subgraph(query.content)
            response.metadata["visualization"] = {
                "type": "knowledge_subgraph",
                "data": graph_data
            }
            
        return response
        
    def _extract_relevant_subgraph(self, content: str) -> dict:
        """Create a subgraph relevant to the query"""
        matches = self.context.graph.find_semantic_matches(content)
        if not matches:
            return {}
            
        central_node = matches[0]["node_id"]
        subgraph = nx.ego_graph(self.context.graph.graph, central_node, radius=2)
        
        return {
            "central_concept": self.context.graph.graph.nodes[central_node],
            "related": [
                {
                    "id": n,
                    "content": self.context.graph.graph.nodes[n]["content"],
                    "type": self.context.graph.graph.nodes[n]["type"],
                    "relations": [
                        {
                            "target": e[1],
                            "type": e[2]["type"],
                            "weight": e[2].get("weight", 1.0)
                        }
                        for e in subgraph.edges(n, data=True)
                    ]
                }
                for n in subgraph.nodes() if n != central_node
            ]
        }