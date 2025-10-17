"""
Databricks Assessment Tool - Minimal Backend
Testing deployment on Databricks Apps
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from pathlib import Path

app = FastAPI(title="Databricks Assessment Tool - Minimal", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    message: str
    environment: dict

@app.get("/")
async def root():
    return {
        "message": "Databricks Assessment Tool API - Minimal Version",
        "status": "running",
        "version": "1.0.0-minimal"
    }

@app.get("/health")
async def health():
    return HealthResponse(
        status="healthy",
        message="Application is running",
        environment={
            "backend_port": os.getenv("BACKEND_PORT", "8080"),
            "databricks_host": os.getenv("DATABRICKS_HOST", "not_set")[:20] + "..." if os.getenv("DATABRICKS_HOST") else "not_set",
            "volume_path": os.getenv("VOLUME_PATH", "not_set"),
        }
    )

@app.get("/api/health")
async def api_health():
    """Health check endpoint for API"""
    return {
        "status": "ok",
        "service": "Databricks Assessment Tool",
        "version": "1.0.0-minimal"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)

