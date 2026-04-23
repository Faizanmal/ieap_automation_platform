# 🚀 IEAP - Intelligent Enterprise Automation Platform

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)

**Enterprise-grade AI-powered automation platform for intelligent decision making, ML model deployment, and autonomous business operations.**

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Docs](#-api-documentation) • [Deployment](#-deployment)

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [Production Features](#-production-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Documentation](#-api-documentation)
- [Deployment](#-deployment)
- [Development](#-development)
- [Testing](#-testing)
- [Monitoring](#-monitoring)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🤖 Machine Learning
- **8+ Pre-built Models**: Anomaly detection, demand forecasting, churn prediction, sentiment analysis, and more
- **Model Registry**: Version control and lifecycle management for ML models
- **Auto-scaling Inference**: Batch and real-time predictions with automatic scaling
- **A/B Testing**: Built-in support for model experimentation

### 🔄 Automation
- **Multi-Agent Orchestrator**: Coordinate multiple AI agents for complex workflows
- **Decision Engine**: Autonomous decision-making with configurable approval workflows
- **Real-time Pipelines**: Stream processing for real-time data transformation
- **Task Queue**: Distributed task processing with Celery

### 🔒 Enterprise Security
- **JWT & OAuth2 Authentication**: Secure token-based authentication
- **Role-Based Access Control (RBAC)**: Fine-grained permission management
- **API Key Management**: Secure API access for external integrations
- **Audit Logging**: Complete audit trail for compliance
- **Data Encryption**: AES-256 encryption for sensitive data

### 📊 Observability
- **Prometheus Metrics**: Real-time performance monitoring
- **OpenTelemetry Tracing**: Distributed request tracing
- **Structured Logging**: JSON-formatted logs for easy analysis
- **Health Checks**: Kubernetes-ready liveness and readiness probes

### 🚢 Deployment
- **Docker & Kubernetes**: Production-ready containerization
- **Helm Charts**: Easy Kubernetes deployment
- **CI/CD Pipelines**: GitHub Actions for automated testing and deployment
- **Auto-scaling**: Horizontal Pod Autoscaler for elastic scaling

### 🛠️ Advanced Features
- **CLI Interface**: Professional command-line tools for platform management
- **GraphQL API**: Flexible query language for efficient data fetching
- **WebSocket Support**: Real-time bidirectional communication
- **Python SDK**: Easy integration with Python applications
- **Resilience Patterns**: Circuit breaker and retry mechanisms for fault tolerance
- **Batch Processing**: High-throughput batch job processing
- **Event System**: Asynchronous event-driven architecture
- **AI Explainability**: Model interpretation with SHAP and LIME
- **Rate Limiting**: Advanced rate limiting with Redis
- **Admin Dashboard API**: Administrative interfaces for monitoring and management
- **Health Aggregator**: Comprehensive health checks across all services
- **Plugin System**: Extensible architecture with hot-swappable plugins

---

## 🚀 Production Features

See [docs/PRODUCTION_FEATURES.md](docs/PRODUCTION_FEATURES.md) for complete documentation on all production features including CLI, GraphQL, WebSocket, SDK, Resilience, Batch Processing, Event System, AI Explainability, Rate Limiting, Admin Dashboard, Health Aggregator, and Plugin System.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           IEAP Architecture                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Web UI    │    │  REST API   │    │  Dashboard  │    │  Webhooks   │  │
│  │  (React)    │    │  (FastAPI)  │    │ (Streamlit) │    │  (Async)    │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                  │                  │                  │          │
│  ───────┴──────────────────┴──────────────────┴──────────────────┴───────   │
│                              API Gateway                                     │
│                    (Authentication, Rate Limiting, CORS)                    │
│  ────────────────────────────────────────────────────────────────────────   │
│                                    │                                         │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │             │
│  ┌──────▼──────┐           ┌───────▼──────┐          ┌───────▼──────┐      │
│  │   ML Model  │           │   Decision   │          │  Orchestrator│      │
│  │   Service   │           │    Engine    │          │   (Agents)   │      │
│  └──────┬──────┘           └───────┬──────┘          └───────┬──────┘      │
│         │                          │                          │             │
│  ───────┴──────────────────────────┴──────────────────────────┴───────      │
│                            Data Pipeline                                     │
│                      (Stream Processing, ETL)                               │
│  ────────────────────────────────────────────────────────────────────────   │
│                                    │                                         │
│    ┌───────────┐     ┌─────────────┼─────────────┐     ┌───────────┐       │
│    │           │     │             │             │     │           │       │
│ ┌──▼───┐  ┌────▼───┐ │  ┌──────────▼──────────┐  │  ┌──▼───┐  ┌────▼───┐  │
│ │Redis │  │Postgres│ │  │    Message Queue    │  │  │Model │  │ Object │  │
│ │Cache │  │   DB   │ │  │      (Celery)       │  │  │Store │  │ Store  │  │
│ └──────┘  └────────┘ │  └─────────────────────┘  │  └──────┘  └────────┘  │
│                      │                           │                          │
└──────────────────────┴───────────────────────────┴──────────────────────────┘
```

### Component Overview

| Component | Description | Technology |
|-----------|-------------|------------|
| API Gateway | Entry point for all requests | FastAPI |
| ML Service | Model training and inference | TensorFlow, PyTorch, scikit-learn |
| Decision Engine | Autonomous decision making | Custom rule engine |
| Orchestrator | Multi-agent coordination | Custom framework |
| Data Pipeline | Real-time data processing | Custom streaming |
| Task Queue | Background job processing | Celery + Redis |
| Database | Primary data store | PostgreSQL |
| Cache | Session and data caching | Redis |
| Monitoring | Metrics and tracing | Prometheus, Jaeger |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/ieap.git
cd ieap

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Access the API
open http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/ieap.git
cd ieap

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn api.main:create_app --factory --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A cache.celery_app:celery_app worker --loglevel=info

# Start the web frontend (optional)
cd frontend
npm install
npm run dev
```

### Option 3: One-Click Launch (Windows)

```bash
# Run both backend and frontend with a single command
./run_ieap.bat
```

## 🎨 Web Frontend

IEAP includes a modern React-based web interface for monitoring and managing the platform:

### Features
- **Real-time Dashboard**: System metrics, agent status, and task monitoring
- **Agent Management**: View and control AI agents
- **Task Monitoring**: Track task execution and performance
- **Analytics**: Interactive charts and insights
- **Settings**: Configure system parameters

### Access Points
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Frontend Tech Stack
- React 18 with TypeScript
- Tailwind CSS for styling
- Recharts for data visualization
- Vite for build tooling

### Running the Production Platform

```bash
# Run the full production-ready platform with all features
python app_production.py
```

### Using the CLI

```bash
# Install CLI dependencies (if not already installed)
pip install -e .

# Check platform health
python -m cli.main health

# List available models
python -m cli.main models list

# View help for more commands
python -m cli.main --help
```

### Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Get API docs
open http://localhost:8000/docs
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/staging/production) | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Required |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | `30` |
| `CORS_ORIGINS` | Allowed CORS origins | `["*"]` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENABLE_DOCS` | Enable API documentation | `true` |
| `OTLP_ENDPOINT` | OpenTelemetry collector endpoint | Optional |

### Feature Flags

Feature flags can be configured in `config/features.json`:

```json
{
  "new_prediction_engine": {
    "enabled": true,
    "percentage": 50
  },
  "beta_dashboard": {
    "enabled": true,
    "users": ["user1", "user2"]
  }
}
```

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **GraphQL Playground**: http://localhost:8000/graphql
- **WebSocket Endpoint**: ws://localhost:8000/ws

### Python SDK

The platform includes a Python SDK for easy integration:

```python
from sdk.client import IEAPClient

client = IEAPClient(base_url="http://localhost:8000")
# Use client for predictions, models, etc.
```

### Key Endpoints

#### Authentication
```http
POST /api/v1/auth/register    # Register new user
POST /api/v1/auth/login       # Login and get tokens
POST /api/v1/auth/refresh     # Refresh access token
POST /api/v1/auth/logout      # Logout and revoke tokens
```

#### ML Models
```http
GET    /api/v1/models              # List all models
POST   /api/v1/models              # Create new model
GET    /api/v1/models/{id}         # Get model details
PUT    /api/v1/models/{id}         # Update model
DELETE /api/v1/models/{id}         # Delete model
POST   /api/v1/models/{id}/train   # Start training
POST   /api/v1/models/{id}/deploy  # Deploy model
```

#### Predictions
```http
POST /api/v1/predictions           # Single prediction
POST /api/v1/predictions/batch     # Batch predictions
GET  /api/v1/predictions/{id}      # Get prediction result
```

#### Pipelines
```http
GET    /api/v1/pipelines           # List pipelines
POST   /api/v1/pipelines           # Create pipeline
POST   /api/v1/pipelines/{id}/run  # Execute pipeline
GET    /api/v1/pipelines/{id}/status  # Get pipeline status
```

### Example Request

```bash
# Get access token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Make a prediction
curl -X POST http://localhost:8000/api/v1/predictions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "anomaly-detector-v1",
    "input": {
      "feature1": 1.5,
      "feature2": 2.3,
      "feature3": 0.8
    }
  }'
```

---

## 🚢 Deployment

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -k k8s/overlays/production

# Check deployment status
kubectl get pods -n ieap

# View logs
kubectl logs -f deployment/ieap-api -n ieap
```

### Helm Chart

```bash
# Add Helm repository
helm repo add ieap https://charts.ieap.example.com

# Install
helm install ieap ieap/ieap \
  --namespace ieap \
  --create-namespace \
  --values values-production.yaml
```

### Production Checklist

- [ ] Set strong `JWT_SECRET_KEY` (256-bit random string)
- [ ] Configure `ENCRYPTION_KEY` for data encryption
- [ ] Set up PostgreSQL with SSL and connection pooling
- [ ] Configure Redis with authentication
- [ ] Set up TLS/SSL certificates
- [ ] Configure rate limiting
- [ ] Set up log aggregation (ELK, Loki)
- [ ] Configure alerting (PagerDuty, Slack)
- [ ] Enable database backups
- [ ] Set up monitoring dashboards

---

## 💻 Development

### Project Structure

```
ieap/
├── api/                    # FastAPI application
│   ├── main.py            # App factory
│   ├── middleware.py      # Custom middleware
│   ├── dependencies.py    # FastAPI dependencies
│   └── v1/                # API v1 endpoints
├── config/                 # Configuration management
├── security/               # Authentication & authorization
├── database/               # SQLAlchemy models & repositories
├── cache/                  # Redis & Celery
├── monitoring/             # Metrics, tracing, logging
├── ml_models/              # ML model implementations
├── decision_engine/        # Autonomous decision making
├── orchestrator/           # Multi-agent orchestration
├── data_pipeline/          # Data processing
├── tests/                  # Test suite
├── k8s/                    # Kubernetes manifests
├── deploy/                 # Deployment configs
└── scripts/                # Utility scripts
```

### Code Style

We use the following tools for code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Fast Python linting
- **MyPy**: Static type checking

```bash
# Format code
black .
isort .

# Lint
ruff check .

# Type check
mypy .
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_security.py

# Run integration tests only
pytest -m integration

# Run with verbose output
pytest -v
```

### Test Categories

- **Unit Tests** (`tests/unit/`): Fast, isolated tests
- **Integration Tests** (`tests/integration/`): Tests with external dependencies
- **E2E Tests** (`tests/e2e/`): Full workflow tests

---

## 📊 Monitoring

### Metrics

Access Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

Key metrics:
- `ieap_http_requests_total` - Total HTTP requests
- `ieap_model_predictions_total` - Total predictions
- `ieap_decision_confidence` - Decision confidence distribution
- `ieap_pipeline_records_total` - Pipeline records processed

### Grafana Dashboards

Pre-built dashboards available in `deploy/grafana/`:
- API Performance Dashboard
- ML Model Dashboard
- Pipeline Dashboard
- System Health Dashboard

### Distributed Tracing

Traces are exported to Jaeger:
- **Jaeger UI**: http://localhost:16686

---

## 🔒 Security

### Authentication Methods

1. **JWT Tokens**: For user authentication
2. **API Keys**: For service-to-service communication
3. **OAuth2**: For third-party integrations

### Security Best Practices

- All passwords hashed with Argon2
- JWT tokens expire after 30 minutes
- API keys can be scoped and rate-limited
- All sensitive data encrypted at rest
- Complete audit trail for compliance

### Reporting Vulnerabilities

Please report security vulnerabilities to security@ieap.example.com

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Documentation**: https://docs.ieap.example.com
- **Issues**: https://github.com/your-org/ieap/issues
- **Email**: support@ieap.example.com
- **Slack**: [#ieap-support](https://slack.ieap.example.com)

---

<div align="center">

Made with ❤️ by the IEAP Team

</div>
