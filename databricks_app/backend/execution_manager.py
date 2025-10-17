"""
Execution Manager - Handles execution state, stop signals, and state persistence
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExecutionManager:
    """Manages execution state and stop signals"""
    
    def __init__(self):
        self.current_execution: Optional[asyncio.Task] = None
        self.stop_requested = False
        self.execution_state = {
            "running": False,
            "step": None,
            "progress": 0,
            "can_stop": False
        }
        self.last_config = {}
        
        # Path for state persistence
        self.state_file = Path(__file__).parent.parent.parent / "execution_state.json"
    
    def request_stop(self):
        """Request execution to stop"""
        logger.info("🛑 Stop requested by user")
        self.stop_requested = True
        self.execution_state["running"] = False
        return {"success": True, "message": "Stop requested"}
    
    def is_stop_requested(self) -> bool:
        """Check if stop was requested"""
        return self.stop_requested
    
    def reset_stop(self):
        """Reset stop flag for new execution"""
        self.stop_requested = False
    
    def set_execution_state(self, running: bool, step: Optional[str] = None, progress: int = 0):
        """Update execution state"""
        self.execution_state = {
            "running": running,
            "step": step,
            "progress": progress,
            "can_stop": running
        }
    
    def get_execution_state(self) -> Dict:
        """Get current execution state"""
        return self.execution_state.copy()
    
    def save_config(self, config: Dict):
        """Save execution configuration for re-use"""
        self.last_config = config.copy()
        self.last_config["timestamp"] = datetime.now().isoformat()
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.last_config, f, indent=2)
            logger.info(f"💾 Configuration saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def load_config(self) -> Dict:
        """Load last execution configuration"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"📂 Configuration loaded from {self.state_file}")
                return config
            else:
                logger.info("No saved configuration found")
                return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    def get_last_config(self) -> Dict:
        """Get last used configuration (from memory or file)"""
        if self.last_config:
            return self.last_config
        return self.load_config()


# Global instance
execution_manager = ExecutionManager()

