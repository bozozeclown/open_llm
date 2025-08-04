# Open LLM Code Assistant

An AI-powered coding assistant with hybrid reasoning, self-learning capabilities, and multi-LLM orchestration.

## ✨ Features

### Core Architecture
- **Hybrid Reasoning Engine** - Combines rule-based patterns, knowledge graphs, and LLMs
- **Multi-LLM Integration** - Supports Ollama, vLLM, HuggingFace, Grok, and more
- **Adaptive Routing** - Dynamic load balancing and SLA-aware prioritization
- **Self-Learning** - Improves from user feedback and corrections
- **Quality Gates** - Automated validation of all responses
- **Predictive Caching** - Anticipates and pre-computes likely queries

### Advanced Capabilities
- **Multi-Modal Code Analysis** - Extract and analyze code from images/screenshots
- **Advanced Refactoring Engine** - Intelligent code improvement suggestions
- **Real-time Collaboration** - Live coding sessions with multiple users
- **VS Code Extension** - Seamless IDE integration
- **Comprehensive Analytics Dashboard** - Real-time metrics and insights
- **ML Model Management** - Automated model updates and versioning
- **Knowledge Graph Versioning** - Track and restore knowledge graph states

### Security & Reliability
- **Authentication & Authorization** - API key-based access control
- **Rate Limiting** - Advanced throttling with multiple strategies
- **Circuit Breakers** - Resilient error handling and failover
- **Health Monitoring** - Comprehensive system health checks
- **Performance Optimization** - Database optimization and caching

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Redis (for caching)
- PostgreSQL (for analytics)
- Docker (optional, for containerized deployment)
- GPU (optional, for optimal performance with local models)

### Quick Start
```bash
git clone https://github.com/bozozeclown/open_llm.git
cd open_llm
pip install -r requirements.txt
```

### Configuration
1. Copy example configuration:
```bash
cp configs/integration.example.yaml configs/integration.yaml
```

2. Edit `configs/integration.yaml` to enable your preferred LLM providers:
```yaml
plugins:
  ollama:
    enabled: true
    config:
      base_url: "http://localhost:11434"
      default_model: "codellama"
  vllm:
    enabled: true
    config:
      model: "codellama/CodeLlama-7b-hf"
```

3. Set environment variables:
```bash
export GROQ_API_KEY="your_groq_api_key"
export HF_API_KEY="your_huggingface_api_key"
export TEXTGEN_API_KEY="your_textgen_api_key"
```

### Docker Deployment (Optional)
```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the application
# Web Interface: http://localhost:8000
# Analytics Dashboard: http://localhost:8000/analytics/dashboard
# Grafana: http://localhost:3000
```

## 📖 Usage

### Web Interface
Start the service:
```bash
python -m core.service
```

Access the web interface at `http://localhost:8000`

### API Usage
```python
from client import OpenLLMClient

client = OpenLLMClient()

# Basic code completion
response = client.query("How to reverse a list in Python?")
print(response.content)

# Code refactoring suggestions
suggestions = client.analyze_refactoring("your_code_here", "python")

# Multi-modal analysis
analysis = client.analyze_image("path/to/code/image.png")

# Real-time collaboration
session = client.create_session("My Coding Session", "print('Hello World')", "python")

# Knowledge graph versioning
version_id = client.create_version("Initial knowledge state")
restored = client.restore_version(version_id)
```

### VS Code Extension
1. Install the Open LLM Code Assistant extension from the VS Code marketplace
2. Configure your API endpoint in VS Code settings:
```json
{
  "open-llm.apiUrl": "http://localhost:8000",
  "open-llm.apiKey": "your_api_key"
}
```

### Keyboard Shortcuts
- `Ctrl+Shift+C` (Windows/Linux) / `Cmd+Shift+C` (Mac) - Get code suggestion
- `Ctrl+Shift+R` (Windows/Linux) / `Cmd+Shift+R` (Mac) - Analyze refactoring opportunities

## 📊 Analytics Dashboard

Access the comprehensive analytics dashboard at `http://localhost:8000/analytics/dashboard` to monitor:
- **Usage Statistics**: Request trends, active users, success rates
- **Performance Metrics**: Response times, latency distribution
- **User Analytics**: Activity patterns, top users
- **Code Quality Trends**: Language distribution, refactoring patterns

## 🔧 Configuration

### Environment Variables
```bash
# API Keys
GROQ_API_KEY="your_groq_api_key"
HF_API_KEY="your_huggingface_api_key"
TEXTGEN_API_KEY="your_textgen_api_key"

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/open_llm"
REDIS_URL="redis://localhost:6379"

# Security
SECRET_KEY="your_secret_key_here"
JWT_SECRET="your_jwt_secret_here"

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### Model Management
```python
from core.ml.model_manager import ModelManager

manager = ModelManager()

# Download and load models
await manager.download_model(ModelType.MULTIMODAL)
await manager.load_model(ModelType.MULTIMODAL)

