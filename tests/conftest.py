# tests/conftest.py
import pytest
import asyncio
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import ContextManager
from core.orchestrator import Orchestrator
from core.validation.quality_gates import QualityValidator
from modules.registry import ModuleRegistry
from shared.knowledge.graph import KnowledgeGraph

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def context_manager():
    """Create a test context manager"""
    context = ContextManager()
    yield context
    # Cleanup
    context.graph.graph.clear()

@pytest.fixture
async def module_registry():
    """Create a test module registry"""
    registry = ModuleRegistry()
    registry.discover_modules()
    yield registry

@pytest.fixture
async def quality_validator():
    """Create a test quality validator"""
    config = {
        "quality_standards": {
            "min_complexity": 0.3,
            "required_keys": ["answer", "explanation"],
            "banned_patterns": ["eval(", "system("]
        }
    }
    return QualityValidator(config)

# tests/test_orchestrator.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from shared.schemas import Query, Response
from core.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_route_query_success(context_manager, module_registry):
    """Test successful query routing"""
    # Mock dependencies
    validator = MagicMock()
    sla_router = MagicMock()
    load_balancer = MagicMock()
    healing_controller = MagicMock()
    reasoning_engine = MagicMock()
    monitoring = MagicMock()
    
    # Configure mocks
    sla_router.select_provider.return_value = {"provider": "test", "tier": "standard"}
    reasoning_engine.process.return_value = {"source": "llm", "result": "test response"}
    
    module = MagicMock()
    module.process.return_value = Response(content="test response")
    module_registry.get_module.return_value = module
    
    validator.validate.return_value = {
        "passed": True,
        "checks": {},
        "original_response": Response(content="test response")
    }
    
    # Create orchestrator
    orchestrator = Orchestrator(
        validator=validator,
        sla_router=sla_router,
        load_balancer=load_balancer,
        registry=module_registry,
        healing_controller=healing_controller,
        context_manager=context_manager,
        reasoning_engine=reasoning_engine,
        monitoring=monitoring
    )
    
    # Test query
    query = Query(content="test query")
    response = await orchestrator.route_query(query)
    
    # Assertions
    assert response.content == "test response"
    assert sla_router.select_provider.called
    assert reasoning_engine.process.called
    assert module.process.called

@pytest.mark.asyncio
async def test_route_query_with_quality_failure(context_manager, module_registry):
    """Test query routing with quality validation failure"""
    # Mock dependencies
    validator = MagicMock()
    sla_router = MagicMock()
    load_balancer = MagicMock()
    healing_controller = MagicMock()
    reasoning_engine = MagicMock()
    monitoring = MagicMock()
    
    # Configure mocks
    sla_router.select_provider.return_value = {"provider": "test", "tier": "standard"}
    reasoning_engine.process.return_value = {"source": "llm", "result": "test response"}
    
    module = MagicMock()
    module.process.return_value = Response(content="test response")
    module_registry.get_module.return_value = module
    
    validator.validate.return_value = {
        "passed": False,
        "checks": {"safety": False},
        "original_response": Response(content="test response")
    }
    
    # Create orchestrator
    orchestrator = Orchestrator(
        validator=validator,
        sla_router=sla_router,
        load_balancer=load_balancer,
        registry=module_registry,
        healing_controller=healing_controller,
        context_manager=context_manager,
        reasoning_engine=reasoning_engine,
        monitoring=monitoring
    )
    
    # Mock the retry method
    orchestrator._retry_with_stricter_llm = AsyncMock(return_value=Response(content="retry response"))
    
    # Test query
    query = Query(content="test query")
    response = await orchestrator.route_query(query)
    
    # Assertions
    assert response.content == "retry response"
    assert orchestrator._retry_with_stricter_llm.called

# tests/test_integrations/test_ollama.py
import pytest
from unittest.mock import Mock, patch
from core.integrations.ollama import Plugin

@pytest.mark.asyncio
async def test_ollama_plugin_initialization():
    """Test Ollama plugin initialization"""
    config = {
        "base_url": "http://localhost:11434",
        "default_model": "llama2",
        "batch_size": 4
    }
    
    plugin = Plugin(config)
    result = plugin.initialize()
    
    assert result is True
    assert plugin._initialized is True
    assert plugin.base_url == "http://localhost:11434"
    assert plugin.default_model == "llama2"

@pytest.mark.asyncio
async def test_ollama_plugin_execution():
    """Test Ollama plugin execution"""
    config = {
        "base_url": "http://localhost:11434",
        "default_model": "llama2",
        "batch_size": 4
    }
    
    plugin = Plugin(config)
    plugin.initialize()
    
    input_data = {"prompt": "test prompt", "max_tokens": 100}
    
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = {"response": "test response"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = plugin.execute(input_data)
        
        assert result["response"] == "test response"
        mock_post.assert_called_once()