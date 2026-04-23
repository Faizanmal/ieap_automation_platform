#!/usr/bin/env bash
#
# IEAP - Development Setup Script
#
# This script sets up the development environment:
# 1. Creates virtual environment
# 2. Installs dependencies
# 3. Sets up pre-commit hooks
# 4. Creates .env file from template
# 5. Runs database migrations
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "============================================================"
echo "  IEAP - Development Environment Setup"
echo "============================================================"
echo -e "${NC}"

# Get the script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command -v python3.11 &> /dev/null; then
    PYTHON=python3.11
elif command -v python3 &> /dev/null; then
    PYTHON=python3
else
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✓ Using Python $PYTHON_VERSION${NC}"

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    $PYTHON -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip wheel setuptools

# Install dependencies
echo -e "\n${YELLOW}Installing production dependencies...${NC}"
pip install -r requirements.txt

echo -e "\n${YELLOW}Installing development dependencies...${NC}"
pip install -r requirements-dev.txt

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Install pre-commit hooks
echo -e "\n${YELLOW}Setting up pre-commit hooks...${NC}"
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}⚠ pre-commit not found, skipping hook installation${NC}"
fi

# Create .env file
echo -e "\n${YELLOW}Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env from template${NC}"
        echo -e "${YELLOW}⚠ Don't forget to update .env with your actual values!${NC}"
    else
        echo -e "${YELLOW}⚠ .env.example not found, skipping .env creation${NC}"
    fi
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Generate secrets
echo -e "\n${YELLOW}Generating secrets (for reference)...${NC}"
if [ -f "scripts/generate_secrets.py" ]; then
    python scripts/generate_secrets.py > secrets_output.txt 2>&1
    echo -e "${GREEN}✓ Secrets generated in secrets_output.txt${NC}"
    echo -e "${YELLOW}⚠ Copy relevant values to your .env file${NC}"
fi

# Create necessary directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p logs
mkdir -p data
mkdir -p models
echo -e "${GREEN}✓ Directories created${NC}"

# Summary
echo -e "\n${GREEN}"
echo "============================================================"
echo "  Setup Complete!"
echo "============================================================"
echo -e "${NC}"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Update .env with your configuration"
echo ""
echo "  3. Start the development services:"
echo "     docker-compose up -d postgres redis"
echo ""
echo "  4. Run database migrations:"
echo "     alembic upgrade head"
echo ""
echo "  5. Start the development server:"
echo "     uvicorn api.main:app --reload"
echo ""
echo "  6. Open http://localhost:8000/docs for API docs"
echo ""
