# 🚀 FINCENTER Deployment Guide

## Overview

This guide covers deployment of FINCENTER from development to production environments. All components are 100% FREE and open-source.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements

#### Minimum (Development)
- CPU: 4 cores
- RAM: 8GB
- Disk: 30GB free space
- OS: Linux, macOS, or Windows with WSL2

#### Recommended (Production)
- CPU: 8+ cores
- RAM: 16GB+
- Disk: 100GB+ SSD
- OS: Ubuntu 22.04 LTS or similar

#### Optional (Performance)
- GPU: NVIDIA GPU with 8GB+ VRAM (3-5x faster inference)
- CUDA: 11.8+ for GPU acceleration

### Software Requirements

- Docker 24.0+
- Docker Compose 2.20+
- Git
- (Optional) NVIDIA Docker runtime for GPU support

## Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/Raed-Bourouis/talan-week2.git
cd talan-week2
```

### 2. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration if needed (defaults work fine)
nano .env
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# Watch model download progress (first time only)
docker logs -f fincenter-ollama-setup

# Once complete, verify all services
docker-compose ps
```

### 4. Access Applications

- **Dashboard**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j/fincenter123)
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### 5. Load Sample Data

```bash
# Load Neo4j schema and sample data
docker exec -it fincenter-neo4j cypher-shell -u neo4j -p fincenter123 -f /var/lib/neo4j/import/schema.cypher

# Verify data loaded
docker exec -it fincenter-neo4j cypher-shell -u neo4j -p fincenter123 "MATCH (n) RETURN labels(n), count(n)"
```

## Production Deployment

### Option 1: Single Server (Docker Compose)

#### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### 2. Production Configuration

```bash
# Clone repository
git clone https://github.com/Raed-Bourouis/talan-week2.git
cd talan-week2

# Create production environment
cp .env.example .env
nano .env  # Update passwords and settings

# Production docker-compose overrides
cat > docker-compose.prod.yml <<EOF
version: '3.8'

services:
  neo4j:
    restart: always
    environment:
      - NEO4J_AUTH=neo4j/STRONG_PASSWORD_HERE
  
  postgres:
    restart: always
    environment:
      - POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
  
  backend:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  
  dashboard:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
EOF
```

#### 3. Deploy

```bash
# Start services with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f
```

#### 4. Setup Reverse Proxy (Nginx)

```bash
# Install Nginx
sudo apt install nginx -y

# Configure Nginx
sudo cat > /etc/nginx/sites-available/fincenter <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/fincenter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. Setup SSL (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Option 2: Kubernetes Deployment

#### 1. Create Kubernetes Manifests

```bash
# Create namespace
kubectl create namespace fincenter

# Deploy StatefulSets for databases
kubectl apply -f k8s/neo4j-statefulset.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/qdrant-statefulset.yaml
kubectl apply -f k8s/redis-statefulset.yaml

# Deploy Ollama
kubectl apply -f k8s/ollama-deployment.yaml

# Deploy backend and dashboard
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/dashboard-deployment.yaml

# Create services
kubectl apply -f k8s/services.yaml

# Create ingress
kubectl apply -f k8s/ingress.yaml
```

#### 2. Horizontal Pod Autoscaling

```yaml
# backend-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: fincenter
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Cloud Deployment

### AWS Deployment

#### Using EC2

```bash
# Launch EC2 instance (t3.xlarge or larger)
# Follow single server deployment steps

# Configure security groups
# - Allow inbound: 80, 443, 8501, 8000
# - Allow outbound: all
```

#### Using ECS

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name fincenter

# Create task definitions for each service
# Deploy services to ECS

# Use EFS for persistent volumes
# Use RDS for PostgreSQL (optional)
```

### Google Cloud Platform

```bash
# Create GKE cluster
gcloud container clusters create fincenter \
    --machine-type n1-standard-4 \
    --num-nodes 3

# Deploy using Kubernetes manifests
kubectl apply -f k8s/
```

### Azure

```bash
# Create AKS cluster
az aks create \
    --resource-group fincenter \
    --name fincenter-cluster \
    --node-count 3 \
    --node-vm-size Standard_D4s_v3

