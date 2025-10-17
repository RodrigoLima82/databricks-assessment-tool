#!/bin/bash

# Databricks Assessment Tool - Local Development Runner
# Starts both backend and frontend simultaneously

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

# PID tracking
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${BLUE}   Stopping backend (PID: $BACKEND_PID)${NC}"
        kill -TERM $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${BLUE}   Stopping frontend (PID: $FRONTEND_PID)${NC}"
        kill -TERM $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Wait a bit for graceful shutdown
    sleep 2
    
    # Force kill if still running
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        kill -9 $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        kill -9 $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
}

# Trap Ctrl+C and other termination signals
trap cleanup SIGINT SIGTERM EXIT

# Header
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║        🚀 DATABRICKS ASSESSMENT TOOL - LOCAL DEV 🚀               ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env exists
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo -e "${YELLOW}   Copy .env.example to .env and configure it${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Found .env file"

# Load environment variables from .env
set -a
source "${PROJECT_ROOT}/.env"
set +a

# Set default ports if not defined
BACKEND_PORT="${BACKEND_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-3002}"

# Check backend directory
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Error: Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Check frontend directory
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Error: Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📦 Starting Backend${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd "$BACKEND_DIR"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠  Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate

# Check if requirements are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠  Installing backend dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓${NC} Backend dependencies installed"
else
    echo -e "${GREEN}✓${NC} Backend dependencies already installed"
fi

# Start backend in background
echo -e "${BLUE}   Starting FastAPI server on port ${BACKEND_PORT}...${NC}"
python main.py > "${PROJECT_ROOT}/backend.log" 2>&1 &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start. Check backend.log for details${NC}"
    tail -20 "${PROJECT_ROOT}/backend.log"
    exit 1
fi

echo -e "${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"
echo -e "${GREEN}   → http://localhost:${BACKEND_PORT}${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎨 Starting Frontend${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

cd "$FRONTEND_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠  Node modules not found. Installing...${NC}"
    npm install
    echo -e "${GREEN}✓${NC} Frontend dependencies installed"
else
    echo -e "${GREEN}✓${NC} Frontend dependencies already installed"
fi

# Start frontend in background
echo -e "${BLUE}   Starting Vite dev server on port ${FRONTEND_PORT}...${NC}"
npm run dev > "${PROJECT_ROOT}/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Wait a bit for frontend to start
sleep 3

# Check if frontend is still running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Frontend failed to start. Check frontend.log for details${NC}"
    tail -20 "${PROJECT_ROOT}/frontend.log"
    cleanup
    exit 1
fi

echo -e "${GREEN}✓${NC} Frontend started (PID: $FRONTEND_PID)"
echo -e "${GREEN}   → http://localhost:${FRONTEND_PORT}${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Application is running!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "   ${GREEN}Backend:${NC}  http://localhost:${BACKEND_PORT}"
echo -e "   ${GREEN}Frontend:${NC} http://localhost:${FRONTEND_PORT}"
echo ""
echo -e "   ${YELLOW}Logs:${NC}"
echo -e "   - Backend:  ${PROJECT_ROOT}/backend.log"
echo -e "   - Frontend: ${PROJECT_ROOT}/frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

