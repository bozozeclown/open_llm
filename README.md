# Open LLM Code Assistant

An AI-powered coding assistant with hybrid reasoning, self-learning capabilities, multi-LLM orchestration, and comprehensive enterprise features.

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

### Offline & Voice Support
- **Offline Mode** - Cache responses for use without internet connectivity
- **Voice Commands** - Natural language interaction with wake word detection
- **CLI Tool** - Command-line interface for all major features

### Enterprise Features
- **SSO Integration** - OAuth2 (Google, Microsoft, GitHub) and SAML 2.0 support
- **Team Management** - Role-based permissions, member invitation, resource sharing
- **Audit Logging** - Comprehensive compliance tracking with searchable audit trails
- **Enterprise Deployment** - Production-ready with high availability and monitoring

### Security & Reliability
- **Authentication & Authorization** - API key-based access and JWT tokens
- **Rate Limiting** - Advanced throttling with multiple strategies
- **Circuit Breakers** - Resilient error handling and failover
- **Health Monitoring** - Comprehensive system health checks
- **Performance Optimization** - Database optimization and caching

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Redis (for caching)
- PostgreSQL (for analytics and enterprise features)
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
# API Keys
export GROQ_API_KEY="your_groq_api_key"
export HF_API_KEY="your_huggingface_api_key"
export TEXTGEN_API_KEY="your_textgen_api_key"

# Database
export DATABASE_URL="postgresql://user:password@localhost:5432/openllm"
export REDIS_URL="redis://localhost:6379"

# Security
export SECRET_KEY="your_secret_key_here"
export JWT_SECRET="your_jwt_secret_here"

# Enterprise Features (optional)
export ENTERPRISE_ENABLED="true"
export SAML_IDP_METADATA_URL="your_idp_metadata_url"
```

### Docker Deployment
```bash
# Standard deployment
docker-compose up -d

# Enterprise deployment with all features
cd deploy/enterprise
docker-compose up -d

# Access the application
# Web Interface: http://localhost:8000
# Analytics Dashboard: http://localhost:8000/analytics/dashboard
# Grafana: http://localhost:3000
# Kibana: http://localhost:5601
```

## 📖 Usage

### Web Interface
Start the service:
```bash
python -m core.service
```

Access the web interface at `http://localhost:8000`

### CLI Tool
Install the CLI tool:
```bash
pip install -e .
```

Usage examples:
```bash
# Ask coding questions
openllm query "How to reverse a list in Python?"

# Analyze code files
openllm analyze -f my_code.py --language python --type refactor

# Create collaboration sessions
openllm session "My Session" --code "print('Hello World')" --language python

# Manage knowledge graph versions
openllm version create "Added optimization patterns"
openllm version list
```

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

### Voice Commands
Enable voice interaction:
```bash
# Start voice listening
curl -X POST http://localhost:8000/voice/command

# Say "Hey assistant, how do I reverse a list in Python?"
# The system will respond with voice and process your query

# Stop voice listening
curl -X POST http://localhost:8000/voice/stop
```

### Offline Mode
The system automatically caches responses for offline use:
```python
# Works without internet connection using cached responses
response = client.query("How to reverse a list in Python?")  # Returns cached response
```

## 📊 Analytics Dashboard

Access the comprehensive analytics dashboard at `http://localhost:8000/analytics/dashboard` to monitor:
- **Usage Statistics**: Request trends, active users, success rates
- **Performance Metrics**: Response times, latency distribution
- **User Analytics**: Activity patterns, top users
- **Code Quality Trends**: Language distribution, refactoring patterns
- **Enterprise Metrics**: Team activities, audit logs, compliance tracking

## 🔧 Configuration

