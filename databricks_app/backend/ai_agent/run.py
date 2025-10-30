#!/usr/bin/env python3
"""
Simple runner for the AI Agent
"""
import os
import sys
from pathlib import Path

# Get language from environment or default to pt-BR
language = os.getenv('REPORT_LANGUAGE', 'pt-BR')

# Import and run agent
try:
    from agent import SimpleDatabricksAgent
    
    print(f"\n{'='*80}")
    print(f"🤖 Starting Analysis (Language: {language})")
    print(f"{'='*80}\n")
    
    agent = SimpleDatabricksAgent(language=language)
    result = agent.run()
    
    if result.get('success'):
        print(f"\n✅ Analysis completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Analysis failed: {result.get('error')}")
        sys.exit(1)
        
except Exception as e:
    print(f"\n❌ Error running agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