# Check model status
model_info = manager.get_model_info(ModelType.MULTIMODAL)
print(f"Model status: {model_info.status}")
```

### Knowledge Graph Versioning
```python
from core.versioning import KnowledgeVersioner

versioner = KnowledgeVersioner(knowledge_graph)

# Create a version
version_id = versioner.create_version(
    description="Added Python optimization patterns",
    author="developer",
    tags=["python", "optimization"]
)

# List all versions
versions = versioner.list_versions()

# Restore to a previous version
success = versioner.restore_version(version_id)
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest --cov=core tests/

# Verify consistency
python -c "from core.orchestrator import Orchestrator; print('✅ Orchestrator imports correctly')"
python -c "from core.service import AIService; print('✅ Service imports correctly')"
python -c "from modules.registry import ModuleRegistry; print('✅ Module registry imports correctly')"
```

## 📈 Performance

The system is optimized for:
- **High Throughput**: 100+ requests per second
- **Low Latency**: <2s average response time
- **Memory Efficiency**: Optimized database queries and caching
- **Scalability**: Horizontal scaling with Docker and load balancing

## 🛠️ Development

### Project Structure
```
open_llm/
├── configs/                    # Configuration files
│   ├── base.yaml              # Base project configuration
│   ├── integration.yaml        # LLM provider integrations
│   ├── model.yaml             # Model management settings
│   ├── predictions.yaml       # Prediction caching settings
│   └── sla_tiers.yaml        # Service level agreements
├── core/                      # Core application logic
│   ├── analysis/              # Code analysis components
│   │   └── advanced_analyzer.py
│   ├── analytics/             # Analytics dashboard
│   │   └── dashboard.py
│   ├── collaboration/        # Real-time collaboration
│   │   └── session_manager.py
│   ├── completion/            # Code completion
│   │   └── intelligent_completer.py
│   ├── context.py             # Context and knowledge management
│   ├── database/             # Database management
│   │   └── optimized_manager.py
│   ├── debugging/            # Debugging tools
│   │   └── debugger.py
│   ├── errors/               # Error handling
│   │   ├── handlers.py
│   │   └── resilience.py
│   ├── feedback/             # User feedback processing
│   │   └── processor.py
│   ├── health.py             # Health monitoring
│   ├── integrations/         # LLM provider integrations
│   │   ├── __init__.py
│   │   ├── grok.py
│   │   ├── huggingface.py
│   │   ├── lmstudio.py
│   │   ├── manager.py
│   │   ├── ollama.py
│   │   ├── textgen.py
│   │   └── vllm.py
│   ├── interface.py          # API interface
│   ├── ml/                   # Machine learning
│   │   └── model_manager.py
│   ├── multimodal/           # Multi-modal analysis
│   │   └── image_analyzer.py
│   ├── monitoring/           # Performance monitoring
│   │   └── service.py
│   ├── orchestration/        # Request orchestration
│   │   ├── budget_router.py
│   │   ├── load_balancer.py
│   │   └── sla_router.py
│   ├── orchestrator.py       # Main orchestrator
│   ├── performance/          # Performance optimization
│   │   ├── cost.py
│   │   ├── hashing.py
│   │   ├── optimization.py
│   │   └── tracker.py
│   ├── personalization/      # User personalization
│   │   └── user_profile.py
│   ├── plugin.py             # Plugin system
│   ├── prediction/           # Predictive caching
│   │   ├── cache.py
│   │   └── warmer.py
│   ├── processing/           # Request processing
│   │   └── batcher.py
│   ├── reasoning/            # Reasoning engine
│   │   ├── engine.py
│   │   └── rules.py
│   ├── refactoring/          # Code refactoring
│   │   └── refactor_engine.py
│   ├── security/             # Security features
│   │   ├── auth.py
│   │   └── rate_limiter.py
│   ├── self_healing.py       # Self-healing system
│   ├── self_learning/        # Self-learning capabilities
│   │   ├── engine.py
│   │   └── rule_applier.py
│   ├── service.py            # Main service entry point
│   ├── signature_help.py     # Code signature help
│   ├── state_manager.py      # Session state management
│   ├── testing/              # Test generation
│   │   └── test_generator.py
│   ├── ux/                   # User experience
│   │   └── enhanced_error_handler.py
│   ├── validation/           # Response validation
│   │   └── quality_gates.py
│   └── versioning/           # Knowledge versioning
│       └── __init__.py
├── deploy/                   # Deployment configuration
│   └── docker/
│       └── docker-compose.yml
├── docs/                     # Documentation
│   └── DEVELOPER_GUIDE.md
├── modules/                  # Processing modules
│   ├── base_module.py
│   ├── module_ai.py
│   ├── module_completion.py
│   ├── module_debug.py
│   ├── module_generic.py
│   ├── module_python.py
│   ├── module_signature.py
│   └── registry.py
├── monitoring/               # Monitoring configuration
│   ├── alert_rules.yml
│   ├── dashboard.json
│   └── prometheus.yml
├── shared/                   # Shared components
│   ├── config/               # Configuration management
│   │   ├── init.py
│   │   └── loader.py
│   ├── knowledge/            # Knowledge graph
│   │   └── graph.py
│   └── schemas.py            # Data schemas
├── static/                   # Static web assets
│   ├── css/                  # Stylesheets
│   │   ├── debugger.css
│   │   ├── graph.css
│   │   └── signature.css
│   ├── js/                   # JavaScript
│   │   ├── completion.js
│   │   ├── debugger.js
│   │   ├── graph-explorer.js
│   │   └── signature.js
│   └── templates/            # HTML templates
│       └── index.html
├── tests/                    # Test suite
│   ├── conftest.py
│   ├── integration/          # Integration tests
│   │   ├── test_multimodal.py
│   │   ├── test_refactoring.py
│   │   └── test_collaboration.py
│   ├── performance/          # Performance tests
│   │   └── test_performance.py
│   └── test_orchestrator.py
├── vscode-extension/          # VS Code extension
│   └── package.json
├── .env                      # Environment variables
├── .gitignore               # Git ignore rules
├── package.json             # Node.js dependencies
├── README.md                 # This file
├── requirements.txt          # Python dependencies
└── webpack.config.js        # Webpack configuration
```

### Key Components

#### Core System (`core/`)
- **Orchestrator**: Central query processing and routing
- **Integrations**: Plugin system for LLM providers (Ollama, vLLM, HuggingFace, etc.)
- **Context**: Knowledge graph management and interaction tracking
- **Analytics**: Real-time monitoring dashboard
- **Collaboration**: Live coding session management
- **Multimodal**: Image-based code analysis
- **Refactoring**: Intelligent code improvement suggestions
- **Self-Learning**: System that improves from user interactions
- **Versioning**: Knowledge graph state management and restoration
- **Security**: Authentication, authorization, and rate limiting

#### Modules (`modules/`)
- Specialized processing units for different tasks (Python, debugging, completion, etc.)
- Extensible plugin architecture
- Registry for dynamic module discovery and loading

#### Configuration (`configs/`)
- Centralized configuration management
- Environment-specific settings
- SLA tiers and quality standards

### Contributing
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Start development server with hot reload
uvicorn core.service:app --reload

# Verify project consistency
python -c "from core.orchestrator import Orchestrator; print('✅ Orchestrator OK')"
python -c "from core.service import AIService; print('✅ Service OK')"
python -c "from modules.registry import ModuleRegistry; print('✅ Registry OK')"
```

