"""
Execution modules for Terraform export and AI agents analysis.
CROSS-PLATFORM: Automatically detects OS (Windows, macOS, Linux) and architecture.
"""

import os
import sys
import platform
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Callable, List
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
TF_FILES_DIR = BASE_DIR / "databricks_tf_files"
OUTPUT_DIR = BASE_DIR / "output_summary_agent"
BACKEND_DIR = Path(__file__).parent
AI_AGENT_DIR = BACKEND_DIR / "ai_agent"

# Load environment variables from .env file
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)
    logger.info(f"✅ Loaded environment variables from {env_file}")
else:
    logger.warning(f"⚠️  .env file not found at {env_file}")


def get_terraform_binary_path() -> Optional[Path]:
    """
    Detect Terraform provider binary based on OS and architecture.
    Supports: Windows (x64/ARM), macOS (Intel/Apple Silicon), Linux (x64/ARM)
    
    Returns:
        Path to terraform provider binary or None if not found
    """
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Provider version (should match init.tf)
    PROVIDER_VERSION = "1.95.0"
    
    # Determine platform string for terraform provider
    if system == "windows":
        if "amd64" in machine or "x86_64" in machine:
            platform_str = "windows_amd64"
            binary_name = f"terraform-provider-databricks_v{PROVIDER_VERSION}.exe"
        elif "arm" in machine or "aarch64" in machine:
            platform_str = "windows_arm64"
            binary_name = f"terraform-provider-databricks_v{PROVIDER_VERSION}.exe"
        else:
            logger.error(f"Unsupported Windows architecture: {machine}")
            return None
    
    elif system == "darwin":  # macOS
        if "arm" in machine or "aarch64" in machine:
            platform_str = "darwin_arm64"
            binary_name = f"terraform-provider-databricks_v{PROVIDER_VERSION}"
        else:
            platform_str = "darwin_amd64"
            binary_name = f"terraform-provider-databricks_v{PROVIDER_VERSION}"
    
    elif system == "linux":
        if "aarch64" in machine or "arm64" in machine:
            platform_str = "linux_arm64"
            binary_name = f"terraform-provider-databricks_v{PROVIDER_VERSION}"
        elif "amd64" in machine or "x86_64" in machine:
            platform_str = "linux_amd64"
            binary_name = f"terraform-provider-databricks_v{PROVIDER_VERSION}"
        else:
            logger.error(f"Unsupported Linux architecture: {machine}")
            return None
    
    else:
        logger.error(f"Unsupported operating system: {system}")
        return None
    
    # Construct path to binary
    binary_path = (
        BASE_DIR / ".terraform" / "providers" / "registry.terraform.io" / 
        "databricks" / "databricks" / PROVIDER_VERSION / platform_str / binary_name
    )
    
    logger.info(f"🔍 Detected platform: {system}/{machine} -> {platform_str}")
    logger.info(f"🔍 Expected binary: {binary_path}")
    
    if binary_path.exists():
        logger.info(f"✅ Terraform provider binary found")
        return binary_path
    else:
        logger.warning(f"⚠️  Terraform provider binary not found at: {binary_path}")
        logger.warning(f"   Run: terraform init")
        return None


