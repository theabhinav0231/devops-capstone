# CloudLedger — End-to-End DevOps Automation Platform (ENSP461 Capstone)

**Student:** Abhinav Kumar (`2301730191`)  
**Repository:** https://github.com/theabhinav0231/devops-capstone  
**Domain Application:** CloudLedger — FinTech Payment & Transaction Ledger Microservice  
**Environment:** Ubuntu 24.04 LTS (WSL2) | Docker | Kubernetes (Minikube) | Terraform | Ansible | Prometheus | HashiCorp Vault | Trivy

## 1. Platform Architecture

```
Git Push (main)
   │
   ▼
CI/CD Pipeline (Jenkinsfile / GitHub Actions)
   ├── Gate 1: pytest Unit & Integration Suites (JUnit XML)
   ├── Gate 2: Hardened Non-Root Docker Build
   ├── Gate 3: Trivy IaC & Container Vulnerability Scan
   └── Gate 4: HashiCorp Vault KV v2 Secret Sync (Zero Plaintext)
   │
   ▼
Infrastructure Automation (Terraform + Idempotent Ansible)
   │
   ▼
Kubernetes Orchestration (Minikube namespace: capstone-abhinav)
   ├── Stable (v1.0.0) + Canary (v1.1.0) Weighted Rollout & Auto-Rollback
   ├── HPA + NetworkPolicy + Liveness/Readiness Probes
   └── GitOps Reconciler (Git SSOT Drift Self-Healing)
   │
   ▼
Observability & Resilience
   ├── Prometheus /metrics + SLO Alert Rules + Grafana Dashboard
   ├── Structured JSON Logs + Logstash Pipeline
   └── Online SQLite Backup + SHA-256 Restore & Failover (RPO=0)
```

## 2. Repository Layout

| Path | Purpose |
|---|---|
| `app/` | CloudLedger Flask microservice (`/health`, `/ready`, `/api/transactions`, `/metrics`, JSON logging) |
| `tests/` | Automated unit (`test_unit.py`) and SQLite DR integration (`test_integration.py`) CI gates |
| `Dockerfile`, `docker-compose.yml` | Hardened non-root container image and local observability Compose stack |
| `Jenkinsfile`, `.github/workflows/ci-cd.yml` | Multi-stage CI/CD pipelines with test, security, and rollout gates |
| `infra/terraform/`, `infra/ansible/` | Terraform IaC and idempotent Ansible host provisioning playbook |
| `k8s/` | Namespace, ConfigMap, Secret, Stable/Canary Deployments, Services, HPA, NetworkPolicy |
| `monitoring/`, `logging/` | Prometheus scrape & alert rules, Grafana dashboard JSON, Logstash config |
| `security/` | HashiCorp Vault least-privilege HCL policy and K8s secret sync script |
| `ops/`, `dr/` | GitOps drift reconciler and SHA-256 verified backup/restore/failover scripts |
| `docs/logs/`, `docs/screenshots/` | Captured live execution logs and rendered terminal evidence |

## 3. Quick Execution Steps

```bash
# 1. Automated CI Test Gates
python3 -m venv .venv && .venv/bin/pip install -r app/requirements.txt pytest
PYTHONPATH=. .venv/bin/pytest tests/ -v --junitxml=docs/logs/junit.xml

# 2. Container Build & Security Scan
docker build --build-arg APP_VERSION=1.0.0 -t cloudledger-app:1.0.0 .
docker build --build-arg APP_VERSION=1.1.0 -t cloudledger-app:1.1.0 .
trivy config k8s/
trivy image --severity HIGH,CRITICAL --ignore-unfixed cloudledger-app:1.1.0

# 3. Infrastructure Automation
(cd infra/terraform && terraform init && terraform apply -auto-approve)
ansible-playbook -i infra/ansible/inventory.ini infra/ansible/site.yml

# 4. Kubernetes Orchestration, Canary & GitOps
kubectl apply -f k8s/
bash ops/gitops_reconciler.sh
```
