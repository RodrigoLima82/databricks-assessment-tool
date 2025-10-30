#!/bin/bash

# Databricks Assessment Tool - Universal Runner
# Works on Databricks clusters and local environments
# Auto-installs Terraform and all dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/databricks_app/backend"
FRONTEND_DIR="${PROJECT_ROOT}/databricks_app/frontend"

# Header
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║        🚀 DATABRICKS ASSESSMENT TOOL - LAUNCHER 🚀                 ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env exists
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    echo -e "${YELLOW}⚠  Warning: .env file not found${NC}"
    echo -e "${YELLOW}   Using environment variables from cluster${NC}"
else
    echo -e "${GREEN}✓${NC} Found .env file"
    # Load environment variables from .env
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Set default ports if not defined
BACKEND_PORT="${BACKEND_PORT:-8002}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 Installing Terraform + Provider${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Create Terraform directory
TERRAFORM_DIR="${PROJECT_ROOT}/.terraform/bin"
mkdir -p "$TERRAFORM_DIR"

# Detect architecture
ARCH=$(uname -m)
OS=$(uname -s | tr '[:upper:]' '[:lower:]')

case "$ARCH" in
    x86_64)
        TERRAFORM_ARCH="amd64"
        ;;
    aarch64|arm64)
        TERRAFORM_ARCH="arm64"
        ;;
    *)
        echo -e "${YELLOW}⚠  Unknown architecture: $ARCH, defaulting to amd64${NC}"
        TERRAFORM_ARCH="amd64"
        ;;
esac

# Terraform and Provider versions
TERRAFORM_VERSION="1.9.0"
PROVIDER_VERSION="1.95.0"  # Latest Databricks provider version

