from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from ..knowledge.graph import KnowledgeGraph
from ..context import ContextManager
import logging

class HybridEngine:
    def __init__(self, context: ContextManager):
        self.context = context
        self.graph = context.graph
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.logger = logging.getLogger("reasoning.engine")
        self._init_rules()
        self.learning = SelfLearningEngine(context)
        self.performance = PerformanceTracker()
        self.query_hasher = QueryHasher()

    def _init_rules(self):
        """Load rule-based patterns"""
        self.rules = {
            'list_comp': {
                'pattern': '[x for x in {iterable} if {condition}]',
                'vars': ['iterable', 'condition']
            },
            'context_mgr': {
                'pattern': 'with {expr} as {var}:',
                'vars': ['expr', 'var']
            }
        }

    async def process(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Main reasoning pipeline"""
        # Stage 1: Local Graph Check
        if graph_result := await self._check_graph(query):
            return graph_result

        # Stage 2: Rule Application
        if rule_result := self._apply_rules(query):
            return rule_result

        # Stage 3: LLM Fallback
        return await self._query_llm(query)
        
        result = await self._process_query(query)
        
        # Self-learning hook
        if result.get('success', True):
            self.learning.observe_solution(
                problem=query.get('code', ''),
                solution=str(result),
                source=result.get('source', 'llm')
            )
        
        return result
        
        query_hash = self.query_hasher.hash_query(query)
        recommended_source = self.performance.get_recommended_source(query_hash)
        
        # Route based on performance
        if recommended_source == 'graph':
            result = await self._check_graph(query)
        elif recommended_source == 'rule':
            result = self._apply_rules(query)
        else:
            result = await self._query_llm(query)

        # Record metrics
        self.performance.record_metric(
            source=result.get('source', 'llm'),
            latency=result['latency'],
            success=result.get('success', True),
            query_hash=query_hash
        )
        
        return result

    async def _check_graph(self, query: Dict) -> Optional[Dict]:
        """Check knowledge graph for solutions"""
        try:
            if 'code_context' in query:
                matches = self.graph.find_similar(
                    query['code_context'],
                    threshold=0.7
                )
                if matches:
                    return {'source': 'graph', 'result': matches[0]['solution']}
        except Exception as e:
            self.logger.error(f"Graph query failed: {str(e)}")
        return None

    def _apply_rules(self, query: Dict) -> Optional[Dict]:
        """Apply pre-defined coding patterns"""
        code = query.get('code', '')
        for rule_name, rule in self.rules.items():
            if all(var in code for var in rule['vars']):
                return {
                    'source': 'rule',
                    'rule': rule_name,
                    'template': rule['pattern'].format(**query)
                }
        return None

    async def _query_llm(self, query: Dict) -> Dict:
        """Route to best-suited LLM"""
        llm_pref = query.get('llm', self.context.config.get('default_llm'))
        return await self.context.plugin_manager.execute_llm(
            llm_pref,
            self._build_llm_payload(query)
        )

    def _build_llm_payload(self, query: Dict) -> Dict:
        """Enhance query with context"""
        return {
            **query,
            'context': self.context.get_relevant_context(query),
            'history': self.context.get_interaction_history()
        }