class TerraformExporter:
    """Handles Terraform export operations (cross-platform)"""
    
    def __init__(self):
        self.exporter_binary = get_terraform_binary_path()
        
    async def run(
        self,
        services: str = "groups,secrets,access,compute,users,jobs,storage",
        listing: str = "jobs,compute",
        debug: bool = False,
        callback: Optional[Callable] = None
    ) -> dict:
        """
        Execute Terraform Databricks Exporter.
        
        Args:
            services: Comma-separated list of services to export
            listing: Comma-separated list of listing options
            debug: Enable debug mode
            callback: Optional async callback for real-time updates
        
        Returns:
            Dictionary with execution results
        """
        logger.info("=" * 80)
        logger.info("📦 TERRAFORM EXPORT")
        logger.info("=" * 80)
        logger.info(f"Services: {services}")
        logger.info(f"Listing: {listing}")
        logger.info(f"Debug: {debug}")
        
        if callback:
            await callback("status", "terraform", "running", 
                         "Initializing Terraform export...")
        
        # Verify exporter binary exists
        if self.exporter_binary is None:
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            # Provide platform-specific error message
            if system == "windows" and "arm" in machine:
                error_msg = (
                    f"Terraform provider binary not available for your platform: {system}/{machine}\n\n"
                    f"The Databricks provider does not support Windows ARM64.\n\n"
                    f"Solutions:\n"
                    f"1. Use WSL2 (Windows Subsystem for Linux) - Recommended\n"
                    f"2. Use an x64 Windows machine\n"
                    f"3. Analyze existing Terraform files without running export\n\n"
                    f"Run 'terraform init' to see supported platforms."
                )
            else:
                error_msg = (
                    f"Terraform provider binary not found at expected location.\n\n"
                    f"Platform: {system}/{machine}\n"
                    f"Expected path: .terraform/providers/registry.terraform.io/databricks/databricks/\n\n"
                    f"Solutions:\n"
                    f"1. Ensure 'terraform init' completed successfully\n"
                    f"2. Check that .terraform/providers directory exists\n"
                    f"3. Verify the provider version matches your init.tf\n\n"
                    f"Run 'terraform init' to download the provider."
                )
            
            logger.error(error_msg)
            if callback:
                await callback("status", "terraform", "error", error_msg)
            return {"success": False, "error": error_msg}
        
        if not self.exporter_binary.exists():
            error_msg = f"Exporter binary not found at {self.exporter_binary}\n\nRun: terraform init"
            logger.error(error_msg)
            if callback:
                await callback("status", "terraform", "error", error_msg)
            return {"success": False, "error": error_msg}
        
        # Create output directory if it doesn't exist
        TF_FILES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Clean previous exports
        logger.info("Cleaning previous exports...")
        if callback:
            await callback("log", "terraform", None, 
                         "🗑️  Cleaning previous Terraform files...")
        
        for tf_file in TF_FILES_DIR.glob("*.tf"):
            tf_file.unlink()
        
        # Build command
        cmd = [
            str(self.exporter_binary),
            "exporter",
            "-skip-interactive",
            "-services", services,
            "-listing", listing,
        ]
        
        if debug:
            cmd.append("-debug")
        
        logger.info(f"Command: {' '.join(cmd)}")
        
        # Set environment variables
        env = os.environ.copy()
        env["DATABRICKS_HOST"] = os.getenv("DATABRICKS_HOST", "")
        env["DATABRICKS_TOKEN"] = os.getenv("DATABRICKS_TOKEN", "")
        
        if not env["DATABRICKS_HOST"] or not env["DATABRICKS_TOKEN"]:
            error_msg = "DATABRICKS_HOST and DATABRICKS_TOKEN must be set"
            logger.error(error_msg)
            if callback:
                await callback("status", "terraform", "error", error_msg)
            return {"success": False, "error": error_msg}
        
        # Execute
        try:
            # Windows: Use synchronous subprocess to avoid asyncio issues
            if platform.system() == "Windows":
                logger.info("⚠️  Windows: Using synchronous subprocess in thread pool")
                import subprocess
                import concurrent.futures
                
                def run_terraform_sync():
                    """Run terraform subprocess synchronously"""
                    proc = subprocess.Popen(
                        cmd,
                        cwd=str(TF_FILES_DIR),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        env=env,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        bufsize=1
                    )
                    return proc
                
                # Run subprocess creation in thread
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    process_sync = await loop.run_in_executor(executor, run_terraform_sync)
                
                logger.info(f"✅ Terraform process started with PID: {process_sync.pid}")
                
                # Stream output line by line
                for line in process_sync.stdout:
                    decoded = line.strip()
                    if decoded:
                        logger.info(f"TERRAFORM: {decoded}")
                        if callback:
                            await callback("log", "terraform", None, decoded)
                
                # Wait for completion
                returncode = process_sync.wait()
                
                class FakeProcess:
                    """Fake process object to match Unix behavior"""
                    def __init__(self, rc):
                        self.returncode = rc
                
                process = FakeProcess(returncode)
                
            else:
                # Unix: Use async subprocess normally
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=TF_FILES_DIR,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                
                # Stream output
                async def stream_output(stream, prefix):
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        decoded = line.decode().strip()
                        if decoded:
                            logger.info(f"{prefix}: {decoded}")
                            if callback:
                                await callback("log", "terraform", None, decoded)
                
                await asyncio.gather(
                    stream_output(process.stdout, "TERRAFORM"),
                    stream_output(process.stderr, "TERRAFORM-ERR")
                )
                
                await process.wait()
            
            # Check if files were generated (even if exit code is non-zero)
            # Exit code 1 can happen when terraform fmt fails, but export succeeded
            tf_files = list(TF_FILES_DIR.glob("*.tf"))
            
            if len(tf_files) > 0:
                # Files were generated - consider it a success
                logger.info(f"✅ Successfully exported {len(tf_files)} Terraform files")
                
                if process.returncode != 0:
                    logger.warning(f"⚠️  Exit code {process.returncode} (likely terraform fmt not available, but files were generated)")
                
                if callback:
                    await callback("status", "terraform", "completed",
                                 f"✅ Terraform export completed ({len(tf_files)} files)")
                
                return {
                    "success": True,
                    "files_count": len(tf_files),
                    "exit_code": process.returncode
                }
            else:
                # No files generated - real failure
                error_msg = f"Exporter failed: no files generated (exit code {process.returncode})"
                logger.error(error_msg)
                if callback:
                    await callback("status", "terraform", "error", error_msg)
                return {"success": False, "error": error_msg, "exit_code": process.returncode}
                
        except Exception as e:
            error_msg = f"Exception during export: {str(e)}"
            logger.exception(error_msg)
            if callback:
                await callback("status", "terraform", "error", error_msg)
            return {"success": False, "error": error_msg}


