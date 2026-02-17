# Contributing to GraphRAG

Thank you for your interest in contributing to GraphRAG! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/talan-week2.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Start services with Docker
docker-compose up -d

# Pull the LLM model
docker exec -it talan-week2-ollama-1 ollama pull llama3.1
```

## Code Style

We follow Python best practices:

- Use Black for code formatting: `black graphrag/`
- Use flake8 for linting: `flake8 graphrag/ --max-line-length=100`
- Write docstrings for all public functions and classes
- Add type hints where possible

## Testing

- Write tests for new features
- Ensure all tests pass: `pytest tests/`
- Aim for good test coverage

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (Add, Fix, Update, etc.)
- Keep the first line under 50 characters
- Add detailed description if needed

Example:
```
Add vector store caching functionality

- Implement Redis cache for embeddings
- Add TTL configuration
- Update tests
```

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update README.md if adding user-facing features
5. Create a pull request with a clear description

## Code Review

- Be respectful and constructive
- Respond to feedback promptly
- Make requested changes or explain why they're not needed

## Areas for Contribution

- New features
- Bug fixes
- Documentation improvements
- Performance optimizations
- Test coverage
- Examples and tutorials

## Questions?

Open an issue for discussion before starting work on major changes.

Thank you for contributing!
