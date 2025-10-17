"""
Databricks Assessment Tool - Backend API
FastAPI application for managing Terraform exports and AI agent analysis
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import json
import yaml
import subprocess
import asyncio
from pathlib import Path
import logging

# Import our Python executors
from executors import TerraformExporter, AIAgentsAnalyzer
from pdf_generator import html_to_pdf, markdown_to_html
from execution_manager import execution_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Databricks Assessment Tool", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = BASE_DIR / "databricks_summary_agent" / "src" / "terraform_file_summary_agent" / "config"
OUTPUT_DIR = BASE_DIR / "output_summary_agent"
UCX_DIR = BASE_DIR / "ucx_export"
SCRIPTS_DIR = BASE_DIR / "scripts"

# ============================================================================
# Models
# ============================================================================

class ConfigModel(BaseModel):
    databricks_host: str
    databricks_token: str
    terraform_path: Optional[str] = None

class AgentConfig(BaseModel):
    name: str
    role: str
    goal: str
    backstory: str

class TaskConfig(BaseModel):
    name: str
    description: str
    expected_output: str
    agent: str

class ExecutionRequest(BaseModel):
    run_terraform: bool = True
    run_agents: bool = True
    terraform_services: Optional[str] = "groups,secrets,access,compute,users,jobs,storage"
    terraform_listing: Optional[str] = "jobs,compute"
    terraform_debug: bool = False
    selected_agents: Optional[str] = "terraform_reader,databricks_specialist,ucx_analyst,report_generator"

# ============================================================================
# Step 1: Configuration Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Databricks Assessment Tool"}

@app.post("/api/config/validate")
async def validate_config(config: ConfigModel):
    """Validate Databricks credentials and Terraform setup"""
    try:
        # Test Databricks connection
        import requests
        headers = {"Authorization": f"Bearer {config.databricks_token}"}
        response = requests.get(
            f"{config.databricks_host}/api/2.0/clusters/list",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return {
                "databricks": False,
                "terraform": False,
                "message": f"Databricks authentication failed: {response.status_code}"
            }
        
        # Check Terraform binary
        terraform_exists = os.path.exists(config.terraform_path) if config.terraform_path else False
        if not terraform_exists:
            # Try to find terraform in PATH
            try:
                subprocess.run(["terraform", "--version"], capture_output=True, check=True)
                terraform_exists = True
            except:
                terraform_exists = False
        
        return {
            "databricks": True,
            "terraform": terraform_exists,
            "message": "Configuration validated successfully"
        }
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            "databricks": False,
            "terraform": False,
            "message": f"Error: {str(e)}"
        }

@app.post("/api/config/save")
async def save_config(config: ConfigModel):
    """Save configuration to .env file"""
    try:
        env_path = BASE_DIR / ".env"
        
        env_content = f"""# Databricks Configuration