class AIAgentsAnalyzer:
    """Handles AI agents execution"""
    
    def __init__(self):
        self.agent_dir = AI_AGENT_DIR
        self.output_dir = OUTPUT_DIR
        
    async def run(
        self,
        selected_agents: str = "terraform_reader,databricks_specialist,ucx_analyst,report_generator",
        report_language: str = "pt-BR",
        callback: Optional[Callable] = None
    ) -> dict:
        """
        Execute AI agents analysis.
        
        Args:
            selected_agents: Comma-separated list of agent names
            report_language: Report language code (pt-BR, en-US, es-ES)
            callback: Optional async callback for real-time updates
        
        Returns:
            Dictionary with execution results
        """
        logger.info("=" * 80)
        logger.info("🤖 AI AGENTS ANALYSIS")
        logger.info("=" * 80)
        
        agents_list = [a.strip() for a in selected_agents.split(',')]
        logger.info(f"🔍 Selected Agents: {', '.join(agents_list)}")
        logger.info(f"🔍 Agent Count: {len(agents_list)}")
        logger.info(f"🔍 Agent Directory: {self.agent_dir}")
        logger.info(f"🔍 Output Directory: {self.output_dir}")
        logger.info(f"🔍 Agent Dir Exists: {self.agent_dir.exists()}")
        logger.info(f"🔍 Output Dir Exists: {self.output_dir.exists()}")
        
        if callback:
            await callback("status", "agents", "running",
                         f"Initializing {len(agents_list)} AI agents...")
        
        # Verify Terraform files exist before running AI analysis
        logger.info(f"🔍 Checking for Terraform files in: {TF_FILES_DIR}")
        
        if not TF_FILES_DIR.exists():
            error_msg = "⚠️ Terraform export directory not found. Please run Terraform Export first (Step 3)."
            logger.error(error_msg)
            if callback:
                await callback("status", "agents", "error", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "requires_terraform_export": True
            }
        
        tf_files = list(TF_FILES_DIR.glob("*.tf"))
        
        if not tf_files:
            error_msg = "⚠️ No Terraform files found. Please run Terraform Export first before AI Analysis."
            logger.warning(error_msg)
            logger.info(f"💡 To fix this: Go back to 'Execute' step and check 'Run Terraform Export'")
            
            if callback:
                await callback("status", "agents", "error", error_msg)
                await callback("log", "agents", None, "")
                await callback("log", "agents", None, "📝 How to fix:")
                await callback("log", "agents", None, "   1. Go back to the 'Execute' step")
                await callback("log", "agents", None, "   2. Enable 'Run Terraform Export'")
                await callback("log", "agents", None, "   3. Click 'Start Execution'")
            
            return {
                "success": False,
                "error": error_msg,
                "requires_terraform_export": True
            }
        
        logger.info(f"✅ Found {len(tf_files)} Terraform files")
        logger.info(f"🔍 Files: {', '.join([f.name for f in tf_files[:5]])}{'...' if len(tf_files) > 5 else ''}")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean previous reports
        logger.info("🗑️  Cleaning previous reports...")
        cleaned_count = 0
        for md_file in self.output_dir.glob("*.md"):
            logger.info(f"   Removing: {md_file.name}")
            md_file.unlink()
            cleaned_count += 1
        logger.info(f"✅ Cleaned {cleaned_count} previous report(s)")
        
        # Define fixed agent labels for the three analysis phases
        agent_labels = {
            'terraform_reader': '🔍 Terraform Analysis',
            'ucx_analyst': '🔄 UCX Assessment',
            'report_generator': '📋 Consolidated Report'
        }
        
        if callback:
            for i, agent_name in enumerate(agents_list, 1):
                label = agent_labels.get(agent_name, f"🤖 {agent_name}")
                await callback("log", "agents", None, f"Phase {i}: {label}")
        
        # Set environment
        env = os.environ.copy()
        env["SELECTED_AGENTS"] = selected_agents
        env["REPORT_LANGUAGE"] = report_language
        env["PROJECT_ROOT"] = str(BASE_DIR)  # Ensure agent uses same base path as backend
        
        # Critical: Drop unsupported parameters for Databricks models
        env["LITELLM_DROP_PARAMS"] = "True"
        
        logger.info("🔍 Environment variables:")
        logger.info(f"   SELECTED_AGENTS: {selected_agents}")
        logger.info(f"   REPORT_LANGUAGE: {report_language}")
        logger.info(f"   PROJECT_ROOT: {env['PROJECT_ROOT']}")
        logger.info(f"   DATABRICKS_HOST: {'SET' if env.get('DATABRICKS_HOST') else 'NOT SET'}")
        logger.info(f"   DATABRICKS_TOKEN: {'SET' if env.get('DATABRICKS_TOKEN') else 'NOT SET'}")
        logger.info(f"   LITELLM_DROP_PARAMS: {env.get('LITELLM_DROP_PARAMS')}")
        
        # Execute agents
        logger.info(f"🚀 Executing AI agents (will use UV if available, otherwise direct Python)")
        logger.info(f"   Working directory: {self.agent_dir}")
        
        try:
            # Windows: Use synchronous subprocess to avoid asyncio issues
            if platform.system() == "Windows":
                logger.info("⚠️  Windows: Using synchronous subprocess in thread pool")
                import subprocess
                import concurrent.futures
                
                def run_subprocess_sync():
                    """Run subprocess synchronously and return process object"""
                    # Always use direct Python on Windows (simpler, more reliable)
                    logger.info("Windows: Using direct Python execution")
                    run_script = self.agent_dir / "run.py"
                    if not run_script.exists():
                        raise FileNotFoundError(f"Agent run script not found at {run_script}")
                    
                    cmd = [sys.executable, str(run_script)]
                    
                    proc = subprocess.Popen(
                        cmd,
                        cwd=str(self.agent_dir),  # Run from ai_agent directory
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        env=env,
                        text=True,
                        encoding='utf-8',
                        errors='replace',
                        bufsize=1,
                        shell=False
                    )
                    return proc
                
                # Run subprocess creation in thread
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    process_sync = await loop.run_in_executor(executor, run_subprocess_sync)
                
                logger.info(f"✅ Process started with PID: {process_sync.pid}")
                
                # Stream output line by line
                detected_agents = set()
                for line in process_sync.stdout:
                    decoded = line.strip()
                    if decoded:
                        logger.info(f"AGENTS: {decoded}")
                        
                        # Detect agent changes
                        for agent_name in agents_list:
                            if agent_name in decoded.lower() and agent_name not in detected_agents:
                                detected_agents.add(agent_name)
                                label = agent_labels.get(agent_name, agent_name)
                                if callback:
                                    await callback("log", "agents", None, f"{label} - Active")
                                break
                        
                        # Send important logs (capture phase transitions and key events)
                        if any(kw in decoded.lower() for kw in ['starting', 'completed', 'analyzing', 'generating', 'fase', 'phase', '✅', '📋']):
                            if callback:
                                await callback("log", "agents", None, decoded[:200])
                
                # Wait for completion
                returncode = process_sync.wait()
                
                class FakeProcess:
                    """Fake process object to match Unix behavior"""
                    def __init__(self, rc):
                        self.returncode = rc
                
                process = FakeProcess(returncode)
                
            else:
                # Unix: Use async subprocess
                logger.info("Unix/Mac/Databricks: Using direct Python execution")
                run_script = self.agent_dir / "run.py"
                if not run_script.exists():
                    raise FileNotFoundError(f"Agent run script not found at {run_script}")
                
                cmd = [sys.executable, str(run_script)]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=self.agent_dir,  # Run from ai_agent directory
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                
                logger.info(f"✅ Process started with PID: {process.pid}")
                
                # Unix: Stream output with dynamic agent detection
                current_agent = None
                detected_agents = set()
                
                async def stream_agents_output(stream, prefix):
                    nonlocal current_agent
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        decoded = line.decode().strip()
                        if decoded:
                            logger.info(f"{prefix}: {decoded}")
                            
                            # Detect agent changes dynamically
                            for agent_name in agents_list:
                                if agent_name in decoded.lower() and agent_name not in detected_agents:
                                    detected_agents.add(agent_name)
                                    label = agent_labels.get(agent_name, agent_name)
                                    if callback:
                                        await callback("log", "agents", None, f"{label} - Active")
                                    break
                            
                            # Send important logs (capture phase transitions and key events)
                            if any(kw in decoded.lower() for kw in ['starting', 'completed', 'analyzing', 'generating', 'fase', 'phase', '✅', '📋']):
                                if callback:
                                    await callback("log", "agents", None, decoded[:200])
                
                await asyncio.gather(
                    stream_agents_output(process.stdout, "AGENTS"),
                    stream_agents_output(process.stderr, "AGENTS-ERR")
                )
                
                await process.wait()
            
            logger.info(f"🔍 Process completed with exit code: {process.returncode}")
            
            if process.returncode == 0:
                logger.info("🔍 Checking for generated report files...")
                
                # Verify report was generated
                report_files = list(self.output_dir.glob("*.md"))
                logger.info(f"🔍 Found {len(report_files)} .md files in {self.output_dir}")
                
                if report_files:
                    report_file = report_files[0]
                    file_size = report_file.stat().st_size
                    
                    logger.info(f"✅ Report generated successfully:")
                    logger.info(f"   📄 File: {report_file.name}")
                    logger.info(f"   💾 Size: {file_size} bytes ({file_size/1024:.1f} KB)")
                    logger.info(f"   📂 Path: {report_file}")
                    
                    # Read first few lines for verification
                    try:
                        with open(report_file, 'r') as f:
                            first_lines = f.readlines()[:5]
                        logger.info(f"   📝 First lines preview: {len(first_lines)} lines")
                        for i, line in enumerate(first_lines, 1):
                            logger.info(f"      {i}: {line.strip()[:80]}")
                    except Exception as e:
                        logger.warning(f"   ⚠️  Could not preview file: {e}")
                    
                    if callback:
                        await callback("status", "agents", "completed",
                                     f"✅ AI analysis completed - Report: {report_file.name} ({file_size/1024:.1f} KB)")
                    
                    return {
                        "success": True,
                        "report_file": str(report_file),
                        "report_size": file_size,
                        "exit_code": process.returncode
                    }
                else:
                    error_msg = "❌ Report was not generated"
                    logger.error(error_msg)
                    logger.error(f"🔍 Output directory: {self.output_dir}")
                    logger.error(f"🔍 Directory exists: {self.output_dir.exists()}")
                    
                    # List all files in output directory
                    try:
                        all_files = list(self.output_dir.glob("*"))
                        logger.error(f"🔍 Files in output directory ({len(all_files)}):")
                        for f in all_files:
                            logger.error(f"   - {f.name} ({f.stat().st_size} bytes)")
                    except Exception as e:
                        logger.error(f"🔍 Error listing directory: {e}")
                    
                    # Check for common issues
                    logger.error("🔍 Possible causes:")
                    logger.error("   1. Agent failed to write report")
                    logger.error("   2. FileWriterTool not working")
                    logger.error("   3. Report written to wrong directory")
                    logger.error("   4. Permissions issue")
                    
                    if callback:
                        await callback("status", "agents", "error", error_msg)
                    return {"success": False, "error": error_msg}
            else:
                error_msg = f"❌ AI analysis failed with exit code {process.returncode}"
                logger.error(error_msg)
                logger.error(f"🔍 Exit code indicates process failure")
                
                # Try to capture more error details from logs
                try:
                    if self.agent_dir.exists():
                        log_files = list(self.agent_dir.glob("**/*.log"))
                        if log_files:
                            logger.error(f"🔍 Found {len(log_files)} log files:")
                            for log_file in log_files:
                                logger.error(f"   - {log_file}")
                except Exception as e:
                    logger.error(f"🔍 Error checking logs: {e}")
                
                if callback:
                    await callback("status", "agents", "error", error_msg)
                return {"success": False, "error": error_msg, "exit_code": process.returncode}
                
        except Exception as e:
            import traceback
            error_msg = f"❌ Exception during AI analysis: {str(e)}"
            logger.error(error_msg)
            logger.error("🔍 Full traceback:")
            logger.error(traceback.format_exc())
            
            # Additional debugging info
            logger.error("🔍 Debug information:")
            logger.error(f"   Agent directory: {self.agent_dir}")
            logger.error(f"   Output directory: {self.output_dir}")
            logger.error(f"   Selected agents: {selected_agents}")
            logger.error(f"   Environment SELECTED_AGENTS: {os.getenv('SELECTED_AGENTS', 'NOT SET')}")
            
            if callback:
                await callback("status", "agents", "error", f"{error_msg}\nCheck backend logs for details")
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# Convenience function for full pipeline
async def run_full_pipeline(
    run_terraform: bool = True,
    run_agents: bool = True,
    terraform_services: str = "groups,secrets,access,compute,users,jobs,storage",
    terraform_listing: str = "jobs,compute",
    terraform_debug: bool = False,
    selected_agents: str = "terraform_reader,databricks_specialist,ucx_analyst,report_generator",
    callback: Optional[Callable] = None
) -> dict:
    """
    Run the complete pipeline: Terraform export + AI analysis.
    
    Args:
        run_terraform: Whether to run Terraform export
        run_agents: Whether to run AI agents
        terraform_services: Services to export
        terraform_listing: Listing options
        terraform_debug: Enable debug mode
        selected_agents: Which agents to run
        callback: Callback for real-time updates
    
    Returns:
        Dictionary with results from both stages
    """
    results = {}
    
    if run_terraform:
        exporter = TerraformExporter()
        terraform_result = await exporter.run(
            services=terraform_services,
            listing=terraform_listing,
            debug=terraform_debug,
            callback=callback
        )
        results["terraform"] = terraform_result
        
        if not terraform_result["success"]:
            logger.error("Terraform export failed, skipping AI analysis")
            return results
    
    if run_agents:
        analyzer = AIAgentsAnalyzer()
        agents_result = await analyzer.run(
            selected_agents=selected_agents,
            callback=callback
        )
        results["agents"] = agents_result
    
    return results