# Check if Terraform CLI is already installed
if [ -f "$TERRAFORM_DIR/terraform" ]; then
    INSTALLED_VERSION=$("$TERRAFORM_DIR/terraform" version -json 2>/dev/null | grep -o '"terraform_version":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    echo -e "${GREEN}✓${NC} Terraform CLI already installed (version: $INSTALLED_VERSION)"
else
    echo -e "${YELLOW}   Downloading Terraform CLI ${TERRAFORM_VERSION}...${NC}"
    TERRAFORM_URL="https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_${OS}_${TERRAFORM_ARCH}.zip"
    
    # Download and install Terraform CLI
    cd "$TERRAFORM_DIR"
    if command -v wget &> /dev/null; then
        wget -q "$TERRAFORM_URL" -O terraform.zip
    elif command -v curl &> /dev/null; then
        curl -sL "$TERRAFORM_URL" -o terraform.zip
    else
        echo -e "${RED}❌ Error: Neither wget nor curl is available${NC}"
        exit 1
    fi
    
    unzip -o terraform.zip > /dev/null 2>&1
    rm terraform.zip
    chmod +x terraform
    
    echo -e "${GREEN}✓${NC} Terraform CLI installed"
    cd "$PROJECT_ROOT"
fi

# Check if Databricks Provider is already installed
PLUGIN_DIR="${PROJECT_ROOT}/.terraform/plugins/registry.terraform.io/databricks/databricks/${PROVIDER_VERSION}/${OS}_${TERRAFORM_ARCH}"
if [ -d "$PLUGIN_DIR" ] && [ -n "$(ls -A "$PLUGIN_DIR" 2>/dev/null)" ]; then
    echo -e "${GREEN}✓${NC} Databricks Provider already installed (version: ${PROVIDER_VERSION})"
else
    echo -e "${YELLOW}   Downloading Databricks Provider ${PROVIDER_VERSION}...${NC}"
    PROVIDER_URL="https://github.com/databricks/terraform-provider-databricks/releases/download/v${PROVIDER_VERSION}/terraform-provider-databricks_${PROVIDER_VERSION}_${OS}_${TERRAFORM_ARCH}.zip"
    
    # Download and install Databricks Provider
    cd "$TERRAFORM_DIR"
    if command -v wget &> /dev/null; then
        wget -q "$PROVIDER_URL" -O provider.zip
    elif command -v curl &> /dev/null; then
        curl -sL "$PROVIDER_URL" -o provider.zip
    else
        echo -e "${RED}❌ Error: Neither wget nor curl is available${NC}"
        exit 1
    fi
    
    unzip -o provider.zip > /dev/null 2>&1
    rm provider.zip
    chmod +x terraform-provider-databricks*
    
    echo -e "${GREEN}✓${NC} Databricks Provider downloaded"
    
    # Create plugin directory structure for Terraform
    mkdir -p "$PLUGIN_DIR"
    cp terraform-provider-databricks* "$PLUGIN_DIR/"
    
    echo -e "${GREEN}✓${NC} Databricks Provider installed"
    cd "$PROJECT_ROOT"
fi

# Add Terraform to PATH for this session
export PATH="${TERRAFORM_DIR}:$PATH"
echo -e "${GREEN}✓${NC} Terraform added to PATH"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔧 Initializing Terraform${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd "$PROJECT_ROOT"

# Check if init.tf exists
if [ ! -f "${PROJECT_ROOT}/init.tf" ]; then
    echo -e "${RED}❌ init.tf not found in project root${NC}"
    echo -e "${YELLOW}   Expected at: ${PROJECT_ROOT}/init.tf${NC}"
    echo -e "${YELLOW}   Please ensure init.tf is committed to the repository${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} init.tf found"

# Check if already initialized
PROVIDER_PATH="${PROJECT_ROOT}/.terraform/providers/registry.terraform.io/databricks/databricks/${PROVIDER_VERSION}/linux_${TERRAFORM_ARCH}"
if [ -d "$PROVIDER_PATH" ] && [ -f "${PROVIDER_PATH}/terraform-provider-databricks_v${PROVIDER_VERSION}" ]; then
    echo -e "${GREEN}✓${NC} Terraform already initialized (provider found at correct location)"
else
    echo -e "${YELLOW}   Running terraform init...${NC}"
    echo -e "${YELLOW}   This may take a few minutes on first run...${NC}"
    
    # Run terraform init with full output for debugging
    terraform init -no-color 2>&1
    INIT_EXIT_CODE=$?
    
    if [ $INIT_EXIT_CODE -eq 0 ]; then
        
        # Verify provider was installed
        if [ -f "${PROVIDER_PATH}/terraform-provider-databricks_v${PROVIDER_VERSION}" ]; then
            echo -e "${GREEN}✓${NC} Terraform initialized successfully"
            echo -e "${GREEN}✓${NC} Provider installed at: ${PROVIDER_PATH}"
        else
            echo -e "${RED}❌ Provider not found after init${NC}"
            echo -e "${YELLOW}   Expected at: ${PROVIDER_PATH}${NC}"
            echo -e "${YELLOW}   Checking what was installed...${NC}"
            
            # List what's actually there
            if [ -d "${PROJECT_ROOT}/.terraform/providers" ]; then
                echo -e "${YELLOW}   Installed providers:${NC}"
                find "${PROJECT_ROOT}/.terraform/providers" -name "terraform-provider-*" 2>/dev/null || echo "   None found"
            fi
        fi
    fi
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 Installing Python Dependencies${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if requirements.txt exists
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${RED}❌ Error: requirements.txt not found${NC}"
    echo -e "${YELLOW}   Expected at: $REQUIREMENTS_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}   Upgrading pip...${NC}"
pip install --upgrade pip -q

echo -e "${YELLOW}   Installing dependencies (forcing binary wheels)...${NC}"
# Install dependencies one by one to avoid compilation issues
# Use --only-binary :all: to force pre-compiled wheels only (no compilation)

echo -e "${YELLOW}      → Core web framework...${NC}"
pip install -q --only-binary :all: fastapi uvicorn pydantic websockets python-multipart

echo -e "${YELLOW}      → Utilities...${NC}"
pip install -q --only-binary :all: requests pyyaml python-dotenv markdown

echo -e "${YELLOW}      → Data processing...${NC}"
pip install -q --only-binary :all: pandas openpyxl

echo -e "${YELLOW}      → PDF generation (pure Python)...${NC}"
pip install -q reportlab  # Pure Python, no compilation needed
# Note: Skipping xhtml2pdf to avoid cairo dependencies on Databricks
# PDF generation will use reportlab directly

echo -e "${GREEN}✓${NC} All dependencies installed"
echo -e "${BLUE}   • Web Framework: FastAPI + Uvicorn${NC}"
echo -e "${BLUE}   • PDF Generation: ReportLab (pure Python)${NC}"
echo -e "${BLUE}   • Terraform Export: Full support ✅${NC}"
echo -e "${BLUE}   • UCX Upload: Full support ✅${NC}"
echo -e "${BLUE}   • AI Agents: Pure HTTP (Databricks-native) ✅${NC}"

# Clean any .venv directories that might cause issues in /Workspace
echo -e "${YELLOW}   Cleaning virtual environment directories...${NC}"
rm -rf "${PROJECT_ROOT}/databricks_app/backend/venv" 2>/dev/null || true
rm -rf "${PROJECT_ROOT}/databricks_app/backend/ai_agent/.venv" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Environment cleaned"

cd "$BACKEND_DIR"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎨 Preparing Frontend${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

FRONTEND_DIST="${FRONTEND_DIR}/dist"
FRONTEND_ZIP="${FRONTEND_DIR}/dist.zip"

# Check if frontend dist exists
if [ -d "$FRONTEND_DIST" ] && [ -f "$FRONTEND_DIST/index.html" ]; then
    echo -e "${GREEN}✓${NC} Frontend dist/ found"
else
    # Try to extract from dist.zip
    if [ -f "$FRONTEND_ZIP" ]; then
        echo -e "${YELLOW}   Extracting frontend from dist.zip...${NC}"
        cd "$FRONTEND_DIR"
        unzip -o dist.zip > /dev/null 2>&1
        cd "$PROJECT_ROOT"
        
        if [ -f "$FRONTEND_DIST/index.html" ]; then
            echo -e "${GREEN}✓${NC} Frontend extracted successfully!"
        else
            echo -e "${RED}❌ Frontend extraction failed!${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Frontend not found!${NC}"
        echo -e "${YELLOW}   dist.zip is missing from the repository${NC}"
        echo -e "${YELLOW}   This should not happen - please check Git repository${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Starting Application!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "   ${GREEN}Application will be available at:${NC}"
echo -e "   ${GREEN}→ http://localhost:${BACKEND_PORT}${NC}"
echo ""
echo -e "   ${BLUE}Features:${NC}"
echo -e "   ✅ Terraform Export"
echo -e "   ✅ AI Agents Analysis" 
echo -e "   ✅ UCX Upload"
echo -e "   ✅ PDF Reports"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Set environment to prevent UV from creating venvs in /Workspace
export UV_NO_SYNC=1
export UV_SYSTEM_PYTHON=1
export VIRTUAL_ENV=""

# Start backend (which serves the frontend)
cd "${BACKEND_DIR}"
python main.py

