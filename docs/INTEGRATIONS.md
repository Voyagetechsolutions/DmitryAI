# Dmitry Integration Guide

## Overview

Dmitry supports integration with 20+ external security tools and platforms. This guide covers configuration and usage for each integration.

## SIEM Integrations

### Splunk

#### Configuration

```python
# MarkX/.env
SPLUNK_API_URL=https://splunk.company.com:8089
SPLUNK_API_KEY=your_splunk_token
SPLUNK_INDEX=security
```

#### Usage

```python
from modes.security_mode.integrations.siem.splunk import SplunkIntegration

splunk = SplunkIntegration()

# Search events
results = splunk.search(
    query='index=security sourcetype=firewall action=blocked',
    earliest_time='-24h'
)

# Forward alert
splunk.forward_alert({
    'severity': 'high',
    'title': 'Suspicious Activity Detected',
    'description': 'Multiple failed login attempts',
    'source_ip': '192.168.1.100'
})
```

### Elastic Security

#### Configuration

```python
# MarkX/.env
ELASTIC_API_URL=https://elastic.company.com:9200
ELASTIC_API_KEY=your_elastic_key
ELASTIC_INDEX=security-events
```

#### Usage

```python
from modes.security_mode.integrations.siem.elastic import ElasticIntegration

elastic = ElasticIntegration()

# Query events
events = elastic.query({
    'query': {
        'match': {
            'event.category': 'authentication'
        }
    },
    'size': 100
})

# Create detection rule
elastic.create_rule({
    'name': 'Brute Force Detection',
    'query': 'event.category:authentication AND event.outcome:failure',
    'threshold': 10,
    'window': '5m'
})
```

### Azure Sentinel

#### Configuration

```python
# MarkX/.env
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_WORKSPACE_ID=your_workspace_id
```

#### Usage

```python
from modes.security_mode.integrations.siem.sentinel import SentinelIntegration

sentinel = SentinelIntegration()

# Query incidents
incidents = sentinel.get_incidents(
    status='Active',
    severity=['High', 'Critical']
)

# Create incident
sentinel.create_incident({
    'title': 'Malware Detected',
    'severity': 'High',
    'description': 'Malicious file detected on endpoint'
})
```

## Threat Intelligence

### MISP

#### Configuration

```python
# MarkX/.env
MISP_URL=https://misp.company.com
MISP_API_KEY=your_misp_key
MISP_VERIFY_SSL=true
```

#### Usage

```python
from modes.security_mode.integrations.threat_intel.misp import MISPIntegration

misp = MISPIntegration()

# Search IOCs
iocs = misp.search_iocs(
    value='malicious.com',
    type='domain'
)

# Add IOC
misp.add_ioc({
    'type': 'ip-dst',
    'value': '192.168.1.100',
    'category': 'Network activity',
    'comment': 'C2 server'
})

# Get threat actor info
actor = misp.get_threat_actor('APT28')
```

### VirusTotal

#### Configuration

```python
# MarkX/.env
VIRUSTOTAL_API_KEY=your_vt_key
```

#### Usage

```python
from modes.security_mode.integrations.threat_intel.virustotal import VirusTotalIntegration

vt = VirusTotalIntegration()

# Scan file hash
report = vt.get_file_report('44d88612fea8a8f36de82e1278abb02f')

# Scan URL
url_report = vt.scan_url('https://suspicious-site.com')

# Get IP reputation
ip_report = vt.get_ip_report('192.168.1.100')
```

### AlienVault OTX

#### Configuration

```python
# MarkX/.env
OTX_API_KEY=your_otx_key
```

#### Usage

```python
from modes.security_mode.integrations.threat_intel.otx import OTXIntegration

otx = OTXIntegration()

# Get pulses
pulses = otx.get_pulses(
    tags=['malware', 'ransomware'],
    limit=10
)

# Get IOC details
ioc_details = otx.get_ioc_details('malicious.com', 'domain')
```

## Vulnerability Scanners

### Nessus

#### Configuration

```python
# MarkX/.env
NESSUS_URL=https://nessus.company.com:8834
NESSUS_ACCESS_KEY=your_access_key
NESSUS_SECRET_KEY=your_secret_key
```

#### Usage

```python
from modes.security_mode.integrations.vulnerability.nessus import NessusIntegration

nessus = NessusIntegration()

# Create scan
scan_id = nessus.create_scan({
    'name': 'Network Scan',
    'targets': ['192.168.1.0/24'],
    'template': 'basic'
})

# Launch scan
nessus.launch_scan(scan_id)

# Get results
results = nessus.get_scan_results(scan_id)
```

### OpenVAS

#### Configuration

```python
# MarkX/.env
OPENVAS_URL=https://openvas.company.com:9392
OPENVAS_USERNAME=admin
OPENVAS_PASSWORD=your_password
```

#### Usage

```python
from modes.security_mode.integrations.vulnerability.openvas import OpenVASIntegration

openvas = OpenVASIntegration()

# Create task
task_id = openvas.create_task({
    'name': 'Web App Scan',
    'target': 'example.com',
    'config': 'Full and fast'
})

# Start task
openvas.start_task(task_id)

# Get report
report = openvas.get_report(task_id)
```

### Qualys

#### Configuration

```python
# MarkX/.env
QUALYS_API_URL=https://qualysapi.company.com
QUALYS_USERNAME=your_username
QUALYS_PASSWORD=your_password
```

