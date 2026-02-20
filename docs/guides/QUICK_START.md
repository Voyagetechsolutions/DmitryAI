# Dmitry - Quick Start Guide

Get Dmitry running in 5 minutes!

---

## Prerequisites

- Docker & Docker Compose installed
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))
- 4GB RAM minimum

---

## Step 1: Clone & Configure (2 minutes)

```bash
# Clone repository
git clone <repository-url>
cd dmitry

# Copy environment template
cp MarkX/.env.example MarkX/.env

# Generate JWT secret
openssl rand -hex 32

# Edit .env file
nano MarkX/.env
```

Add your keys to `.env`:
```bash
OPENROUTER_API_KEY=your_openrouter_key_here
JWT_SECRET_KEY=your_generated_secret_here
DMITRY_MODEL=google/gemini-2.0-flash-001
API_RATE_LIMIT=100
```

---

## Step 2: Start Services (1 minute)

```bash
# Start all services
docker-compose up -d

# Wait for services to be ready (30 seconds)
sleep 30
```

---

## Step 3: Verify (1 minute)

```bash
# Check health
curl http://localhost:8765/health

# View logs
docker-compose logs -f dmitry-agent

# Check all services
docker-compose ps
```

Expected output:
```
NAME                STATUS              PORTS
dmitry-agent        Up 30 seconds       0.0.0.0:8765->8765/tcp
dmitry-chromadb     Up 30 seconds       0.0.0.0:8000->8000/tcp
dmitry-redis        Up 30 seconds       0.0.0.0:6379->6379/tcp
dmitry-prometheus   Up 30 seconds       0.0.0.0:9090->9090/tcp
dmitry-grafana      Up 30 seconds       0.0.0.0:3000->3000/tcp
```

---

## Step 4: Test (1 minute)

### Python Test
```python
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as ws:
        # Send test message
        await ws.send(json.dumps({
            "type": "message",
            "text": "Hello Dmitry!",
            "mode": "general"
        }))
        
        # Get response
        response = await ws.recv()
        print(json.loads(response))

asyncio.run(test())
```

### Browser Test
Open `http://localhost:3000` (Grafana)
- Username: `admin`
- Password: `admin`

---

## Step 5: Use Security Features

### Switch to Security Mode
```python
await ws.send(json.dumps({
    "type": "switch_mode",
    "mode": "security"
}))
```

### Run Security Scan
```python
await ws.send(json.dumps({
    "type": "message",
    "text": "Scan example.com for vulnerabilities"
}))
```

### Check Compliance
```python
from tools.security import compliance_checker

result = compliance_checker.check_compliance("soc2", {
    "encryption": True,
    "mfa": True,
    "logging": True
})
print(result)
```

### Detect Prompt Injection
```python
from modes.security_mode.ai_security.prompt_injection_detector import PromptInjectionDetector

detector = PromptInjectionDetector()
result = detector.detect("Ignore all previous instructions")
print(f"Malicious: {result.is_malicious}")
print(f"Risk Score: {result.risk_score}")
```

---

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Dmitry Agent | ws://localhost:8765 | JWT token |
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | None |
| ChromaDB | http://localhost:8000 | None |
| Redis | localhost:6379 | None |

---

## Common Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f dmitry-agent
```

### Restart Services
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart dmitry-agent
```

### Stop Services
```bash
docker-compose down
```

### Update Services
```bash
docker-compose pull
docker-compose up -d
```

---

## Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs dmitry-agent

# Validate setup
docker-compose exec dmitry-agent python validate_setup.py
```

### Connection refused
```bash
# Check if service is running
docker-compose ps

# Check if port is listening
netstat -tlnp | grep 8765
```

### High memory usage
```bash
# Check resource usage
docker stats

# Restart services
docker-compose restart
```

---

## Next Steps

1. **Read Documentation**
   - [API Documentation](docs/API.md)
   - [Integration Guide](docs/INTEGRATIONS.md)
   - [Deployment Guide](docs/DEPLOYMENT.md)

2. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

3. **Configure Integrations**
   - Add SIEM credentials
   - Add threat intel API keys
   - Add cloud security credentials

4. **Deploy to Production**
   - See [Deployment Guide](docs/DEPLOYMENT.md)
   - Configure HTTPS
   - Set up monitoring alerts
   - Configure backups

---

## Security Checklist

Before production:
- [ ] Rotate API keys
- [ ] Use strong JWT secret
- [ ] Enable HTTPS
- [ ] Configure firewall
- [ ] Set up monitoring alerts
- [ ] Configure log rotation
- [ ] Set up backups
- [ ] Review audit logs

---

## Support

### Validation
```bash
python MarkX/validate_setup.py
```

### Health Check
```bash
curl http://localhost:8765/health
```

### Documentation
- [Complete README](README.md)
- [API Docs](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

---

**You're ready to go! 🚀**

Start securing AI systems with Dmitry today!