### Environment Variables
```bash
# API Keys
GROQ_API_KEY="your_groq_api_key"
HF_API_KEY="your_huggingface_api_key"
TEXTGEN_API_KEY="your_textgen_api_key"

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/openllm"
REDIS_URL="redis://localhost:6379"

# Security
SECRET_KEY="your_secret_key_here"
JWT_SECRET="your_jwt_secret_here"

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# Enterprise Features
ENTERPRISE_ENABLED="true"
SAML_IDP_METADATA_URL="your_idp_metadata_url"
SP_ENTITY_ID="your_sp_entity_id"
SP_KEY_FILE="/path/to/sp_key.pem"
SP_CERT_FILE="/path/to/sp_cert.pem"
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

### Enterprise Configuration
```python
# Configure SSO providers
enterprise_config = {
    "oauth": {
        "google": {
            "enabled": true,
            "client_id": "your_google_client_id",
            "client_secret": "your_google_client_secret",
            "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo",
            "scopes": ["openid", "email", "profile"]
        },
        "microsoft": {
            "enabled": true,
            "client_id": "your_microsoft_client_id",
            "client_secret": "your_microsoft_client_secret",
            "user_info_url": "https://graph.microsoft.com/v1.0/me",
            "scopes": ["openid", "email", "profile"]
        }
    },
    "saml": {
        "enabled": true,
        "sp_entity_id": "https://your-domain.com/metadata",
        "acs_url": "https://your-domain.com/saml/acs",
        "idp_metadata_url": "https://your-idp.com/metadata",
        "sp_key_file": "/path/to/sp_key.pem",
        "sp_cert_file": "/path/to/sp_cert.pem"
    }
}
```

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
│   ├── analytics/             # Analytics dashboard
│   ├── collaboration/        # Real-time collaboration
│   ├── completion/            # Code completion
│   ├── context.py             # Context and knowledge management
│   ├── database/             # Database management
│   ├── debugging/            # Debugging tools
│   ├── enterprise/            # Enterprise features
│   │   ├── auth/             # Authentication (SSO, SAML)
│   │   ├── teams/            # Team management
│   │   └── audit/            # Audit logging
│   ├── errors/               # Error handling
│   ├── feedback/             # User feedback processing
│   ├── health.py             # Health monitoring
│   ├── integrations/         # LLM provider integrations
│   ├── interface.py          # API interface
│   ├── ml/                   # Machine learning
│   ├── multimodal/           # Multi-modal analysis
│   ├── offline/              # Offline support
│   ├── monitoring/           # Performance monitoring
│   ├── orchestration/        # Request orchestration
│   ├── orchestrator.py       # Main orchestrator
│   ├── performance/          # Performance optimization
│   ├── personalization/      # User personalization
│   ├── plugin.py             # Plugin system
│   ├── prediction/           # Predictive caching
│   ├── processing/           # Request processing
│   ├── reasoning/            # Reasoning engine
│   ├── refactoring/          # Code refactoring
│   ├── security/             # Security features
│   ├── self_healing.py       # Self-healing system
│   ├── self_learning/        # Self-learning capabilities
│   ├── service.py            # Main service entry point
│   ├── signature_help.py     # Code signature help
│   ├── state_manager.py      # Session state management
│   ├── testing/              # Test generation
│   ├── ux/                   # User experience
│   ├── validation/           # Response validation
│   ├── versioning/           # Knowledge versioning
│   └── voice/                # Voice support
├── deploy/                   # Deployment configuration
│   ├── docker/
│   │   └── docker-compose.yml
│   └── enterprise/
│       └── docker-compose.enterprise.yml
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
│   ├── knowledge/            # Knowledge graph
│   └── schemas.py            # Data schemas
├── static/                   # Static web assets
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript
│   └── templates/            # HTML templates
├── tests/                    # Test suite
│   ├── conftest.py
│   ├── integration/          # Integration tests
│   ├── performance/          # Performance tests
│   ├── enterprise/           # Enterprise tests
│   └── test_orchestrator.py
├── vscode-extension/          # VS Code extension
│   └── package.json
├── cli/                      # Command-line interface
│   ├── commands/
│   ├── config.py
│   └── main.py
├── mobile-app/               # React Native mobile app
│   ├── src/
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
- **Orchestrator**: Central query processing and routing with offline support
- **Integrations**: Plugin system for LLM providers (Ollama, vLLM, HuggingFace, etc.)
- **Context**: Knowledge graph management and interaction tracking
- **Analytics**: Real-time monitoring dashboard
- **Enterprise**: SSO, team management, audit logging, compliance
- **Offline**: Cache management for offline operation
- **Voice**: Speech recognition and synthesis
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

#### Enterprise Features (`core/enterprise/`)
- **Authentication**: OAuth2 and SAML 2.0 integration for enterprise SSO
- **Teams**: Role-based access control, member management, resource sharing
- **Audit**: Comprehensive compliance logging with searchable audit trails

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
python -c "from core.enterprise.auth import EnterpriseAuthManager; print('✅ Enterprise Auth OK')"
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
pytest tests/enterprise/

# Run with coverage
pytest --cov=core tests/

# Verify project consistency
python -c "from core.orchestrator import Orchestrator; print('✅ Orchestrator OK')"
python -c "from core.service import AIService; print('✅ Service OK')"
python -c "from modules.registry import ModuleRegistry; print('✅ Registry OK')"
python -c "from core.enterprise.auth import EnterpriseAuthManager; print('✅ Enterprise Auth OK')"
```

## 📈 Performance

The system is optimized for:
- **High Throughput**: 100+ requests per second
- **Low Latency**: <2s average response time
- **Memory Efficiency**: Optimized database queries and caching
- **Scalability**: Horizontal scaling with Docker and load balancing
- **Enterprise Ready**: High availability, audit compliance, team management

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
- [x] Add CLI tool for command-line usage
- [x] Implement offline mode capabilities
- [x] Add voice command support
- [x] Create mobile app structure (React Native)
- [x] Implement enterprise SSO integration (OAuth2, SAML)
- [x] Add team management and role-based permissions
- [x] Implement comprehensive audit logging and compliance
- [x] Create enterprise deployment templates

### 🚧 In Progress
- [ ] Add mobile app UI implementation
- [ ] Implement advanced AI capabilities (code generation from natural language)
- [ ] Add ecosystem integrations (GitHub, GitLab, Jira, Slack/Teams)

### 📋 Next Phase
- [ ] **Advanced AI Capabilities**
  - [ ] Implement automated test generation
  - [ ] Add bug prediction and prevention
  - [ ] Implement code documentation generation
- [ ] **Ecosystem Integration**
  - [ ] Integrate with GitHub/GitLab for seamless workflow
  - [ ] Add Jira integration for issue tracking
  - [ ] Create browser extension for web-based IDEs
- [ ] **Performance Enhancements**
  - [ ] Implement distributed caching cluster
  - [ ] Add horizontal scaling with Kubernetes
  - [ ] Implement edge caching for global users

## 🤝 Community

- **Documentation**: [Wiki](https://github.com/bozozeclown/open_llm/wiki)
- **Issues**: [GitHub Issues](https://github.com/bozozeclown/open_llm/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bozozeclown/open_llm/discussions)
- **Discord**: [Community Server](https://discord.gg/fTtyhu38)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- **Open Source Community**: For the amazing libraries and tools that make this project possible
- **Contributors**: Everyone who has helped shape this project
- **Early Adopters**: For providing valuable feedback and suggestions
- **Enterprise Partners**: For guidance on compliance and security requirements

---

**Built with ❤️ by the Open LLM community**