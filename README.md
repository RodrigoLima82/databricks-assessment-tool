# Databricks Assessment Tool

Automated infrastructure analysis for Databricks using Terraform Export + AI-powered insights.

![Version](https://img.shields.io/badge/version-2.0.0-blue) ![Python](https://img.shields.io/badge/python-3.11+-blue) ![React](https://img.shields.io/badge/react-18-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)

---

## Overview

Web-based tool for comprehensive Databricks infrastructure assessment:

- **Export** complete Databricks workspace to Terraform (31+ resource types)
- **Analyze** infrastructure using AI (Claude 4.5 Sonnet via Databricks Model Serving)
- **Generate** technical and executive reports in PT-BR
- **Export** reports as Markdown, HTML or PDF

### Key Features

✅ Modern React UI with Material-UI  
✅ FastAPI backend with real-time WebSocket feedback  
✅ Terraform export (Databricks Provider v1.95.0)  
✅ AI analysis
✅ Interactive HTML reports with browser-based PDF export  
✅ Full support for Databricks cluster execution  

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend build)
- Databricks workspace with Model Serving endpoint

### 1. Clone & Configure

```bash
git clone <repository-url>
cd databricks-assessment-tool

# Create .env file
cat > .env << EOF
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
DATABRICKS_ENDPOINT=/serving-endpoints/databricks-claude-sonnet-4-5/invocations
EOF
```

### 2. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies (single file!)
pip install -r requirements.txt
```

### 3. Run Locally

```bash
# Option 1: Python launcher (simple, recommended for local dev)
python run_app.py

# Option 2: Bash launcher (full-featured, auto-installs everything)
bash run_app.sh

# Option 3: Manual
cd databricks_app/backend
uvicorn main:app --reload --port 8000
```

Access: `http://localhost:8000`

### 4. Run on Databricks Cluster

**Upload project to Databricks workspace:**
```bash
# Compress project (frontend already built and included as dist.zip)
zip -r databricks-assessment-tool.zip . -x "*.git*" "*node_modules*" "*venv*" "*__pycache__*"

# Upload via Databricks CLI or UI
databricks workspace import databricks-assessment-tool.zip /Workspace/Users/your.email/databricks-assessment-tool --format AUTO
```

**In cluster terminal:**
```bash
cd /Workspace/Users/your.email/databricks-assessment-tool
bash run_app.sh
```

> **Note:** Frontend is pre-built and included as `databricks_app/frontend/dist.zip`. The script automatically extracts it on first run. No Node.js required on cluster!

**Access via Driver Proxy:**
```
https://your-workspace.cloud.databricks.com/driver-proxy/o/<workspace-id>/<cluster-id>/8000/
```

---

## Architecture

```
Frontend (React + MUI)
    ↓ REST API
Backend (FastAPI)
    ↓
    ├── Terraform Export → .tf files
    └── AI Analysis → Reports
            ↓ HTTP
        Databricks Model Serving (Claude 4.5)
```

### Project Structure

```
databricks-assessment-tool/
├── databricks_app/
│   ├── backend/              # FastAPI server
│   │   ├── main.py           # API endpoints
│   │   ├── executors.py      # Execution logic
│   │   ├── pdf_generator.py  # PDF generation
│   │   └── ai_agent/         # AI Analysis (simplified)
│   │       ├── agent.py      # SimpleDatabricksAgent
│   │       └── prompts.json  # Multilingual prompts
│   └── frontend/             # React app
│       └── src/
│           └── components/
├── run_app.py               # Python launcher (simple, local dev)
└── run_app.sh               # Universal launcher (Databricks + local)
```

---

## Usage

1. **Configure Databricks credentials** in `.env`
2. **Launch application** (locally or on Databricks)
3. **Step 1:** Configure Terraform export parameters
4. **Step 2:** Select AI agents (default: all enabled)
5. **Step 3:** (Optional) Upload UCX assessment files
6. **Step 4:** Execute analysis
7. **Step 5:** View and export reports

### Export Formats

- **Markdown (.md)** - Source format, editable
- **HTML (.html)** - Interactive report with emojis, includes "Export to PDF" button
- **PDF (.pdf)** - Professional format for distribution

**Recommended workflow:**
1. Download HTML report
2. Open in browser
3. Click "📄 Export to PDF" button for best rendering

---

## Configuration

### Environment Variables (.env)

```bash
# Required
DATABRICKS_HOST=https://adb-123456789.azuredatabricks.net
DATABRICKS_TOKEN=dapi...
DATABRICKS_ENDPOINT=/serving-endpoints/databricks-claude-sonnet-4-5/invocations

# Optional (auto-detected)
# PROJECT_ROOT=/Workspace/Users/your.email/databricks-assessment-tool
```

### Supported LLM Models

Works with any Databricks Model Serving endpoint:
- `databricks-claude-sonnet-4-5` (recommended)
- `databricks-meta-llama-3-1-405b-instruct`
- `databricks-gpt-oss-120b`
- Custom models

---

## Terraform Export Coverage

**31+ Databricks resource types:**

- **Identity:** Users, Groups, Service Principals, Permissions
- **Compute:** Clusters, Policies, Instance Pools
- **Jobs:** Job definitions, Tasks, Schedules
- **Unity Catalog:** Catalogs, Schemas, Tables, Volumes, Grants, External Locations, Storage Credentials, Models
- **SQL Analytics:** Warehouses, Dashboards, Queries, Alerts
- **ML:** Model Serving, Vector Search
- **Notebooks:** All workspace notebooks with language detection
- **Storage:** DBFS files, External tables, Workspace files
- **Other:** Secrets, Repos, Settings

---

## AI Analysis

Generates comprehensive reports in PT-BR with:

**Technical Report:**
**Executive Summary:**
**Features:**

---

## Troubleshooting

### Common Issues

**1. "DATABRICKS_HOST and DATABRICKS_TOKEN must be set"**
- Verify `.env` file exists in project root
- Check for extra spaces in variable definitions

**2. Frontend 404 errors (assets not found)**
- Rebuild frontend: `cd databricks_app/frontend && npm run build`
- Verify `vite.config.js` has `base: './'`

**3. Terraform not found**
- Databricks: run `bash run_databricks.sh` (auto-installs Terraform)
- Local: install Terraform CLI from https://www.terraform.io/downloads

**4. AI Agents don't generate report**
- Verify `.tf` files exist in `databricks_tf_files/`
- Check Model Serving endpoint is accessible
- Review logs for `[Simple Agent]` output

**5. PDF tables overflow**
- Use HTML export instead
- Open HTML in browser and click "Export to PDF" button (better rendering)

### Debug Mode

```bash
# Test AI agent directly
cd databricks_app/backend/ai_agent
python run.py

# Backend with verbose logging
cd databricks_app/backend
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## License

Proprietary. All rights reserved.

---

**Built with ❤️ to simplify Databricks infrastructure analysis**
