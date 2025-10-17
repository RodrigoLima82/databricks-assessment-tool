from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileWriterTool
from terraform_file_summary_agent.tools.terraform_summary_tool import TerraformSummaryTool
from terraform_file_summary_agent.tools.ucx_analyzer_tool import UCXAnalyzerTool
from terraform_file_summary_agent.agent_registry import agent_registry
import os
from openai import OpenAI

@CrewBase
class TerraformFileSummaryAgentCrew():
    """TerraformFileSummaryAgent crew"""
    
    def __init__(self):
        super().__init__()
        # Configure Databricks LLM
        self.llm = self._get_databricks_llm()
    
    def _get_databricks_llm(self) -> LLM:
        """
        Configure LLM to use Databricks Model Serving Endpoint.
        Uses LiteLLM's Databricks provider with proper environment variables.
        
        Returns:
            Configured LLM instance
        """
        databricks_host = os.getenv("DATABRICKS_HOST")
        databricks_token = os.getenv("DATABRICKS_TOKEN")
        databricks_endpoint = os.getenv("DATABRICKS_ENDPOINT", "/serving-endpoints/databricks-claude-sonnet-4-5/invocations")
        
        if not databricks_host or not databricks_token:
            raise ValueError(
                "DATABRICKS_HOST and DATABRICKS_TOKEN environment variables must be set. "
                "Please create a .env file with your Databricks credentials."
            )
        
        # Remove trailing slash from host
        databricks_host = databricks_host.rstrip('/')
        
        # Extract endpoint name from path like "serving-endpoints/databricks-claude-sonnet-4-5/invocations"
        endpoint_name = databricks_endpoint.split('/')[-2]
        
        # Set LiteLLM environment variables
        # IMPORTANT: DATABRICKS_API_BASE should end with /serving-endpoints (NO specific endpoint, NO /invocations)
        os.environ["DATABRICKS_API_BASE"] = f"{databricks_host}/serving-endpoints"
        os.environ["DATABRICKS_API_KEY"] = databricks_token
        
        print(f"🔗 Configuring LLM:")
        print(f"   API Base: {os.environ['DATABRICKS_API_BASE']}")
        print(f"   Endpoint: {endpoint_name}")
        
        # Return LLM configured for Databricks
        # LiteLLM will automatically construct: {DATABRICKS_API_BASE}/{endpoint_name}/invocations
        return LLM(
            model=f"databricks/{endpoint_name}",
            temperature=0.7,
        )

    @agent
    def terraform_reader(self) -> Agent:
        return Agent(
            config=self.agents_config['terraform_reader'],
            llm=self.llm,
        )
    
    @agent
    def databricks_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['databricks_specialist'],
            llm=self.llm,
        )

    @agent
    def ucx_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['ucx_analyst'],
            llm=self.llm,
        )

    @agent
    def report_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['report_generator'],
            llm=self.llm,
        )


    @task
    def read_terraform_files_task(self) -> Task:
        return Task(
            config=self.tasks_config['read_terraform_files_task'],
            tools=[TerraformSummaryTool(), FileWriterTool()],
        )
    
    @task
    def databricks_assessment(self) -> Task:
        return Task(
            config=self.tasks_config['databricks_assessment'],
            tools=[FileWriterTool()],
        )

    @task
    def analyze_ucx_assessment(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_ucx_assessment'],
            tools=[UCXAnalyzerTool(), FileWriterTool()],
        )

    @task
    def generate_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_report_task'],
            tools=[FileWriterTool()],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the TerraformFileSummaryAgent crew"""
        return Crew(
            agents=self.agents, 
            tasks=self.tasks, 
            process=Process.sequential,
            verbose=True,
            track_usage=True
        )
    
    def create_custom_crew(self, selected_agents: list = None) -> Crew:
        """
        Creates a custom crew with only selected agents - FULLY DYNAMIC.
        Supports user-created agents without code changes.
        
        Args:
            selected_agents: List of agent names to include (e.g., ['terraform_reader', 'report_generator'])
                           If None, includes all available agents from config.
        
        Returns:
            Crew instance with selected agents and their corresponding tasks
        """
        # Load all available agents dynamically
        available_agents = agent_registry.get_agent_names()
        
        if selected_agents is None:
            selected_agents = available_agents
        
        # Build list of selected agents and tasks dynamically
        selected_agent_objs = []
        selected_task_objs = []
        
        # Get all agent labels dynamically
        agent_labels = agent_registry.get_all_agent_labels()
        
        print(f"\n{'='*80}")
        print(f"🤖 Creating Dynamic AI Crew")
        print(f"{'='*80}")
        print(f"Available Agents: {len(available_agents)}")
        print(f"Selected Agents: {len(selected_agents)}")
        print(f"{'='*80}")
        
        # Dynamically create agents and tasks
        for i, agent_name in enumerate(selected_agents, 1):
            # Check if agent exists in configuration
            if agent_name not in self.agents_config:
                print(f"⚠️  Warning: Agent '{agent_name}' not found in configuration, skipping")
                continue
            
            # Find corresponding task FIRST
            task_name = agent_registry.get_task_for_agent(agent_name)
            
            if task_name not in self.tasks_config:
                print(f"  ⚠️  No task '{task_name}' found for agent '{agent_name}' - SKIPPING")
                print(f"      Available tasks: {list(self.tasks_config.keys())}")
                continue
            
            # Create agent dynamically
            agent_obj = Agent(
                config=self.agents_config[agent_name],
                llm=self.llm,
            )
            selected_agent_objs.append(agent_obj)
            
            # Determine tools based on task/agent name - ALL agents get FileWriterTool
            tools = [FileWriterTool()]  # All agents can save files
            
            if 'terraform' in agent_name.lower() and 'read' in task_name.lower():
                tools.append(TerraformSummaryTool())
            elif 'ucx' in agent_name.lower():
                tools.append(UCXAnalyzerTool())
            
            # Create task - for report_generator, pass previous tasks as context
            task_context = None
            
            # If this is report_generator, pass previously created tasks as context
            if agent_registry.is_report_generator(agent_name):
                if selected_task_objs:
                    task_context = selected_task_objs.copy()  # Pass all previous tasks
                    print(f"  📋 Dynamic context for report: {len(task_context)} previous task(s)")
                else:
                    print(f"  ⚠️  No context available for report - will generate based on instructions only")
            
            # Create task with or without context
            if task_context:
                task_obj = Task(
                    config=self.tasks_config[task_name],
                    tools=tools,
                    context=task_context,
                )
            else:
                task_obj = Task(
                    config=self.tasks_config[task_name],
                    tools=tools,
                )
            
            selected_task_objs.append(task_obj)
            
            tools_str = f" + {len(tools)} tool(s)" if tools else ""
            print(f"  ✓ {i}. {agent_labels.get(agent_name, agent_name)} → {task_name}{tools_str}")
        
        print(f"{'='*80}")
        print(f"📊 Summary:")
        print(f"   Agents created: {len(selected_agent_objs)}")
        print(f"   Tasks created: {len(selected_task_objs)}")
        print(f"{'='*80}\n")
        
        if not selected_agent_objs:
            error_msg = f"No valid agents created! Selected: {selected_agents}, Available: {available_agents}"
            print(f"❌ ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        if not selected_task_objs:
            error_msg = f"No valid tasks created! Agents: {selected_agents}"
            print(f"❌ ERROR: {error_msg}")
            raise ValueError(error_msg)
        
        if len(selected_agent_objs) != len(selected_task_objs):
            print(f"⚠️  WARNING: Agent count ({len(selected_agent_objs)}) != Task count ({len(selected_task_objs)})")
        
        return Crew(
            agents=selected_agent_objs,
            tasks=selected_task_objs,
            process=Process.sequential,
            verbose=True,
            track_usage=True
        )
