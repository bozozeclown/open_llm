# Open LLM Code Assistant

An AI-powered coding assistant with hybrid reasoning, self-learning capabilities, and multi-LLM orchestration.

## Features

✅ **Hybrid Reasoning Engine** - Combines rule-based patterns, knowledge graphs, and LLMs  
✅ **Multi-LLM Integration** - Supports Ollama, vLLM, HuggingFace, Groq, and more  
✅ **Adaptive Routing** - Dynamic load balancing and SLA-aware prioritization  
✅ **Self-Learning** - Improves from user feedback and corrections  
✅ **Quality Gates** - Automated validation of all responses  
✅ **Predictive Caching** - Anticipates and pre-computes likely queries  

## Installation

```bash
git clone https://github.com/bozozeclown/open_llm.git
cd open_llm
pip install -r requirements.txt

# Configure your integrations
cp configs/integration.example.yaml configs/integration.yaml
Configuration
Edit configs/integration.yaml to enable your preferred LLM providers:

yaml
plugins:
  ollama:
    enabled: true
    config:
      base_url: "http://localhost:11434"
      default_model: "codellama"
Usage
Start the service:

bash
python -m core.service
Access the web interface at http://localhost:8000 or use the API:

python
from client import OpenLLMClient
client = OpenLLMClient()
response = client.query("How to reverse a list in Python?")


TO DO

Core Improvements

- Implement cross-provider benchmark testing
- Add automatic failover when providers go offline
- Develop prompt versioning system

Performance

- Optimize knowledge graph queries
- Add GPU memory monitoring for vLLM
- Implement query result compression

New Features

- Add multi-modal support (images + code)
- Develop VS Code extension
- Create collaboration history replay

Documentation

- Write API usage examples
- Create architecture diagrams
- Add developer onboarding guide

Maintenance

- Upgrade to Pydantic v2
- Add integration test suite
- Set up CI/CD pipeline

Contributing

- Fork the repository
- Create a feature branch (git checkout -b feature/your-feature)
- Commit your changes
- Push to the branch
- Open a pull request

License
MIT License - See LICENSE for details.