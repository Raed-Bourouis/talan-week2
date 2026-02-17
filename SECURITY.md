# Security Notes

## Dependency Security Updates

This document tracks security vulnerabilities and their fixes in the GraphRAG system.

## Version 0.1.0 - Security Patches Applied

### Critical Vulnerabilities Fixed

#### 1. FastAPI ReDoS Vulnerability
- **Component**: FastAPI
- **Affected Version**: <= 0.109.0
- **Fixed Version**: 0.109.1
- **Vulnerability**: Duplicate Advisory: FastAPI Content-Type Header ReDoS
- **Severity**: Medium
- **Impact**: Regular expression denial of service (ReDoS) in Content-Type header parsing
- **Fix**: Updated to FastAPI 0.109.1

#### 2. Qdrant Client Input Validation
- **Component**: qdrant-client
- **Affected Version**: < 1.9.0
- **Fixed Version**: 1.9.0
- **Vulnerability**: Input validation failure
- **Severity**: Medium
- **Impact**: Improper input validation could lead to unexpected behavior
- **Fix**: Updated to qdrant-client 1.9.0

#### 3. PyTorch Heap Buffer Overflow
- **Component**: torch (PyTorch)
- **Affected Version**: < 2.2.0
- **Fixed Version**: 2.2.0
- **Vulnerability**: Heap buffer overflow vulnerability
- **Severity**: High
- **Impact**: Potential memory corruption and code execution
- **Fix**: Updated to torch 2.6.0

#### 4. PyTorch Use-After-Free
- **Component**: torch (PyTorch)
- **Affected Version**: < 2.2.0
- **Fixed Version**: 2.2.0
- **Vulnerability**: Use-after-free vulnerability
- **Severity**: High
- **Impact**: Potential memory corruption and code execution
- **Fix**: Updated to torch 2.6.0

#### 5. PyTorch Remote Code Execution
- **Component**: torch (PyTorch)
- **Affected Version**: < 2.6.0
- **Fixed Version**: 2.6.0
- **Vulnerability**: `torch.load` with `weights_only=True` leads to remote code execution
- **Severity**: Critical
- **Impact**: Remote code execution when loading untrusted model files
- **Fix**: Updated to torch 2.6.0
- **Additional Mitigation**: Always use `torch.load` with `weights_only=True` and only load trusted models

#### 6. PyTorch Deserialization (Withdrawn)
- **Component**: torch (PyTorch)
- **Affected Version**: <= 2.3.1
- **Status**: Withdrawn Advisory
- **Note**: Advisory withdrawn by maintainers, no patch available
- **Mitigation**: Using torch 2.6.0 which includes general security improvements

## Current Dependency Versions (Secure)

```
fastapi==0.109.1          # Patched
qdrant-client==1.9.0      # Patched
torch==2.6.0              # Patched (all known vulnerabilities)
neo4j==5.16.0             # No known vulnerabilities
redis==5.0.1              # No known vulnerabilities
sentence-transformers==2.3.1  # No known vulnerabilities
ollama==0.1.6             # No known vulnerabilities
```

## Security Best Practices

### 1. Dependency Management

**Current Practice**:
- All dependencies pinned to specific versions
- Regular security audits
- Immediate patching of vulnerabilities

**Recommendations**:
- Monitor security advisories for all dependencies
- Update dependencies regularly
- Use automated tools like Dependabot or Snyk

### 2. Model Loading Security

**Important**: PyTorch model loading can be dangerous with untrusted models.

**Safe Usage**:
```python
# SAFE: Use weights_only=True (with torch >= 2.6.0)
model = torch.load('model.pt', weights_only=True)

# UNSAFE: Loading arbitrary Python objects
model = torch.load('untrusted_model.pt')  # DON'T DO THIS
```

**Recommendations**:
- Only load models from trusted sources
- Use `weights_only=True` when loading models
- Verify model checksums
- Scan models for malicious code

### 3. API Security

**Current State**: No authentication (suitable for local development)

**Production Recommendations**:

1. **Add Authentication**:
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403)
```

2. **Add Rate Limiting**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/query")
@limiter.limit("10/minute")
async def query(request: Request, input_data: QueryInput):
    ...
```