DATABRICKS_HOST={config.databricks_host}
DATABRICKS_TOKEN={config.databricks_token}
"""
        if config.terraform_path:
            env_content += f"TERRAFORM_PATH={config.terraform_path}\n"
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        return {"success": True, "message": "Configuration saved successfully"}
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/load")
async def load_config():
    """Load existing configuration"""
    try:
        env_path = BASE_DIR / ".env"
        if not env_path.exists():
            return {"exists": False}
        
        config = {}
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key.lower()] = value
        
        return {
            "exists": True,
            "config": {
                "databricks_host": config.get("databricks_host", ""),
                "databricks_token": config.get("databricks_token", "")[:10] + "..." if config.get("databricks_token") else "",
                "terraform_path": config.get("terraform_path", "")
            }
        }
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Step 2: Agent Configuration Endpoints
# ============================================================================

@app.get("/api/agents/list")
async def list_agents():
    """List all configured agents"""
    try:
        agents_path = CONFIG_DIR / "agents.yaml"
        with open(agents_path, 'r') as f:
            agents = yaml.safe_load(f)
        
        return {"agents": agents}
    except Exception as e:
        logger.error(f"Error loading agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tasks/list")
async def list_tasks():
    """List all configured tasks"""
    try:
        tasks_path = CONFIG_DIR / "tasks.yaml"
        with open(tasks_path, 'r') as f:
            tasks = yaml.safe_load(f)
        
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error loading tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/agents/update/{agent_name}")
async def update_agent(agent_name: str, agent: AgentConfig):
    """Update an existing agent configuration"""
    try:
        agents_path = CONFIG_DIR / "agents.yaml"
        with open(agents_path, 'r') as f:
            agents = yaml.safe_load(f)
        
        agents[agent_name] = {
            "role": agent.role,
            "goal": agent.goal,
            "backstory": agent.backstory
        }
        
        with open(agents_path, 'w') as f:
            yaml.dump(agents, f, default_flow_style=False, sort_keys=False)
        
        return {"success": True, "message": f"Agent '{agent_name}' updated successfully"}
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agents/create")
async def create_agent(agent: AgentConfig):
    """Create a new agent"""
    try:
        agents_path = CONFIG_DIR / "agents.yaml"
        with open(agents_path, 'r') as f:
            agents = yaml.safe_load(f) or {}
        
        if agent.name in agents:
            raise HTTPException(status_code=400, detail="Agent already exists")
        
        agents[agent.name] = {
            "role": agent.role,
            "goal": agent.goal,
            "backstory": agent.backstory
        }
        
        with open(agents_path, 'w') as f:
            yaml.dump(agents, f, default_flow_style=False, sort_keys=False)
        
        return {"success": True, "message": f"Agent '{agent.name}' created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agents/delete/{agent_name}")
async def delete_agent(agent_name: str):
    """Delete an agent"""
    try:
        agents_path = CONFIG_DIR / "agents.yaml"
        with open(agents_path, 'r') as f:
            agents = yaml.safe_load(f)
        
        if agent_name not in agents:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        del agents[agent_name]
        
        with open(agents_path, 'w') as f:
            yaml.dump(agents, f, default_flow_style=False, sort_keys=False)
        
        return {"success": True, "message": f"Agent '{agent_name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Step 3: UCX Upload Endpoint
# ============================================================================

@app.post("/api/ucx/upload")
async def upload_ucx_file(file: UploadFile = File(...)):
    """Upload UCX assessment CSV/Excel file"""
    try:
        # Ensure UCX directory exists
        UCX_DIR.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = UCX_DIR / file.filename
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        
        return {
            "success": True,
            "message": f"File '{file.filename}' uploaded successfully",
            "filename": file.filename,
            "size": len(content)
        }
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ucx/files")
async def list_ucx_files():
    """List uploaded UCX files"""
    try:
        if not UCX_DIR.exists():
            return {"files": []}
        
        files = []
        for file_path in UCX_DIR.glob("*"):
            if file_path.is_file() and file_path.suffix in ['.csv', '.xlsx', '.xls']:
                files.append({
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime
                })
        
        return {"files": files}
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/ucx/delete/{filename}")
async def delete_ucx_file(filename: str):
    """Delete a UCX file"""
    try:
        file_path = UCX_DIR / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path.unlink()
        return {"success": True, "message": f"File '{filename}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Step 4: Execution Endpoints with WebSocket
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws/execution")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time execution updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/execute/start")
async def start_execution(request: ExecutionRequest):
    """Start the execution pipeline"""
    try:
        # Save configuration for re-use
        execution_manager.save_config({
            "run_terraform": request.run_terraform,
            "run_agents": request.run_agents,
            "terraform_services": request.terraform_services,
            "terraform_listing": request.terraform_listing,
            "terraform_debug": request.terraform_debug,
            "selected_agents": request.selected_agents
        })
        
        # Reset stop flag
        execution_manager.reset_stop()
        execution_manager.set_execution_state(True, "initializing", 0)
        
        # Clean previous outputs
        if OUTPUT_DIR.exists():
            for file in OUTPUT_DIR.glob("*.md"):
                file.unlink()
        
        # Start execution in background
        asyncio.create_task(run_pipeline(request))
        
        return {
            "success": True,
            "message": "Execution started",
            "estimated_time": "5-10 minutes"
        }
    except Exception as e:
        logger.error(f"Error starting execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute/stop")
async def stop_execution():
    """Stop the current execution"""
    try:
        result = execution_manager.request_stop()
        await manager.broadcast({
            "type": "stopped",
            "message": "Execution stopped by user"
        })
        return result
    except Exception as e:
        logger.error(f"Error stopping execution: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/execute/status")
async def get_execution_status():
    """Get current execution status"""
    try:
        return execution_manager.get_execution_state()
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/execute/last-config")
async def get_last_config():
    """Get last execution configuration"""
    try:
        config = execution_manager.get_last_config()
        return {"success": True, "config": config}
    except Exception as e:
        logger.error(f"Error getting last config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_pipeline(request: ExecutionRequest):
    """Run the execution pipeline with real-time updates and detailed logs"""
    import time
    
    # Callback for real-time updates
    async def broadcast_callback(msg_type: str, step: str, status: Optional[str], message: str):
        """Helper to broadcast messages to WebSocket clients"""
        msg = {
            "type": msg_type,
            "step": step,
            "message": message
        }
        if status:
            msg["status"] = status
        await manager.broadcast(msg)
    
    try:
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("🚀 STARTING PIPELINE EXECUTION")
        logger.info("=" * 80)
        logger.info(f"Terraform Export: {request.run_terraform}")
        if request.run_terraform:
            logger.info(f"  Services: {request.terraform_services}")
            logger.info(f"  Listing: {request.terraform_listing}")
            logger.info(f"  Debug: {request.terraform_debug}")
        logger.info(f"AI Agents Analysis: {request.run_agents}")
        if request.run_agents:
            agents_list = request.selected_agents.split(',') if request.selected_agents else []
            logger.info(f"  Selected Agents: {', '.join(agents_list)}")
            logger.info(f"  Agent Count: {len(agents_list)}")
        
        # Step 1: Terraform Export
        if request.run_terraform:
            # Check for stop
            if execution_manager.is_stop_requested():
                logger.info("🛑 Execution stopped by user (before Terraform)")
                return
            
            execution_manager.set_execution_state(True, "terraform", 25)
            logger.info("\n" + "=" * 80)
            logger.info("📦 STEP 1/2: TERRAFORM EXPORT")
            logger.info("=" * 80)
            
            exporter = TerraformExporter()
            terraform_result = await exporter.run(
                services=request.terraform_services or "groups,secrets,access,compute,users,jobs,storage",
                listing=request.terraform_listing or "jobs,compute",
                debug=request.terraform_debug,
                callback=broadcast_callback
            )
            
            elapsed = time.time() - start_time
            
            # Check for stop after terraform
            if execution_manager.is_stop_requested():
                logger.info("🛑 Execution stopped by user (after Terraform)")
                return
            
            if not terraform_result["success"]:
                logger.error(f"❌ Terraform export failed: {terraform_result.get('error')}")
                execution_manager.set_execution_state(False, "error", 0)
                return
        
        # Step 2: AI Agents
        if request.run_agents:
            # Check for stop
            if execution_manager.is_stop_requested():
                logger.info("🛑 Execution stopped by user (before AI Agents)")
                return
            
            execution_manager.set_execution_state(True, "agents", 50)
            logger.info("\n" + "=" * 80)
            logger.info("🤖 STEP 2/2: AI AGENTS ANALYSIS")
            logger.info("=" * 80)
            
            agents_start = time.time()
            
            analyzer = AIAgentsAnalyzer()
            agents_result = await analyzer.run(
                selected_agents=request.selected_agents or "terraform_reader,databricks_specialist,ucx_analyst,report_generator",
                callback=broadcast_callback
            )
            
            agents_elapsed = time.time() - agents_start
            
            # Check for stop after agents
            if execution_manager.is_stop_requested():
                logger.info("🛑 Execution stopped by user (after AI Agents)")
                return
            
            if not agents_result["success"]:
                logger.error(f"❌ AI analysis failed: {agents_result.get('error')}")
                execution_manager.set_execution_state(False, "error", 0)
                return
        
        # Execution completed
        total_time = time.time() - start_time
        execution_manager.set_execution_state(False, "completed", 100)
        logger.info("\n" + "=" * 80)
        logger.info(f"🎉 PIPELINE COMPLETED SUCCESSFULLY in {total_time:.1f}s")
        logger.info("=" * 80)
        
        await manager.broadcast({
            "type": "completed",
            "message": f"Pipeline execution completed successfully in {total_time:.1f}s"
        })
        
    except Exception as e:
        execution_manager.set_execution_state(False, "error", 0)
        logger.error(f"❌ Pipeline execution error: {str(e)}", exc_info=True)
        await manager.broadcast({
            "type": "error",
            "message": f"Pipeline error: {str(e)}"
        })

# ============================================================================
# Step 5: Results and Export Endpoints
# ============================================================================

@app.get("/api/results/list")
async def list_reports():
    """List all generated reports from agents"""
    try:
        reports = []
        
        # Define expected reports with their metadata
        report_configs = [
            {
                "filename": "Terraform_Infrastructure_Analysis.md",
                "agent": "terraform_reader",
                "title": "Infrastructure Analysis",
                "icon": "🔍",
                "description": "Terraform resources and configurations"
            },
            {
                "filename": "Databricks_Security_Performance_Analysis.md",
                "agent": "databricks_specialist",
                "title": "Security & Performance",
                "icon": "🛡️",
                "description": "Security findings and optimization opportunities"
            },
            {
                "filename": "UCX_Migration_Assessment.md",
                "agent": "ucx_analyst",
                "title": "UCX Migration Readiness",
                "icon": "📈",
                "description": "Unity Catalog migration assessment"
            },
            {
                "filename": "Databricks_Assessment_Report.md",
                "agent": "report_generator",
                "title": "Consolidated Report",
                "icon": "📝",
                "description": "Complete assessment summary"
            }
        ]
        
        for config in report_configs:
            report_path = OUTPUT_DIR / config["filename"]
            if report_path.exists():
                stat = report_path.stat()
                reports.append({
                    "filename": config["filename"],
                    "agent": config["agent"],
                    "title": config["title"],
                    "icon": config["icon"],
                    "description": config["description"],
                    "size": stat.st_size,
                    "exists": True
                })
            else:
                reports.append({
                    "filename": config["filename"],
                    "agent": config["agent"],
                    "title": config["title"],
                    "icon": config["icon"],
                    "description": config["description"],
                    "exists": False
                })
        
        return {"success": True, "reports": reports}
        
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/report/{filename}")
async def get_report_by_filename(filename: str, format: str = "html"):
    """Get a specific report by filename in HTML or Markdown format"""
    try:
        report_path = OUTPUT_DIR / filename
        if not report_path.exists():
            raise HTTPException(status_code=404, detail=f"Report {filename} not found")
        
        with open(report_path, 'r') as f:
            markdown_content = f.read()
        
        if format == "html":
            # Convert Markdown to HTML for better display
            html_content = markdown_to_html(markdown_content)
            return {
                "success": True,
                "content": html_content,
                "format": "html",
                "filename": filename
            }
        else:
            # Return raw markdown
            return {
                "success": True,
                "content": markdown_content,
                "format": "markdown",
                "filename": filename
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading report {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/final")
async def get_final_report(format: str = "html"):
    """Get the final consolidated report in HTML or Markdown format (alias for consolidated report)"""
    return await get_report_by_filename("Databricks_Assessment_Report.md", format)

@app.get("/api/results/download")
async def download_report():
    """Download the final report as Markdown"""
    try:
        report_path = OUTPUT_DIR / "Databricks_Assessment_Report.md"
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        return FileResponse(
            path=report_path,
            media_type="text/markdown",
            filename="Databricks_Assessment_Report.md"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/results/export-pdf")
async def export_to_pdf():
    """Export report to PDF using WeasyPrint (no pandoc required!)"""
    try:
        report_path = OUTPUT_DIR / "Databricks_Assessment_Report.md"
        pdf_path = OUTPUT_DIR / "Databricks_Assessment_Report.pdf"
        
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Read markdown content
        with open(report_path, 'r') as f:
            markdown_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown_to_html(markdown_content)
        
        # Generate PDF from HTML using WeasyPrint (no pandoc needed!)
        success = html_to_pdf(
            html_content,
            str(pdf_path),
            title="Databricks Assessment Report"
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="PDF generation failed. Install weasyprint: pip install weasyprint"
            )
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename="Databricks_Assessment_Report.pdf"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Serve Frontend Static Files (for single-process deployment)
# ============================================================================

# Mount static assets
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    logger.info(f"Serving static frontend from: {FRONTEND_DIST}")
    # Serve assets folder
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")
    
    # Serve index.html for root and all non-API routes (SPA routing)
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend_root():
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text(), status_code=200)
        return HTMLResponse(content="<h1>Frontend not built</h1><p>Run: cd frontend && npm run build</p>", status_code=404)
    
    # Catch-all route for SPA (must be last)
    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_frontend_catchall(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # Serve index.html for all other routes (SPA routing)
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text(), status_code=200)
        return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)
else:
    logger.warning(f"Frontend dist directory not found: {FRONTEND_DIST}")
    logger.warning("Run 'cd frontend && npm run build' to build the frontend")
    
    @app.get("/")
    async def root():
        return {"message": "Databricks Assessment Tool API", "status": "Frontend not built"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)

