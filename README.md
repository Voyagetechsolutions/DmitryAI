# Dmitry - AI Risk Intelligence Platform

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)]()
[![Version](https://img.shields.io/badge/version-1.0.0-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Tests](https://img.shields.io/badge/tests-passing-success)]()

**The world's first AI assistant with built-in AI security and risk intelligence capabilities.**

---

## 🎯 What is Dmitry?

Dmitry is a production-ready AI Risk Intelligence platform that combines:
- **7 Cognitive Modes** for different tasks (Utility, General, Design, Developer, Research, Security, Simulation)
- **Enhanced Security Mode** with 7 specialized sub-modes for security operations
- **AI-Native Security** with prompt injection detection, model risk assessment, and OWASP LLM Top 10 coverage
- **20+ Security Integrations** (SIEM, threat intelligence, vulnerability scanners, cloud security)
- **Enterprise-Grade Features** (JWT auth, audit logging, rate limiting, monitoring)

---

## ✨ Key Features

### 🛡️ AI Security (First of Its Kind)
- **Prompt Injection Detection** - Real-time detection and blocking of malicious prompts
- **Model Risk Assessment** - Evaluate AI models for bias, fairness, and security risks
- **AI Security Auditing** - OWASP LLM Top 10 compliance checking
- **Adversarial Testing** - Test AI systems against jailbreak and manipulation attempts

### 🔐 Security Operations
- **Threat Hunting** - Proactive threat detection and analysis
- **Vulnerability Assessment** - Automated scanning and risk prioritization
- **Compliance Auditing** - SOC2, ISO27001, NIST, GDPR, HIPAA, PCI, CIS, GDPR
- **Incident Response** - Automated response workflows
- **Cloud Security** - AWS, Azure, GCP security posture management
- **Penetration Testing** - Security testing and validation

### 🔌 Integrations (20+)
- **SIEM**: Splunk, Elastic Security, Azure Sentinel
- **Threat Intel**: MISP, VirusTotal, AlienVault OTX
- **Vulnerability Scanners**: Nessus, OpenVAS, Qualys
- **Cloud Security**: AWS Security Hub, Azure Security Center, GCP Security Command Center

### 🏢 Enterprise Features
- **JWT Authentication** - Secure API access with token-based auth
- **Audit Logging** - Comprehensive logging of all actions
- **Rate Limiting** - Protect against abuse
- **Monitoring** - Prometheus metrics + Grafana dashboards
- **Scalability** - Horizontal scaling with load balancing

### 🧠 7 Cognitive Modes
1. **Utility Mode** - System operations and file management
2. **General Mode** - General conversation and queries
3. **Design Mode** - UI/UX design assistance
4. **Developer Mode** - Code development and debugging
5. **Research Mode** - Research and information gathering
6. **Security Mode** - Security operations (7 sub-modes)
7. **Simulation Mode** - Scenario simulation and modeling

---

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- OpenRouter API key

### 1. Clone Repository
```bash
git clone <repository-url>
cd dmitry
```

### 2. Configure Environment
```bash
cp MarkX/.env.example MarkX/.env
```

Edit `MarkX/.env`:
```bash
OPENROUTER_API_KEY=your_key_here
JWT_SECRET_KEY=$(openssl rand -hex 32)
```

### 3. Start Services
```bash
docker-compose up -d
```

### 4. Verify Deployment
```bash
# Check health
curl http://localhost:8765/health

# View logs
docker-compose logs -f dmitry-agent
```

### 5. Access Services
- **Dmitry Agent**: `ws://localhost:8765`
- **Grafana**: `http://localhost:3000` (admin/admin)
- **Prometheus**: `http://localhost:9090`

---

## 📖 Documentation

### Core Documentation
- [API Documentation](docs/API.md) - Complete API reference
- [Integration Guide](docs/INTEGRATIONS.md) - 20+ integration guides
- [Deployment Guide](docs/DEPLOYMENT.md) - Docker, K8s, AWS, Azure, GCP

### Implementation Journey
- [Findings & Analysis](FINDINGS.md) - Initial project analysis
- [Implementation Plan](IMPLEMENTATION_PLAN.md) - 12-week roadmap
- [Action Plan](ACTION_PLAN_100_PERCENT.md) - Detailed action items
- [Implementation Status](IMPLEMENTATION_STATUS.md) - Real-time progress
- [Completion Report](COMPLETION_100_PERCENT.md) - Final status

---

## 🔧 Usage Examples

### Python Client
```python
import asyncio
import websockets
import json

async def chat_with_dmitry():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as websocket:
        # Authenticate
        await websocket.send(json.dumps({
            "type": "auth",
            "token": "your_jwt_token"
        }))
        
        # Switch to Security Mode
        await websocket.send(json.dumps({
            "type": "switch_mode",
            "mode": "security"
        }))
        
        # Run security scan
        await websocket.send(json.dumps({
            "type": "message",
            "text": "Scan example.com for vulnerabilities"
        }))
        
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(chat_with_dmitry())
```

### Security Tools
```python
from tools.security import threat_intel_lookup, compliance_checker, ai_security_audit

# Lookup threat intelligence
result = threat_intel_lookup.lookup_ioc("suspicious-domain.com")

# Check compliance
compliance = compliance_checker.check_compliance("soc2", {
    "encryption": True,
    "mfa": True
})

# Audit AI model
audit = ai_security_audit.audit_model({
    "name": "my-model",
    "type": "llm"
})
```

---

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=MarkX --cov-report=html

# Run specific test file
pytest tests/test_prompt_injection.py -v
```

### Test Coverage
- Authentication tests
- Audit logging tests
- Prompt injection detection tests
- Security mode tests
- Security tools tests

---

## 📊 Monitoring

### Prometheus Metrics
Available at `http://localhost:8765/metrics`:
- `dmitry_requests_total` - Total requests
- `dmitry_request_duration_seconds` - Request latency
- `dmitry_active_sessions` - Active sessions
- `dmitry_tool_executions_total` - Tool executions
- `dmitry_security_events_total` - Security events

### Grafana Dashboards
Access at `http://localhost:3000`:
- System Overview
- Security Events
- API Performance
- Tool Usage

---

## 🔐 Security

### Built-in Security Features
- ✅ JWT authentication
- ✅ Rate limiting
- ✅ Audit logging
- ✅ Prompt injection detection
- ✅ Risk-based permissions
- ✅ Secure credential management
- ✅ HTTPS ready

### Security Best Practices
1. Rotate API keys regularly
2. Use strong JWT secrets
3. Enable HTTPS in production
4. Monitor audit logs
5. Keep dependencies updated
6. Run security scans regularly

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Dmitry Platform                       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Utility    │  │   General    │  │    Design    │  │
│  │     Mode     │  │     Mode     │  │     Mode     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Developer   │  │   Research   │  │  Simulation  │  │
│  │     Mode     │  │     Mode     │  │     Mode     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │         Enhanced Security Mode                   │    │
│  ├─────────────────────────────────────────────────┤    │
│  │ • Threat Hunting                                 │    │
│  │ • Vulnerability Assessment                       │    │
│  │ • AI Security Audit                              │    │
│  │ • Compliance Audit                               │    │
│  │ • Incident Response                              │    │
│  │ • Cloud Security Posture                         │    │
│  │ • Penetration Testing                            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
├─────────────────────────────────────────────────────────┤
│                   Core Services                          │
├─────────────────────────────────────────────────────────┤
│  • JWT Authentication    • Audit Logging                 │
│  • Rate Limiting         • Prompt Injection Detection    │
│  • Integration Manager   • Tool Registry                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🚢 Deployment

### Docker Compose (Recommended)
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

### Cloud Platforms
- **AWS ECS**: See [Deployment Guide](docs/DEPLOYMENT.md#aws-deployment)
- **Azure ACI**: See [Deployment Guide](docs/DEPLOYMENT.md#azure-deployment)
- **GCP Cloud Run**: See [Deployment Guide](docs/DEPLOYMENT.md#gcp-deployment)

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines.

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd dmitry

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r MarkX/requirements_production.txt
pip install pytest pytest-cov

# Run tests
pytest tests/ -v
```

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- OpenRouter for LLM API access
- ChromaDB for vector storage
- Prometheus & Grafana for monitoring
- All open-source security tools integrated

---

## 📞 Support

### Documentation
- [API Docs](docs/API.md)
- [Integration Guides](docs/INTEGRATIONS.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

### Validation
```bash
python MarkX/validate_setup.py
```

### Health Check
```bash
curl http://localhost:8765/health
```

### Logs
```bash
docker-compose logs -f dmitry-agent
```

---

## 🎯 Roadmap

### Completed ✅
- [x] 7 cognitive modes
- [x] Enhanced Security Mode
- [x] AI security features
- [x] 20+ integrations
- [x] Enterprise features
- [x] Testing infrastructure
- [x] Deployment automation
- [x] Complete documentation

### Future Enhancements
- [ ] Additional SIEM integrations
- [ ] More threat intelligence sources
- [ ] Advanced SOAR capabilities
- [ ] Machine learning for threat detection
- [ ] Mobile app
- [ ] Web UI enhancements

---

## 📊 Project Status

**Version**: 1.0.0  
**Status**: Production Ready  
**Completion**: 100%  
**Test Coverage**: 40+ test cases  
**Documentation**: Complete  

---

## 🏆 What Makes Dmitry Special

### 1. AI-Native Security
First AI assistant with built-in prompt injection detection, model risk assessment, and AI-specific security auditing.

### 2. Multi-Modal Intelligence
7 cognitive modes for different tasks, with Enhanced Security Mode as the integration hub.

### 3. Enterprise-Ready
JWT authentication, comprehensive audit logging, rate limiting, monitoring, and production deployment.

### 4. Open & Extensible
Clean architecture, well-documented APIs, easy integration, and customizable workflows.

---

**Built with ❤️ for the AI security community**

**Start securing AI systems today! 🚀**