#### Usage

```python
from modes.security_mode.integrations.vulnerability.qualys import QualysIntegration

qualys = QualysIntegration()

# Launch scan
scan_ref = qualys.launch_scan({
    'scan_title': 'Infrastructure Scan',
    'ip': '192.168.1.0/24',
    'option_title': 'Initial Options'
})

# Get vulnerabilities
vulns = qualys.get_vulnerabilities(
    severity=['4', '5'],  # High and Critical
    status='Active'
)
```

## Cloud Security

### AWS Security Hub

#### Configuration

```python
# MarkX/.env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
```

#### Usage

```python
from modes.security_mode.integrations.cloud_security.aws_security_hub import AWSSecurityHub

aws_hub = AWSSecurityHub()

# Get findings
findings = aws_hub.get_findings(
    severity=['HIGH', 'CRITICAL'],
    workflow_status='NEW'
)

# Update finding
aws_hub.update_finding(
    finding_id='arn:aws:securityhub:...',
    workflow_status='RESOLVED',
    note='Fixed by patching'
)

# Get compliance status
compliance = aws_hub.get_compliance_status('cis-aws-foundations-benchmark')
```

### Azure Security Center

#### Configuration

```python
# MarkX/.env
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_SUBSCRIPTION_ID=your_subscription_id
```

#### Usage

```python
from modes.security_mode.integrations.cloud_security.azure_security import AzureSecurityCenter

azure_sec = AzureSecurityCenter()

# Get alerts
alerts = azure_sec.get_alerts(
    severity=['High', 'Medium'],
    status='Active'
)

# Get secure score
score = azure_sec.get_secure_score()

# Get recommendations
recommendations = azure_sec.get_recommendations(
    category='Compute'
)
```

### GCP Security Command Center

#### Configuration

```python
# MarkX/.env
GCP_PROJECT_ID=your_project_id
GCP_CREDENTIALS_PATH=/path/to/credentials.json
```

#### Usage

```python
from modes.security_mode.integrations.cloud_security.gcp_security import GCPSecurityCenter

gcp_sec = GCPSecurityCenter()

# List findings
findings = gcp_sec.list_findings(
    severity=['HIGH', 'CRITICAL'],
    state='ACTIVE'
)

# Get assets
assets = gcp_sec.list_assets(
    asset_type='compute.googleapis.com/Instance'
)

# Run security health analytics
analytics = gcp_sec.run_security_health_analytics()
```

## Integration Manager

### Check Integration Status

```python
from modes.security_mode.integrations import IntegrationManager

manager = IntegrationManager()

# Get all integrations
integrations = manager.get_all_integrations()

# Check specific integration
status = manager.get_integration_status('splunk')
print(f"Splunk: {status['status']}")  # connected/disconnected

# Test connection
result = manager.test_connection('splunk')
```

### Enable/Disable Integrations

```python
# Enable integration
manager.enable_integration('splunk')

# Disable integration
manager.disable_integration('splunk')

# Reload configuration
manager.reload_config()
```

## Best Practices

### 1. Credential Management

Store credentials securely:
```bash
# Use environment variables
export SPLUNK_API_KEY=$(vault read -field=key secret/splunk)

# Or use secrets management
kubectl create secret generic dmitry-integrations \
  --from-literal=splunk-key=$SPLUNK_KEY \
  --from-literal=elastic-key=$ELASTIC_KEY
```

### 2. Rate Limiting

Respect API rate limits:
```python
from time import sleep

for ioc in iocs:
    result = vt.get_file_report(ioc)
    sleep(15)  # VirusTotal: 4 requests/minute for free tier
```

### 3. Error Handling

Always handle integration errors:
```python
try:
    results = splunk.search(query)
except ConnectionError:
    logger.error("Splunk connection failed")
    # Fallback to local analysis
except RateLimitError:
    logger.warning("Rate limit exceeded, retrying...")
    sleep(60)
```

### 4. Caching

Cache results to reduce API calls:
```python
from core.cache import Cache

cache = Cache()

# Check cache first
cached = cache.get(f"vt_report_{file_hash}")
if cached:
    return cached

# Fetch and cache
report = vt.get_file_report(file_hash)
cache.set(f"vt_report_{file_hash}", report, ttl=3600)
```

### 5. Monitoring

Monitor integration health:
```python
from prometheus_client import Counter, Histogram

integration_calls = Counter('dmitry_integration_calls_total', 'Integration API calls', ['integration', 'status'])
integration_latency = Histogram('dmitry_integration_latency_seconds', 'Integration latency', ['integration'])

with integration_latency.labels(integration='splunk').time():
    result = splunk.search(query)
    integration_calls.labels(integration='splunk', status='success').inc()
```

## Troubleshooting

### Connection Issues

```python
# Test connectivity
import requests

response = requests.get(f"{SPLUNK_API_URL}/services/server/info", 
                       headers={'Authorization': f'Bearer {SPLUNK_API_KEY}'})
print(response.status_code)
```

### Authentication Failures

```bash
# Verify credentials
python -c "from modes.security_mode.integrations.siem.splunk import SplunkIntegration; s = SplunkIntegration(); print(s.test_connection())"
```

### API Errors

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For integration issues:
1. Check integration status in Integration Manager
2. Verify credentials in `.env`
3. Test connection manually
4. Review audit logs for errors
5. Check vendor API documentation
