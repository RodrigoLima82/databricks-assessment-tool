#!/usr/bin/env python3
"""
Cross-platform application starter for Databricks Assessment Tool
Replaces run_app.sh with a Python script that works on Windows, macOS, and Linux
"""

import os
import sys
import time
import signal
import subprocess
import platform
from pathlib import Path
from dotenv import load_dotenv

# Colors for terminal output
if platform.system() == "Windows":
    # Enable ANSI colors on Windows 10+
    os.system("color")

BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

# Project paths
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = PROJECT_ROOT / "databricks_app" / "backend"
FRONTEND_DIR = PROJECT_ROOT / "databricks_app" / "frontend"
ENV_FILE = PROJECT_ROOT / ".env"

# Global process references
backend_process = None
frontend_process = None


def print_color(text, color=NC):
    """Print colored text"""
    print(f"{color}{text}{NC}")


def load_env_file():
    """Load environment variables from .env"""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
        print_color(f"✅ Loaded .env from {ENV_FILE}", GREEN)
        return True
    else:
        print_color(f"❌ .env file not found: {ENV_FILE}", RED)
        print_color("   Create .env based on .env.example", YELLOW)
        return False


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print_color(f"🐍 Python {version.major}.{version.minor}.{version.micro}", BLUE)
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_color("❌ Python 3.8+ required", RED)
        return False
    
    return True


def check_node():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_color(f"📦 Node.js {version}", BLUE)
            return True
    except FileNotFoundError:
        pass
    
    print_color("❌ Node.js not found. Install from https://nodejs.org/", RED)
    return False


def install_backend_deps():
    """Install backend dependencies"""
    print_color("\n📦 Installing backend dependencies...", BLUE)
    
    # Choose requirements file based on platform
    if platform.system() == "Windows":
        req_file = BACKEND_DIR / "requirements_windows.txt"
        if not req_file.exists():
            req_file = BACKEND_DIR / "requirements.txt"
    else:
        req_file = BACKEND_DIR / "requirements.txt"
    
    print_color(f"   Using: {req_file.name}", BLUE)
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            cwd=str(PROJECT_ROOT),
            check=True
        )
        print_color("✅ Backend dependencies installed", GREEN)
        return True
    except subprocess.CalledProcessError as e:
        print_color(f"❌ Failed to install backend dependencies: {e}", RED)
        return False


def install_frontend_deps():
    """Install frontend dependencies"""
    print_color("\n📦 Installing frontend dependencies...", BLUE)
    
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        print_color("✅ node_modules exists, skipping install", GREEN)
        return True
    
    try:
        subprocess.run(
            ["npm", "install"],
            cwd=str(FRONTEND_DIR),
            check=True
        )
        print_color("✅ Frontend dependencies installed", GREEN)
        return True
    except subprocess.CalledProcessError as e:
        print_color(f"❌ Failed to install frontend dependencies: {e}", RED)
        return False


def start_backend(port):
    """Start FastAPI backend"""
    global backend_process
    
    print_color(f"\n🚀 Starting backend on port {port}...", BLUE)
    
    # Use uvicorn with proper module path
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", str(port),
        "--reload"
    ]
    
    try:
        backend_process = subprocess.Popen(
            cmd,
            cwd=str(BACKEND_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print_color(f"✅ Backend started (PID: {backend_process.pid})", GREEN)
        print_color(f"   → http://localhost:{port}", GREEN)
        return True
        
    except Exception as e:
        print_color(f"❌ Failed to start backend: {e}", RED)
        return False


def start_frontend(port):
    """Start Vite frontend"""
    global frontend_process
    
    print_color(f"\n🚀 Starting frontend on port {port}...", BLUE)
    
    # Set environment variable for Vite
    env = os.environ.copy()
    env['PORT'] = str(port)
    
    # Use npm run dev
    cmd = ["npm", "run", "dev", "--", "--port", str(port), "--host"]
    
    try:
        frontend_process = subprocess.Popen(
            cmd,
            cwd=str(FRONTEND_DIR),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print_color(f"✅ Frontend started (PID: {frontend_process.pid})", GREEN)
        print_color(f"   → http://localhost:{port}", GREEN)
        return True
        
    except Exception as e:
        print_color(f"❌ Failed to start frontend: {e}", RED)
        return False


def cleanup():
    """Cleanup processes on exit"""
    print_color("\n\n🛑 Shutting down...", YELLOW)
    
    if backend_process:
        print_color("   Stopping backend...", YELLOW)
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
    
    if frontend_process:
        print_color("   Stopping frontend...", YELLOW)
        frontend_process.terminate()
        try:
            frontend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            frontend_process.kill()
    
    print_color("✅ Shutdown complete", GREEN)


def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    cleanup()
    sys.exit(0)


def main():
    """Main function"""
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    if platform.system() != "Windows":
        signal.signal(signal.SIGTERM, signal_handler)
    
    print_color("=" * 80, BLUE)
    print_color("   🚀 DATABRICKS ASSESSMENT TOOL - Startup Script", BLUE)
    print_color("=" * 80, BLUE)
    print_color(f"\n📍 Project: {PROJECT_ROOT}", BLUE)
    print_color(f"💻 Platform: {platform.system()} {platform.machine()}\n", BLUE)
    
    # Pre-flight checks
    if not check_python_version():
        sys.exit(1)
    
    if not check_node():
        sys.exit(1)
    
    if not load_env_file():
        sys.exit(1)
    
    # Get ports from environment or use defaults
    backend_port = int(os.getenv("BACKEND_PORT", "8002"))
    frontend_port = int(os.getenv("FRONTEND_PORT", "3002"))
    
    print_color(f"\n🔧 Configuration:", BLUE)
    print_color(f"   Backend Port:  {backend_port}", BLUE)
    print_color(f"   Frontend Port: {frontend_port}", BLUE)
    
    # Ask if user wants to install dependencies
    print_color("\n" + "=" * 80, BLUE)
    response = input("Install/update dependencies? [y/N]: ").strip().lower()
    
    if response == 'y':
        if not install_backend_deps():
            sys.exit(1)
        if not install_frontend_deps():
            sys.exit(1)
    else:
        print_color("⏭️  Skipping dependency installation", YELLOW)
    
    # Start services
    print_color("\n" + "=" * 80, BLUE)
    print_color("   🚀 STARTING SERVICES", BLUE)
    print_color("=" * 80, BLUE)
    
    if not start_backend(backend_port):
        sys.exit(1)
    
    time.sleep(2)  # Give backend time to start
    
    if not start_frontend(frontend_port):
        cleanup()
        sys.exit(1)
    
    # Wait for frontend to be ready
    time.sleep(5)
    
    # Print ready message
    print_color("\n" + "=" * 80, GREEN)
    print_color("   ✅ APPLICATION READY!", GREEN)
    print_color("=" * 80, GREEN)
    print_color(f"\n   Backend:  http://localhost:{backend_port}", GREEN)
    print_color(f"   Frontend: http://localhost:{frontend_port}", GREEN)
    print_color(f"\n   Press Ctrl+C to stop\n", YELLOW)
    
    # Keep running and monitor processes
    try:
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process and backend_process.poll() is not None:
                print_color("❌ Backend process died unexpectedly", RED)
                cleanup()
                sys.exit(1)
            
            if frontend_process and frontend_process.poll() is not None:
                print_color("❌ Frontend process died unexpectedly", RED)
                cleanup()
                sys.exit(1)
                
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()

