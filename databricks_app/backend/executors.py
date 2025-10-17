"""
Execution modules for Terraform export and AI agents analysis.
Replaces shell scripts with Python for better integration and maintainability.
"""

import os
import sys
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
AGENT_DIR = BASE_DIR / "databricks_summary_agent"

# Load environment variables from .env file
env_file = BASE_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)
    logger.info(f"✅ Loaded environment variables from {env_file}")
else:
    logger.warning(f"⚠️  .env file not found at {env_file}")


class TerraformExporter:
    """Handles Terraform export operations"""
    
    def __init__(self):
        self.exporter_binary = (
            BASE_DIR / ".terraform" / "providers" / "registry.terraform.io" / 
            "databricks" / "databricks" / "1.91.0" / "darwin_arm64" / 
            "terraform-provider-databricks_v1.91.0"
        )
        
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
        if not self.exporter_binary.exists():
            error_msg = f"Exporter binary not found at {self.exporter_binary}"
            logger.error(error_msg)
            if callback:
                await callback("status", "terraform", "error", error_msg)
            return {"success": False, "error": error_msg}
        
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
            
            if process.returncode == 0:
                # Count exported files
                tf_files = list(TF_FILES_DIR.glob("*.tf"))
                logger.info(f"✅ Successfully exported {len(tf_files)} Terraform files")
                
                if callback:
                    await callback("status", "terraform", "completed",
                                 f"✅ Terraform export completed ({len(tf_files)} files)")
                
                return {
                    "success": True,
                    "files_count": len(tf_files),
                    "exit_code": process.returncode
                }
            else:
                error_msg = f"Exporter failed with exit code {process.returncode}"
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
        self.agent_dir = AGENT_DIR
        self.output_dir = OUTPUT_DIR
        
    async def run(
        self,
        selected_agents: str = "terraform_reader,databricks_specialist,ucx_analyst,report_generator",
        callback: Optional[Callable] = None
    ) -> dict:
        """
        Execute AI agents analysis.
        
        Args:
            selected_agents: Comma-separated list of agent names
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
        
        # Only verify Terraform files if terraform_reader agent is selected
        if 'terraform_reader' in agents_list:
            logger.info(f"🔍 Checking for Terraform files in: {TF_FILES_DIR}")
            tf_files = list(TF_FILES_DIR.glob("*.tf"))
            
            if not tf_files:
                error_msg = f"❌ No Terraform files found in {TF_FILES_DIR}. Run export first."
                logger.error(error_msg)
                logger.error(f"🔍 TF_FILES_DIR exists: {TF_FILES_DIR.exists()}")
                
                # List what's actually there
                try:
                    all_files = list(TF_FILES_DIR.glob("*"))
                    logger.error(f"🔍 Files in directory ({len(all_files)}):")
                    for f in all_files[:10]:  # Show first 10
                        logger.error(f"   - {f.name}")
                except Exception as e:
                    logger.error(f"🔍 Error listing directory: {e}")
                
                if callback:
                    await callback("status", "agents", "error", error_msg)
                return {"success": False, "error": error_msg}
            
            logger.info(f"✅ Found {len(tf_files)} Terraform files")
            logger.info(f"🔍 Files: {', '.join([f.name for f in tf_files[:5]])}{'...' if len(tf_files) > 5 else ''}")
        else:
            logger.info("ℹ️  Terraform reader agent not selected, skipping TF files validation")
        
        # Clean previous reports
        logger.info("🗑️  Cleaning previous reports...")
        cleaned_count = 0
        for md_file in self.output_dir.glob("*.md"):
            logger.info(f"   Removing: {md_file.name}")
            md_file.unlink()
            cleaned_count += 1
        logger.info(f"✅ Cleaned {cleaned_count} previous report(s)")
        
        # Load agent labels dynamically
        try:
            import sys
            sys.path.insert(0, str(AGENT_DIR / "src"))
            from terraform_file_summary_agent.agent_registry import agent_registry
            agent_labels = agent_registry.get_all_agent_labels()
        except Exception as e:
            logger.warning(f"Could not load agent labels dynamically: {e}")
            # Fallback: use agent names as labels
            agent_labels = {name: f"🤖 {name}" for name in agents_list}
        
        if callback:
            for i, agent_name in enumerate(agents_list, 1):
                label = agent_labels.get(agent_name, f"🤖 {agent_name}")
                await callback("log", "agents", None, f"Agent {i}: {label}")
        
        # Set environment
        env = os.environ.copy()
        env["SELECTED_AGENTS"] = selected_agents
        
        logger.info("🔍 Environment variables:")
        logger.info(f"   SELECTED_AGENTS: {selected_agents}")
        logger.info(f"   DATABRICKS_HOST: {'SET' if env.get('DATABRICKS_HOST') else 'NOT SET'}")
        logger.info(f"   DATABRICKS_TOKEN: {'SET' if env.get('DATABRICKS_TOKEN') else 'NOT SET'}")
        
        # Execute agents
        logger.info(f"🚀 Executing: uv run terraform_file_summary_agent run")
        logger.info(f"   Working directory: {self.agent_dir}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                "uv", "run", "terraform_file_summary_agent", "run",
                cwd=self.agent_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            logger.info(f"✅ Process started with PID: {process.pid}")
            
            # Stream output with dynamic agent detection
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
                        
                        # Send important logs
                        if any(kw in decoded.lower() for kw in ['starting', 'completed', 'analyzing', 'generating']):
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

