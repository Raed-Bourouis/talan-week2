# Security Policy

## Supported Versions

This project is actively maintained. Security updates are applied to the latest version.

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |

## Security Updates

### Latest Security Patches (2024)

The following dependencies have been updated to address known vulnerabilities:

#### FastAPI - ReDoS Vulnerability
- **Issue**: Content-Type Header ReDoS vulnerability
- **Affected**: fastapi <= 0.109.0
- **Fixed**: Updated to fastapi==0.109.1
- **Severity**: Medium
- **Status**: ✅ Patched

#### python-multipart - Multiple Vulnerabilities
- **Issue 1**: Arbitrary File Write via Non-Default Configuration
- **Issue 2**: DoS via malformed multipart/form-data boundary
- **Issue 3**: Content-Type Header ReDoS
- **Affected**: python-multipart <= 0.0.6
- **Fixed**: Updated to python-multipart==0.0.22
- **Severity**: High
- **Status**: ✅ Patched

#### langchain-community - Multiple Vulnerabilities
- **Issue 1**: XML External Entity (XXE) Attacks
- **Issue 2**: SSRF vulnerability in RequestsToolkit
- **Issue 3**: Pickle deserialization of untrusted data
- **Affected**: langchain-community < 0.3.27
- **Fixed**: Updated to langchain-community==0.3.27
- **Severity**: High
- **Status**: ✅ Patched

## Security Best Practices

### For Production Deployment

1. **Authentication & Authorization**
   - Implement OAuth2 or JWT authentication
   - Add role-based access control (RBAC)
   - Use API keys for service-to-service communication

2. **Network Security**
   - Enable HTTPS/TLS for all endpoints
   - Configure proper CORS policies
   - Use firewall rules to restrict access
   - Disable debug mode in production

3. **Input Validation**
   - Validate all file uploads (type, size, content)
   - Sanitize all user inputs
   - Use Pydantic models for request validation
   - Implement rate limiting

4. **Data Protection**
   - Encrypt sensitive data at rest
   - Use secure environment variable management
   - Implement proper logging without exposing secrets
   - Regular backup of vector database

5. **Dependency Management**
   - Regularly update dependencies
   - Use `pip-audit` or `safety` to scan for vulnerabilities
   - Pin dependency versions in requirements.txt
   - Monitor security advisories

6. **Container Security**
   - Use minimal base images
   - Run containers as non-root users
   - Scan images for vulnerabilities
   - Keep Docker and dependencies updated

7. **LLM Security**
   - Sanitize prompts to prevent injection attacks
   - Implement output filtering
   - Set reasonable token limits
   - Monitor for abuse patterns

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **Do NOT** open a public issue
2. Email the maintainers directly at [security contact]
3. Provide detailed information:
   - Type of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work on a fix as quickly as possible.

## Security Checklist for Deployment

- [ ] Update all dependencies to latest secure versions
- [ ] Enable authentication and authorization
- [ ] Configure HTTPS/TLS
- [ ] Set up proper CORS policies
- [ ] Implement rate limiting
- [ ] Configure proper logging (without secrets)
- [ ] Use environment variables for sensitive config
- [ ] Disable debug mode
- [ ] Run containers as non-root
- [ ] Set up network segmentation
- [ ] Implement file upload restrictions
- [ ] Add input validation and sanitization
- [ ] Set up monitoring and alerting
- [ ] Regular security audits
- [ ] Backup strategy for data

## Dependency Scanning

### Manual Scanning

```bash
# Install security scanning tools
pip install pip-audit safety

# Scan with pip-audit
pip-audit -r requirements.txt

# Scan with safety
safety check -r requirements.txt
```

### Automated Scanning

Consider using:
- **Dependabot** (GitHub) - Automated dependency updates
- **Snyk** - Continuous security monitoring
- **GitHub Security Advisories** - Automated vulnerability alerts

## Known Limitations

### Current Security Considerations

1. **No Built-in Authentication**: The API does not include authentication by default. This is suitable for development but MUST be added for production.

2. **Local LLM**: Using Ollama means LLM inference happens locally, which is good for privacy but:
   - Requires proper access controls to the Ollama service
   - Monitor for resource exhaustion attacks

3. **File Upload**: Current implementation:
   - Has file size limits (10MB default)
   - Validates file extensions
   - Uses temporary files that are cleaned up
   - Consider adding: virus scanning, content validation

4. **Vector Database**: ChromaDB storage:
   - No built-in encryption at rest
   - Consider encrypting the volume in production
   - Implement access controls

## Updates Log

| Date       | Component              | Version | Security Issue                    |
|------------|------------------------|---------|-----------------------------------|
| 2024-02-17 | fastapi                | 0.109.1 | ReDoS vulnerability               |
| 2024-02-17 | python-multipart       | 0.0.22  | Multiple vulnerabilities          |
| 2024-02-17 | langchain-community    | 0.3.27  | XXE, SSRF, pickle deserialization |

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [FastAPI Security Guide](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

## License

This security policy is part of the project and follows the same MIT License.
