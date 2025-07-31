from dataclasses import dataclass
from typing import Dict, List, Set, Optional
import networkx as nx
from enum import Enum
import hashlib
import numpy as np
from sentence_transformers import SentenceTransformer
import spacy

class EntityType(Enum):
    CONCEPT = "concept"
    CODE = "code"
    API = "api"
    LIBRARY = "library"
    ERROR = "error"
    PATTERN = "pattern"

@dataclass
class KnowledgeNode:
    id: str
    type: EntityType
    content: str
    metadata: dict
    embeddings: Optional[np.ndarray] = None

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load("en_core_web_sm")
        self._setup_indices()
        
    def _setup_indices(self):
        """Initialize data structures for efficient lookup"""
        self.content_index = {}  # content -> node_id
        self.embedding_index = []  # List of (node_id, embedding)
        
    def _generate_id(self, content: str, type: EntityType) -> str:
        """Create deterministic node ID"""
        return hashlib.sha256(f"{type.value}:{content}".encode()).hexdigest()
        
    def add_entity(self, content: str, type: EntityType, metadata: dict = None) -> str:
        """Add or update an entity with enhanced NLP processing"""
        # Preprocess content
        doc = self.nlp(content)
        normalized_content = " ".join([token.lemma_ for token in doc if not token.is_stop])
        
        node_id = self._generate_id(normalized_content, type)
        embedding = self.encoder.encode(normalized_content)
        
        if node_id not in self.graph:
            self.graph.add_node(node_id, 
                type=type,
                content=content,
                normalized=normalized_content,
                metadata=metadata or {},
                embedding=embedding
            )
            self.content_index[normalized_content] = node_id
            self.embedding_index.append((node_id, embedding))
        else:
            # Update existing node
            self.graph.nodes[node_id]['metadata'].update(metadata or {})
            
        return node_id
        
    def add_relation(self, source_id: str, target_id: str, relation_type: str, weight: float = 1.0):
        """Create weighted relationship between entities"""
        if source_id in self.graph and target_id in self.graph:
            self.graph.add_edge(source_id, target_id, 
                type=relation_type,
                weight=weight
            )
            
    def find_semantic_matches(self, query: str, threshold: float = 0.7) -> List[dict]:
        """Find knowledge nodes semantically similar to query"""
        query_embedding = self.encoder.encode(query)
        matches = []
        
        for node_id, emb in self.embedding_index:
            similarity = np.dot(query_embedding, emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(emb)
            )
            if similarity > threshold:
                matches.append({
                    "node_id": node_id,
                    "similarity": float(similarity),
                    **self.graph.nodes[node_id]
                })
                
        return sorted(matches, key=lambda x: x["similarity"], reverse=True)
        
    def expand_from_text(self, text: str, source: str = "user"):
        """Automatically extract and add knowledge from text"""
        doc = self.nlp(text)
        
        # Extract entities and noun phrases
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        noun_chunks = [(chunk.text, "NOUN_PHRASE") for chunk in doc.noun_chunks]
        
        # Add to knowledge graph
        nodes = []
        for content, label in entities + noun_chunks:
            node_id = self.add_entity(
                content=content,
                type=self._map_spacy_label(label),
                metadata={"source": source}
            )
            nodes.append(node_id)
            
        # Create relationships based on syntactic dependencies
        for sent in doc.sents:
            for token in sent:
                if token.dep_ in ("dobj", "nsubj", "attr"):
                    source = self._get_node_for_token(token.head)
                    target = self._get_node_for_token(token)
                    if source and target:
                        self.add_relation(source, target, token.dep_)
    
    def _map_spacy_label(self, label: str) -> EntityType:
        """Map Spacy labels to our entity types"""
        mapping = {
            "PERSON": "concept",
            "ORG": "concept",
            "GPE": "concept",
            "PRODUCT": "api",
            "NOUN_PHRASE": "concept"
        }
        return EntityType(mapping.get(label, "concept"))
        
    def _get_node_for_token(self, token) -> Optional[str]:
        """Find or create node for a Spacy token"""
        text = token.lemma_
        return self.content_index.get(text)
        
    def get_statistics(self) -> dict:
        """Return comprehensive graph statistics"""
        centrality = nx.degree_centrality(self.graph)
        top_nodes = sorted(
            [(n, c) for n, c in centrality.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "basic": {
                "nodes": len(self.graph.nodes()),
                "edges": len(self.graph.edges()),
                "components": nx.number_weakly_connected_components(self.graph)
            },
            "centrality": {
                "top_concepts": [
                    {"id": n[0], "content": self.graph.nodes[n[0]]["content"], "score": n[1]}
                    for n in top_nodes
                ]
            },
            "types": {
                nt: sum(1 for n in self.graph.nodes() if self.graph.nodes[n]["type"] == nt)
                for nt in set(nx.get_node_attributes(self.graph, "type").values())
            }
        }

    def export_gexf(self, path: str):
        """Export graph to GEXF format for external tools"""
        nx.write_gexf(self.graph, path)