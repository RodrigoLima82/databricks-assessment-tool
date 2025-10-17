"""
Custom tool para resumir arquivos Terraform sem exceder rate limits
"""
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import sys
from pathlib import Path

# Adicionar o path do módulo
sys.path.insert(0, str(Path(__file__).parent.parent))
from terraform_summarizer import summarize_terraform_directory


class TerraformSummaryToolInput(BaseModel):
    """Input schema for TerraformSummaryTool."""
    directory: str = Field(..., description="Path to the directory containing Terraform files")


class TerraformSummaryTool(BaseTool):
    name: str = "Terraform Directory Summarizer"
    description: str = (
        "Analyzes a directory of Terraform files and returns a statistical summary "
        "including resource counts, configurations, and key metrics WITHOUT reading "
        "all file contents. This tool is optimized to reduce token usage by providing "
        "only the essential information needed for infrastructure assessment."
    )
    args_schema: Type[BaseModel] = TerraformSummaryToolInput

    def _run(self, directory: str) -> str:
        """
        Executa o resumo do diretório Terraform
        
        Args:
            directory: Path to Terraform directory
            
        Returns:
            Text summary of the infrastructure
        """
        try:
            summary = summarize_terraform_directory(directory)
            return summary
        except Exception as e:
            return f"Error summarizing Terraform directory: {str(e)}"

