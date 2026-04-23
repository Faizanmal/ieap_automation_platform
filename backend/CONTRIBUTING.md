# Contributing to IEAP

Thank you for your interest in contributing to the Intelligent Enterprise Automation Platform! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

### Setting Up Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/your-username/ieap.git
cd ieap

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Start development services
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start the development server
uvicorn api.main:create_app --factory --reload
```

## Development Process

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Creating a Feature

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push branch
git push origin feature/your-feature-name
```

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(api): add batch prediction endpoint
fix(auth): resolve token refresh issue
docs(readme): update installation instructions
```

## Pull Request Process

1. Ensure all tests pass locally
2. Update documentation if needed
3. Add tests for new functionality
4. Fill out the PR template completely
5. Request review from maintainers
6. Address review feedback
7. Squash commits before merging

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Linked related issues

## Coding Standards

### Python Style Guide

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black default)
- Use docstrings for all public functions

### Code Quality Tools

```bash
# Format code
black .
isort .

# Lint
ruff check .
ruff check --fix .

# Type check
mypy .

# All checks at once
make lint
```

### Example Code Style

```python
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class PredictionResult:
    """Result of a model prediction.
    
    Attributes:
        prediction: The predicted value.
        confidence: Confidence score (0-1).
        features: List of feature importance scores.
    """
    prediction: float
    confidence: float
    features: Optional[List[float]] = None


async def make_prediction(
    model_id: str,
    input_data: dict,
    *,
    use_cache: bool = True
) -> PredictionResult:
    """Make a prediction using the specified model.
    
    Args:
        model_id: The unique identifier of the model.
        input_data: Input features for prediction.
        use_cache: Whether to use cached results.
    
    Returns:
        PredictionResult containing the prediction and metadata.
    
    Raises:
        ModelNotFoundError: If the model doesn't exist.
        ValidationError: If input_data is invalid.
    """
    # Implementation
    pass
```

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests
│   ├── test_security.py
│   └── test_models.py
├── integration/         # Integration tests
│   ├── test_api.py
│   └── test_database.py
└── e2e/                 # End-to-end tests
    └── test_workflows.py
```

### Writing Tests

```python
import pytest
from httpx import AsyncClient


class TestPredictionAPI:
    """Tests for prediction endpoints."""
    
    @pytest.mark.asyncio
    async def test_successful_prediction(
        self,
        client: AsyncClient,
        auth_token: str,
        test_model
    ):
        """Test making a successful prediction."""
        response = await client.post(
            "/api/v1/predictions",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "model_id": test_model.id,
                "input": {"feature": 1.0}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific markers
pytest -m unit
pytest -m integration

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## Documentation

### Updating Documentation

- Update docstrings for all public APIs
- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update API documentation (OpenAPI)

### Docstring Format

Use Google-style docstrings:

```python
def function(arg1: str, arg2: int) -> bool:
    """Short description.
    
    Longer description if needed.
    
    Args:
        arg1: Description of arg1.
        arg2: Description of arg2.
    
    Returns:
        Description of return value.
    
    Raises:
        ValueError: When arg1 is empty.
    
    Example:
        >>> function("test", 42)
        True
    """
```

## Questions?

Feel free to open an issue or reach out to the maintainers!
