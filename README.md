# 🚀 IEAP - Intelligent Enterprise Automation Platform

**Enterprise-grade AI-powered automation platform for intelligent decision making, ML model deployment, and autonomous business operations.**

This repository serves as a monorepo for the IEAP project, housing both the backend API and the frontend web application.

## 📂 Project Structure

- **[`backend/`](backend/)**: The core logic, including the FastAPI application, Machine Learning models, Celery workers, and automation pipelines.
- **[`frontend/`](frontend/)**: The modern web interface built with Next.js and Reactv18+.

## 🛠️ Quick Links

- [Backend Documentation](backend/README.md) - Detailed setup, API docs, and architecture.
- [Frontend Documentation](frontend/README.md) - Frontend setup and development guide.
- [Project Features](backend/docs/PRODUCTION_FEATURES.md) - Comprehensive list of production features.

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose** (Recommended)
- **PostgreSQL 15+**
- **Redis 7+**

### Running the Project (Docker)

1. Navigate to the `backend` directory (where the docker configuration resides):
   ```bash
   cd backend
   ```
2. Start the services:
   ```bash
   docker-compose up -d
   ```

### Running Locally

Please follow the specific instructions in each directory:

1. **Backend Setup**: See [`backend/README.md`](backend/README.md#option-2-local-development)
2. **Frontend Setup**: See [`frontend/README.md`](frontend/README.md#getting-started)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](backend/LICENSE) file for details.