## 📋 TO DO

### ✅ Completed
- [x] Implement core architecture and orchestration
- [x] Add multi-LLM integration support
- [x] Implement self-learning and feedback processing
- [x] Add quality gates and validation
- [x] Implement caching and performance optimization
- [x] Add comprehensive error handling
- [x] Implement security layer (authentication, authorization)
- [x] Add testing infrastructure
- [x] Implement Docker containerization
- [x] Add monitoring and alerting
- [x] Implement multi-modal code analysis
- [x] Add advanced refactoring suggestions
- [x] Implement real-time collaboration features
- [x] Create VS Code extension
- [x] Build comprehensive analytics dashboard
- [x] Implement ML model management system
- [x] Add performance testing and optimization
- [x] Implement advanced rate limiting
- [x] Add database optimization
- [x] Implement knowledge graph versioning system
- [x] Fix all import and naming inconsistencies
- [x] Ensure project-wide consistency

### 🚧 In Progress
- [ ] Add mobile app support (React Native)
- [ ] Implement offline mode capabilities
- [ ] Add voice command support
- [ ] Create CLI tool for command-line usage

### 📋 Next Phase
- [ ] **Enterprise Features**
  - [ ] Add SSO integration (OAuth2, SAML)
  - [ ] Implement team management and permissions
  - [ ] Add audit logging and compliance features
  - [ ] Create enterprise deployment templates
- [ ] **Advanced AI Capabilities**
  - [ ] Implement code generation from natural language specifications
  - [ ] Add automated test generation
  - [ ] Implement bug prediction and prevention
  - [ ] Add code documentation generation
- [ ] **Ecosystem Integration**
  - [ ] Integrate with GitHub/GitLab for seamless workflow
  - [ ] Add Jira integration for issue tracking
  - [ ] Implement Slack/Teams bot integration
  - [ ] Create browser extension for web-based IDEs

## 🤝 Community

- **Documentation**: [Wiki](https://github.com/bozozeclown/open_llm/wiki)
- **Issues**: [GitHub Issues](https://github.com/bozozeclown/open_llm/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bozozeclown/open_llm/discussions)
- **Discord**: [Community Server](https://discord.gg/5VEMNdsyYs)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- **Open Source Community**: For the amazing libraries and tools that make this project possible
- **Contributors**: Everyone who has helped shape this project
- **Early Adopters**: For providing valuable feedback and suggestions

---

**Built with ❤️ by the Open LLM community**