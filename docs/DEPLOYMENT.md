# Dmitry Deployment Guide

## Quick Start with Docker Compose

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### 1. Clone Repository

```bash
git clone <repository-url>
cd dmitry
```

### 2. Configure Environment

```bash
cp MarkX/.env.example MarkX/.env
```

Edit `MarkX/.env` and set:
```bash
OPENROUTER_API_KEY=your_key_here
JWT_SECRET_KEY=$(openssl rand -hex 32)
API_RATE_LIMIT=100
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Verify Deployment

```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f dmitry-agent

# Run health check
curl http://localhost:8765/health
```

### 5. Access Services

- Dmitry Agent: `ws://localhost:8765`
- Grafana: `http://localhost:3000` (admin/admin)
- Prometheus: `http://localhost:9090`
- ChromaDB: `http://localhost:8000`

## Production Deployment

### Kubernetes Deployment

#### 1. Create Namespace

```bash
kubectl create namespace dmitry
```

#### 2. Create Secrets

```bash
kubectl create secret generic dmitry-secrets \
  --from-literal=openrouter-api-key=your_key \
  --from-literal=jwt-secret=your_secret \
  -n dmitry
```

#### 3. Deploy Application

```yaml
# dmitry-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dmitry-agent
  namespace: dmitry
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dmitry-agent
  template:
    metadata:
      labels:
        app: dmitry-agent
    spec:
      containers:
      - name: dmitry
        image: your-registry/dmitry:latest
        ports:
        - containerPort: 8765
        env:
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: dmitry-secrets
              key: openrouter-api-key
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: dmitry-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8765
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8765
          initialDelaySeconds: 5
          periodSeconds: 5
```

Apply:
```bash
kubectl apply -f dmitry-deployment.yaml
```

#### 4. Create Service

```yaml
# dmitry-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: dmitry-agent
  namespace: dmitry
spec:
  selector:
    app: dmitry-agent
  ports:
  - protocol: TCP
    port: 8765
    targetPort: 8765
  type: LoadBalancer
```

Apply:
```bash
kubectl apply -f dmitry-service.yaml
```

### AWS Deployment

#### Using ECS Fargate

1. **Create ECR Repository**
```bash
aws ecr create-repository --repository-name dmitry
```

2. **Build and Push Image**
```bash
docker build -t dmitry .
docker tag dmitry:latest <account-id>.dkr.ecr.<region>.amazonaws.com/dmitry:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/dmitry:latest
```

3. **Create Task Definition**
```json
{
  "family": "dmitry-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "dmitry-agent",
      "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/dmitry:latest",
      "portMappings": [
        {
          "containerPort": 8765,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DMITRY_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENROUTER_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:dmitry/api-key"
        }
      ]
    }
  ]
}
```

4. **Create Service**
```bash
aws ecs create-service \
  --cluster dmitry-cluster \
  --service-name dmitry-service \
  --task-definition dmitry-task \
  --desired-count 2 \
  --launch-type FARGATE
```

### Azure Deployment

#### Using Azure Container Instances

```bash
az container create \
  --resource-group dmitry-rg \
  --name dmitry-agent \
  --image your-registry/dmitry:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8765 \
  --environment-variables \
    DMITRY_ENV=production \
  --secure-environment-variables \
    OPENROUTER_API_KEY=$API_KEY \
    JWT_SECRET_KEY=$JWT_SECRET
```

### GCP Deployment

#### Using Cloud Run

```bash
gcloud run deploy dmitry-agent \
  --image gcr.io/project-id/dmitry:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DMITRY_ENV=production \
  --set-secrets OPENROUTER_API_KEY=dmitry-api-key:latest
```

## Monitoring Setup

### Prometheus Configuration

Already configured in `prometheus.yml`. Metrics include:
- Request rates
- Response times
- Error rates
- Active sessions
- Tool executions

### Grafana Dashboards

1. **Access Grafana**: http://localhost:3000
2. **Login**: admin/admin
3. **Add Prometheus datasource**: http://prometheus:9090
4. **Import dashboards** from `grafana/dashboards/`

Key dashboards:
- System Overview
- Security Events
- API Performance
- Tool Usage

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up -d --scale dmitry-agent=3

# Kubernetes
kubectl scale deployment dmitry-agent --replicas=5 -n dmitry
```

### Load Balancing

Use nginx or cloud load balancer:

```nginx
upstream dmitry {
    least_conn;
    server dmitry-1:8765;
    server dmitry-2:8765;
    server dmitry-3:8765;
}

server {
    listen 80;
    location / {
        proxy_pass http://dmitry;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Backup and Recovery

### Backup Data

```bash
# Backup volumes
docker run --rm \
  -v dmitry_dmitry-memory:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/memory-$(date +%Y%m%d).tar.gz /data

# Backup ChromaDB
docker exec dmitry-chromadb tar czf /tmp/chroma-backup.tar.gz /chroma/chroma
docker cp dmitry-chromadb:/tmp/chroma-backup.tar.gz ./backups/
```

### Restore Data

```bash
# Restore memory
docker run --rm \
  -v dmitry_dmitry-memory:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/memory-20260217.tar.gz -C /

# Restore ChromaDB
docker cp ./backups/chroma-backup.tar.gz dmitry-chromadb:/tmp/
docker exec dmitry-chromadb tar xzf /tmp/chroma-backup.tar.gz -C /
```

## Security Hardening

### 1. Enable HTTPS

Use Let's Encrypt with certbot:

```bash
certbot certonly --standalone -d dmitry.yourdomain.com
```

Configure nginx with SSL:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/dmitry.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dmitry.yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://dmitry-agent:8765;
    }
}
```

### 2. Network Isolation

```yaml
# docker-compose.yml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

### 3. Resource Limits

```yaml
services:
  dmitry-agent:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 4. Security Scanning

```bash
# Scan image for vulnerabilities
trivy image your-registry/dmitry:latest

# Scan running containers
docker scan dmitry-agent
```

## Troubleshooting

### Common Issues

**Service won't start**
```bash
# Check logs
docker-compose logs dmitry-agent

# Verify environment
docker-compose exec dmitry-agent python validate_setup.py
```

**High memory usage**
```bash
# Check resource usage
docker stats

# Adjust memory limits in docker-compose.yml
```

**Connection refused**
```bash
# Check if service is listening
docker-compose exec dmitry-agent netstat -tlnp

# Verify firewall rules
sudo ufw status
```

### Health Checks

```bash
# API health
curl http://localhost:8765/health

# Prometheus metrics
curl http://localhost:8765/metrics

# Check all services
docker-compose ps
```

## Maintenance

### Update Deployment

```bash
# Pull latest image
docker-compose pull

# Restart services
docker-compose up -d

# Verify update
docker-compose logs -f dmitry-agent
```

### Log Rotation

Configure in `docker-compose.yml`:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Database Maintenance

```bash
# Vacuum ChromaDB
docker-compose exec chromadb chroma utils vacuum

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHDB
```

## Performance Tuning

### Optimize Python

```python
# Use uvloop for better async performance
pip install uvloop

# In main.py
import uvloop
uvloop.install()
```

### Optimize Redis

```bash
# Increase max memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 2gb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Optimize ChromaDB

```yaml
# In docker-compose.yml
chromadb:
  environment:
    - CHROMA_SERVER_THREAD_POOL_SIZE=10
```

## Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Run validation: `python validate_setup.py`
3. Review documentation
4. Check GitHub issues
