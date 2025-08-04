# docs/DEVELOPER_GUIDE.md

# Open LLM Code Assistant - Developer Guide

## Architecture Overview

The Open LLM Code Assistant is built with a modular architecture that separates concerns into distinct layers:

### Core Components

1. **Orchestration Layer** (`core/orchestrator.py`)
   - Main query processing pipeline
   - Routes requests to appropriate modules
   - Handles quality validation and response enhancement

2. **Integration Layer** (`core/integrations/`)
   - Plugin system for LLM providers
   - Supports multiple backends (Ollama, vLLM, HuggingFace, etc.)
   - Handles batching and rate limiting

3. **Context Management** (`core/context.py`)
   - Maintains knowledge graph
   - Tracks user interactions
   - Provides contextual information for queries

4. **Module System** (`modules/`)
   - Specialized processing modules
   - Language-specific functionality
   - Extensible plugin architecture

## Development Setup

### Prerequisites
- Python 3.8+
- Redis (for caching)
- GPU (for optimal performance with local models)

### Installation
```bash
git clone https://github.com/bozozeclown/open_llm.git
cd open_llm
pip install -r requirements.txt