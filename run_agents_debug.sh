#!/bin/bash

# ============================================================================
# 🚀 DATABRICKS ASSESSMENT - RUN AI AGENTS (DEBUG MODE)
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         🤖 DATABRICKS AI AGENTS - DEBUG MODE 🤖                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Load .env if exists
if [ -f .env ]; then
    echo -e "${GREEN}✓${NC} Loading .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Clean previous reports
echo -e "${YELLOW}🗑️  Cleaning previous reports...${NC}"
rm -f output_summary_agent/*.md
echo -e "${GREEN}✓${NC} Reports cleaned"

# Set agents to run (default: all 4)
AGENTS="${1:-terraform_reader,databricks_specialist,ucx_analyst,report_generator}"
export SELECTED_AGENTS="$AGENTS"

echo ""
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "   Agents: ${GREEN}$AGENTS${NC}"
echo -e "   TF Files: ${PROJECT_ROOT}/databricks_tf_files"
echo -e "   Output: ${PROJECT_ROOT}/output_summary_agent"
echo -e "   UCX Files: ${PROJECT_ROOT}/ucx_export"
echo ""

# Check if venv exists, if not create it
if [ ! -d "databricks_summary_agent/.venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found, creating...${NC}"
    cd databricks_summary_agent
    uv sync
    cd ..
fi

echo -e "${BLUE}🚀 Starting AI Agents Analysis...${NC}"
echo ""

# Run agents with debug output
cd databricks_summary_agent
uv run terraform_file_summary_agent run 2>&1 | tee "${PROJECT_ROOT}/agents_execution.log"

# Check results
cd "$PROJECT_ROOT"
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        📊 RESULTS                                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ -d "output_summary_agent" ]; then
    REPORT_COUNT=$(ls -1 output_summary_agent/*.md 2>/dev/null | wc -l | tr -d ' ')
    
    if [ "$REPORT_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ Reports generated: $REPORT_COUNT${NC}"
        echo ""
        
        for report in output_summary_agent/*.md; do
            if [ -f "$report" ]; then
                LINES=$(wc -l < "$report" | tr -d ' ')
                SIZE=$(ls -lh "$report" | awk '{print $5}')
                FILENAME=$(basename "$report")
                
                echo -e "${GREEN}✓${NC} ${FILENAME}"
                echo -e "   Lines: ${BLUE}${LINES}${NC} | Size: ${BLUE}${SIZE}${NC}"
            fi
        done
        
        echo ""
        echo -e "${GREEN}📄 Full log saved to:${NC} ${PROJECT_ROOT}/agents_execution.log"
        
    else
        echo -e "${RED}❌ No reports generated!${NC}"
        echo -e "${YELLOW}Check the log file for errors:${NC} ${PROJECT_ROOT}/agents_execution.log"
    fi
else
    echo -e "${RED}❌ Output directory not found!${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"