# Deploy using Kubernetes manifests
kubectl apply -f k8s/
```

## GPU Support

### Enable GPU in Docker Compose

```yaml
# Add to ollama service in docker-compose.yml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Install NVIDIA Container Toolkit

```bash
# Install toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Verify
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

## Backup & Recovery

### Database Backups

```bash
# Neo4j backup
docker exec fincenter-neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-$(date +%Y%m%d).dump

# PostgreSQL backup
docker exec fincenter-postgres pg_dump -U fincenter fincenter > backup-$(date +%Y%m%d).sql

# Qdrant backup
curl -X POST http://localhost:6333/collections/financial_documents/snapshots
```

### Automated Backups

```bash
# Create backup script
cat > /opt/fincenter/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/backups/fincenter"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Neo4j
docker exec fincenter-neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-${DATE}.dump

# Backup PostgreSQL
docker exec fincenter-postgres pg_dump -U fincenter fincenter > $BACKUP_DIR/postgres-${DATE}.sql

# Backup Qdrant
curl -X POST http://localhost:6333/collections/financial_documents/snapshots

# Keep only last 7 days
find $BACKUP_DIR -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/fincenter/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/fincenter/backup.sh") | crontab -
```

## Monitoring & Maintenance

### Health Monitoring

```bash
# Check all services
curl http://localhost:8000/health

# Monitor logs
docker-compose logs -f --tail=100

# Check resource usage
docker stats
```

### Log Rotation

```yaml
# Add to all services in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Update Procedure

```bash
# Pull latest changes
git pull origin main

# Backup first!
./backup.sh

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Verify
docker-compose ps
curl http://localhost:8000/health
```

## Security Hardening

### 1. Change Default Passwords

```bash
# Update .env with strong passwords
NEO4J_PASSWORD=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

### 2. Enable Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Enable HTTPS

Already covered in SSL setup section.

### 4. Regular Updates

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d
```

## Performance Tuning

### Neo4j

```conf
# config/neo4j.conf
server.memory.heap.initial_size=2G
server.memory.heap.max_size=4G
server.memory.pagecache.size=2G
```

### PostgreSQL

```conf
# Add to docker-compose.yml postgres service
command: postgres -c shared_buffers=256MB -c max_connections=200
```

### Ollama

```yaml
# Use GPU for 3-5x speedup
# Or use smaller model for CPU
OLLAMA_MODEL=mistral:7b  # or phi3:3b
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check ports
sudo netstat -tulpn | grep -E ':(8000|8501|7474|6333|5432|6379|11434)'
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats

# Solutions:
# 1. Use smaller Ollama model (phi3:3b)
# 2. Increase swap space
# 3. Add more RAM
# 4. Reduce concurrent requests
```

### Slow Performance

```bash
# Check if using GPU
docker logs fincenter-ollama | grep -i gpu

# Enable GPU support (see GPU section)
# Or use smaller model

# Monitor bottlenecks
docker stats
```

### Models Won't Download

```bash
# Check Ollama logs
docker logs fincenter-ollama-setup

# Manual download
docker exec -it fincenter-ollama ollama pull llama3.1:8b

# Check disk space
df -h
```

## Cost Analysis

### Single Server (AWS EC2 t3.xlarge)
- Instance: ~$120/month
- Storage: ~$20/month  
- **Total: ~$140/month**
- **LLM API Costs: $0/month** ✨

### Comparison with API-based Solution
- OpenAI GPT-4: $0.03/1K tokens
- Average queries: 10K/day
- **Monthly API cost: $3000-5000**

**Savings with FINCENTER: ~$2860/month or $34,320/year** 🎉

## Conclusion

FINCENTER provides enterprise-grade financial intelligence at zero API costs. With proper deployment and maintenance, it offers:

- ✅ Complete data privacy
- ✅ Predictable costs
- ✅ Unlimited queries
- ✅ No vendor lock-in
- ✅ Full customization

For questions or support, refer to the [README](README.md) or open an issue on GitHub.
