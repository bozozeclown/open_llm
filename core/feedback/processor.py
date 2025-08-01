from datetime import datetime
from typing import Dict, Any
import numpy as np
from shared.knowledge.graph import KnowledgeGraph

class FeedbackProcessor:
    def __init__(self, context_manager):
        self.context = context_manager
        self.feedback_weights = {
            'explicit_rating': 0.7,
            'implicit_engagement': 0.3,
            'correction': 1.0
        }

    def process_feedback(self, feedback: Dict[str, Any]):
        """Handle both explicit and implicit feedback"""
        # Store raw feedback
        self._log_feedback(feedback)

        # Update knowledge graph
        if feedback['type'] == 'correction':
            self._apply_correction(feedback)
        else:
            self._update_edge_weights(feedback)

    def _apply_correction(self, feedback):
        """Direct knowledge corrections"""
        self.context.graph.update_node(
            node_id=feedback['target_node'],
            new_content=feedback['corrected_info'],
            metadata={'last_corrected': datetime.now()}
        )

    def _update_edge_weights(self, feedback):
        """Adjust relationship strengths"""
        current_weight = self.context.graph.get_edge_weight(
            feedback['query_node'],
            feedback['response_node']
        )
        
        new_weight = current_weight * (1 + self._calculate_feedback_impact(feedback))
        self.context.graph.update_edge(
            source=feedback['query_node'],
            target=feedback['response_node'],
            weight=min(new_weight, 1.0)  # Cap at 1.0
        )

    def _calculate_feedback_impact(self, feedback) -> float:
        """Calculate weighted feedback impact"""
        base_score = (
            feedback.get('rating', 0.5) * self.feedback_weights['explicit_rating'] +
            feedback.get('engagement', 0.2) * self.feedback_weights['implicit_engagement']
        )
        return base_score * (2 if feedback['type'] == 'positive' else -1)