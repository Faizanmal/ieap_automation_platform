# IEAP Backend Examples and Reference Implementations

This directory contains reference implementations, tutorials, and alternative entry points for the Intelligent Enterprise Automation Platform (IEAP).

## Directory Structure

- **1_ml_model_deployment/**: Tutorial/Reference for ML model deployment.
- **2_automation_pipeline/**: Reference for the automation pipeline architecture.
- **3_nlp_ai_integration/**: NLP and AI integration examples.
- **4_analytics_dashboard/**: Dashboard backend reference code.

## Script Descriptions

### `ieap_main.py`
A standalone simulation script that acts as a "central command center". It initializes the orchestrator, ML hub, decision engine, and data pipeline in a single process loop. It runs a purely simulated environment without a web server.
**Usage**: `python examples/ieap_main.py` (Note: May require adjusting python path)

### `demo_platform.py`
A demonstration script showcasing specific platform capabilities.

### `app_production.py`
An advanced FastAPI application factory that includes additional features like GraphQL, WebSockets, and a Plugin System. This serves as a reference for a more complex production setup compared to the standard `api/main.py`.