3. **Enable HTTPS**:
```bash
uvicorn app:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

4. **Input Validation**:
- Already implemented via Pydantic models
- Additional validation in business logic

### 4. Database Security

**Neo4j**:
```yaml
# Production: Use strong passwords
NEO4J_AUTH=neo4j/strong_secure_password_here

# Enable encryption
NEO4J_dbms_connector_bolt_tls__level=REQUIRED
```

**Qdrant**:
```yaml
# Enable API key authentication
qdrant:
  environment:
    - QDRANT__SERVICE__API_KEY=your_secure_api_key
```

**Redis**:
```yaml
# Require password
redis:
  command: redis-server --requirepass your_secure_password
```

### 5. Network Security

**Docker Network Isolation**:
```yaml
# Current: All services on same network (suitable for local development)
# Production: Separate internal and external networks

networks:
  internal:
    internal: true
  external:

services:
  graphrag:
    networks:
      - external
      - internal
  
  neo4j:
    networks:
      - internal  # Not exposed externally
```

### 6. Data Security

**Current State**:
- All data processing is local
- No external API calls
- Data doesn't leave the system

**Additional Recommendations**:
- Encrypt volumes at rest
- Use encrypted connections between services
- Implement data retention policies
- Regular backups

## Vulnerability Scanning

### Automated Scanning

Use these tools to scan for vulnerabilities:

```bash
# pip-audit: Check Python dependencies
pip install pip-audit
pip-audit

# safety: Check for known security vulnerabilities
pip install safety
safety check

# bandit: Check code for common security issues
pip install bandit
bandit -r graphrag/

# trivy: Scan Docker images
trivy image graphrag:latest
```

### GitHub Security Features

Enable in repository settings:
- Dependabot alerts
- Dependabot security updates
- Code scanning (CodeQL)
- Secret scanning

## Security Incident Response

### If Vulnerability Discovered

1. **Assess Impact**: Determine affected components and severity
2. **Apply Patch**: Update to patched version immediately
3. **Test**: Verify patch doesn't break functionality
4. **Deploy**: Roll out update to all environments
5. **Document**: Update SECURITY.md and CHANGELOG.md
6. **Notify**: Inform users if necessary

### Contact

For security issues:
- Create a private security advisory on GitHub
- Email: [security contact if available]
- Don't disclose publicly until patched

## Security Checklist for Deployment

Before deploying to production:

- [ ] Update all dependencies to latest secure versions
- [ ] Enable authentication on API
- [ ] Enable authentication on all databases
- [ ] Use strong passwords (20+ characters)
- [ ] Enable HTTPS/TLS
- [ ] Set up rate limiting
- [ ] Configure firewalls
- [ ] Enable audit logging
- [ ] Set up monitoring and alerts
- [ ] Encrypt data at rest
- [ ] Encrypt data in transit
- [ ] Regular security scans
- [ ] Backup strategy in place
- [ ] Incident response plan documented

## Compliance

### Data Privacy

- **GDPR**: All processing local, user controls data
- **CCPA**: User data not shared with third parties
- **HIPAA**: Additional encryption may be needed for healthcare

### License Compliance

All dependencies use permissive licenses:
- MIT License: FastAPI, Pydantic, Redis
- Apache 2.0: PyTorch, Neo4j Community
- MIT/Apache 2.0: Qdrant

## Regular Security Maintenance

**Monthly**:
- Check for dependency updates
- Review security advisories
- Update to patched versions

**Quarterly**:
- Full security audit
- Penetration testing (production)
- Review access controls

**Annually**:
- Security architecture review
- Threat model update
- Compliance review

## References

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Neo4j Security](https://neo4j.com/docs/operations-manual/current/security/)
- [PyTorch Security](https://pytorch.org/docs/stable/notes/serialization.html)

## Version History

- **v0.1.0** (2024-02-17): Initial release with security patches applied
  - FastAPI 0.109.1
  - qdrant-client 1.9.0
  - torch 2.6.0

---

Last Updated: 2024-02-17
Next Review: 2024-03-17
