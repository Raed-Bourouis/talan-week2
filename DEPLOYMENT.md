# Production Deployment Guide

## Prerequisites

- Docker Swarm or Kubernetes cluster
- Load balancer (nginx, HAProxy, or cloud LB)
- SSL/TLS certificates
- Backup strategy
- Monitoring solution

## Environment Configuration

### Production .env

```bash
# OpenAI
OPENAI_API_KEY=<production-key>

# Secure Passwords (use strong, unique values)
NEO4J_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>

# Application
ENVIRONMENT=production
LOG_LEVEL=WARNING
API_BASE_URL=https://api.yourdomain.com

# Scaling
MAX_WORKERS=4
```

## Docker Compose Production

Update `docker-compose.yml` for production:

```yaml
services:
  api:
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        max_attempts: 3
    environment:
      - MAX_WORKERS=4
    healthcheck:
      interval: 30s
      timeout: 10s
      retries: 3
```

## Kubernetes Deployment

See `k8s/` directory for manifests:
- deployments.yaml
- services.yaml
- ingress.yaml
- configmaps.yaml
- secrets.yaml

## Security Hardening

1. **Enable Authentication**
   - Implement JWT tokens
   - Add API key validation
   - Set up OAuth2 if needed

2. **Network Security**
   - Use private networks
   - Enable firewalls
   - Restrict database access

3. **Secrets Management**
   - Use Docker secrets or Kubernetes secrets
   - Never commit credentials
   - Rotate passwords regularly

4. **SSL/TLS**
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       ...
   }
   ```

## Monitoring

### Health Checks
```bash
# Check system health every minute
*/1 * * * * curl -f https://api.yourdomain.com/health || alert
```

### Logging
- Centralized logging (ELK, Splunk, CloudWatch)
- Log retention policy
- Error alerting

### Metrics
- Prometheus + Grafana
- Custom dashboards
- Performance monitoring

## Backup Strategy

### Databases

**Neo4j:**
```bash
docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-backup.dump
```

**PostgreSQL:**
```bash
docker-compose exec postgres pg_dump -U fincenter fincenter > backup.sql
```

**Qdrant:**
```bash
# Backup data directory
tar -czf qdrant-backup.tar.gz /path/to/qdrant/storage
```

### Automation
```bash
# Daily backup cron job
0 2 * * * /path/to/backup-script.sh
```

## Scaling

### Horizontal Scaling
- Scale API containers: `docker-compose up --scale api=5`
- Load balance with nginx
- Session affinity via Redis

### Database Scaling
- Neo4j cluster mode
- PostgreSQL replication
- Qdrant distributed mode

## Disaster Recovery

1. **Regular backups** (daily recommended)
2. **Test restore procedures** monthly
3. **Document recovery steps**
4. **Maintain DR site** if critical

## Cost Optimization

- Right-size containers
- Use spot instances where appropriate
- Implement caching effectively
- Monitor resource usage
- Clean up old data

## Monitoring Checklist

- [ ] Health endpoint monitoring
- [ ] Database connection pool monitoring
- [ ] API response time tracking
- [ ] Error rate alerting
- [ ] Disk space monitoring
- [ ] Memory usage tracking
- [ ] CPU utilization monitoring

## Support

For production support:
- Check logs: `docker-compose logs -f`
- Health status: `curl /health`
- Database status via admin UIs
