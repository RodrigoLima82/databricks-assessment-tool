#!/usr/bin/env python
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from terraform_file_summary_agent.crew import TerraformFileSummaryAgentCrew

# Load environment variables from .env file
# Try to load from the project root directory
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try to load from current directory
    load_dotenv()

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    Reads selected agents from SELECTED_AGENTS environment variable.
    """
    # Get paths from environment variables or use defaults relative to project root
    # main.py is in: dbr_export/databricks_summary_agent/src/terraform_file_summary_agent/main.py
    # Project root (dbr_export) is 3 levels up: ../../..
    project_root = os.getenv('PROJECT_ROOT', os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    
    inputs = {
        'directory_path': os.getenv('TF_FILES_DIR', os.path.join(project_root, 'databricks_tf_files')),
        'output_file_path': os.getenv('OUTPUT_DIR', os.path.join(project_root, 'output_summary_agent')) + '/',
        'ucx_directory': os.getenv('UCX_DIR', os.path.join(project_root, 'ucx_export'))
    }
    
    crew_instance = TerraformFileSummaryAgentCrew()
    
    # Check if agents were passed via environment variable
    selected_agents = os.getenv('SELECTED_AGENTS')
    
    # If specific agents are selected, use custom crew
    if selected_agents and selected_agents.strip():
        agent_list = [a.strip() for a in selected_agents.split(',')]
        print(f"\n🎯 Running with selected agents: {agent_list}\n")
        
        crew = crew_instance.create_custom_crew(agent_list)
        print(f"🔍 Crew created with {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        print(f"🔍 Starting kickoff with inputs:")
        print(f"   - directory_path: {inputs['directory_path']}")
        print(f"   - output_file_path: {inputs['output_file_path']}")
        print(f"   - ucx_directory: {inputs['ucx_directory']}")
        print(f"\n{'='*80}")
        print(f"🚀 EXECUTING CREW...")
        print(f"{'='*80}\n")
        
        result = crew.kickoff(inputs=inputs)
        
        print(f"\n{'='*80}")
        print(f"✅ CREW EXECUTION COMPLETED")
        print(f"{'='*80}")
    else:
        # Run all agents
        print(f"\n🎯 Running with all agents\n")
        result = crew_instance.crew().kickoff(inputs=inputs)

    # Listar todas as propriedades do CrewOutput para entender o que está disponível
    print(">>>>>>>>>>>>>>>>>> Costs <<<<<<<<<<<<<<<<<")
    costs = 0.150 * (result.token_usage.prompt_tokens + result.token_usage.completion_tokens) / 1_000_000
    print(f"Total costs: ${costs:.4f}")
    print(result.token_usage)
    
    # More debug info
    print(f"\n>>>>>>>>>>>>>>>>>> Result Info <<<<<<<<<<<<<<<<<")
    print(f"Raw output length: {len(result.raw) if hasattr(result, 'raw') else 'N/A'}")
    print(f"Result type: {type(result)}")
    
    # Check if report was generated
    import glob
    reports = glob.glob(f"{inputs['output_file_path']}/*.md")
    print(f"\n>>>>>>>>>>>>>>>>>> Generated Files <<<<<<<<<<<<<<<<<")
    print(f"Reports found: {len(reports)}")
    for report in reports:
        print(f"  - {report}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'directory_path': 'sample_value',
        'output_file_path': 'sample_value'
    }
    try:
        TerraformFileSummaryAgentCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        TerraformFileSummaryAgentCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'directory_path': 'sample_value',
        'output_file_path': 'sample_value'
    }
    try:
        TerraformFileSummaryAgentCrew().crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [<args>]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
