"""
Dynamic Agent Registry - Reads agents from YAML configuration
Supports user-created agents without code changes
"""

import yaml
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Registry for dynamically managing agents from YAML configuration"""
    
    def __init__(self):
        self.config_path = Path(__file__).parent / "config" / "agents.yaml"
        self.tasks_config_path = Path(__file__).parent / "config" / "tasks.yaml"
        self._agents = None
        self._tasks = None
    
    def load_agents(self) -> Dict:
        """Load all agents from agents.yaml"""
        if self._agents is None:
            try:
                with open(self.config_path, 'r') as f:
                    self._agents = yaml.safe_load(f)
                logger.info(f"✅ Loaded {len(self._agents)} agents from configuration")
            except Exception as e:
                logger.error(f"Error loading agents: {e}")
                self._agents = {}
        return self._agents
    
    def load_tasks(self) -> Dict:
        """Load all tasks from tasks.yaml"""
        if self._tasks is None:
            try:
                with open(self.tasks_config_path, 'r') as f:
                    self._tasks = yaml.safe_load(f)
                logger.info(f"✅ Loaded {len(self._tasks)} tasks from configuration")
            except Exception as e:
                logger.error(f"Error loading tasks: {e}")
                self._tasks = {}
        return self._tasks
    
    def get_agent_names(self) -> List[str]:
        """Get list of all available agent names"""
        agents = self.load_agents()
        return list(agents.keys())
    
    def get_agent_label(self, agent_name: str) -> str:
        """Get human-readable label for an agent"""
        agents = self.load_agents()
        if agent_name in agents:
            role = agents[agent_name].get('role', agent_name)
            # Add icon based on agent name patterns
            if 'terraform' in agent_name.lower() or 'analysis' in role.lower():
                icon = '🔍'
            elif 'databricks' in agent_name.lower() or 'optimization' in role.lower():
                icon = '🛡️'
            elif 'ucx' in agent_name.lower() or 'migration' in role.lower():
                icon = '📈'
            elif 'report' in agent_name.lower() or 'documentation' in role.lower():
                icon = '📝'
            else:
                icon = '🤖'
            
            return f"{icon} {role}"
        return f"🤖 {agent_name}"
    
    def get_all_agent_labels(self) -> Dict[str, str]:
        """Get mapping of agent names to their labels"""
        agents = self.load_agents()
        return {name: self.get_agent_label(name) for name in agents.keys()}
    
    def get_task_for_agent(self, agent_name: str) -> str:
        """Get the corresponding task name for an agent"""
        tasks = self.load_tasks()
        
        # Explicit mapping for known agents
        agent_to_task_map = {
            'terraform_reader': 'read_terraform_files_task',
            'databricks_specialist': 'databricks_assessment',
            'ucx_analyst': 'analyze_ucx_assessment',
            'report_generator': 'generate_report_task'
        }
        
        # Check explicit mapping first
        if agent_name in agent_to_task_map:
            task_name = agent_to_task_map[agent_name]
            if task_name in tasks:
                return task_name
        
        # Try direct match
        if agent_name in tasks:
            return agent_name
        
        # Try with _task suffix
        task_name = f"{agent_name}_task"
        if task_name in tasks:
            return task_name
        
        # Try common patterns - check if agent name is part of task name
        for task_key in tasks.keys():
            # Check if agent name (without special chars) is in task name
            agent_clean = agent_name.replace('_', '').lower()
            task_clean = task_key.replace('_', '').lower()
            if agent_clean in task_clean:
                return task_key
        
        # Last resort: return first task or agent_name
        logger.warning(f"No task found for agent '{agent_name}', using agent name")
        return agent_name
    
    def is_report_generator(self, agent_name: str) -> bool:
        """Check if an agent is a report generator type"""
        agents = self.load_agents()
        if agent_name in agents:
            role = agents[agent_name].get('role', '').lower()
            goal = agents[agent_name].get('goal', '').lower()
            return 'report' in role or 'documentation' in role or 'report' in goal
        return 'report' in agent_name.lower()
    
    def get_default_agents(self) -> List[str]:
        """Get list of default agents (all available)"""
        return self.get_agent_names()


# Global instance
agent_registry = AgentRegistry()

