"""
Terraform Summarizer - Extrai resumo estatístico dos arquivos Terraform
para reduzir o consumo de tokens no LLM
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any
import json


class TerraformSummarizer:
    """Extrai resumo estatístico de arquivos Terraform"""
    
    def __init__(self, directory_path: str):
        self.directory_path = Path(directory_path)
        self.summary = {}
        
    def analyze_directory(self) -> Dict[str, Any]:
        """Analisa todos os arquivos .tf no diretório e retorna resumo"""
        
        # Encontrar todos os arquivos .tf
        tf_files = list(self.directory_path.glob("*.tf"))
        
        summary = {
            "total_files": len(tf_files),
            "resources_by_type": {},
            "data_sources": {},
            "total_resources": 0,
            "total_data_sources": 0,
            "configurations_summary": {},
            "notebooks_count": 0,
            "python_files": 0,
            "sql_files": 0,
        }
        
        # Contar notebooks
        notebooks_dir = self.directory_path / "notebooks"
        if notebooks_dir.exists():
            summary["notebooks_count"] = len(list(notebooks_dir.rglob("*.py"))) + len(list(notebooks_dir.rglob("*.sql")))
            summary["python_files"] = len(list(notebooks_dir.rglob("*.py")))
            summary["sql_files"] = len(list(notebooks_dir.rglob("*.sql")))
        
        # Analisar cada arquivo .tf
        for tf_file in tf_files:
            file_summary = self._analyze_file(tf_file)
            
            # Agregar recursos por tipo
            for resource_type, count in file_summary["resources"].items():
                summary["resources_by_type"][resource_type] = \
                    summary["resources_by_type"].get(resource_type, 0) + count
                summary["total_resources"] += count
            
            # Agregar data sources
            for data_type, count in file_summary["data_sources"].items():
                summary["data_sources"][data_type] = \
                    summary["data_sources"].get(data_type, 0) + count
                summary["total_data_sources"] += count
            
            # Extrair configurações importantes
            if file_summary["key_configs"]:
                summary["configurations_summary"][tf_file.stem] = file_summary["key_configs"]
        
        return summary
    
    def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analisa um arquivo .tf individual"""
        
        file_summary = {
            "resources": {},
            "data_sources": {},
            "key_configs": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Contar recursos: resource "tipo" "nome"
            resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"'
            resources = re.findall(resource_pattern, content)
            for resource_type, _ in resources:
                file_summary["resources"][resource_type] = \
                    file_summary["resources"].get(resource_type, 0) + 1
            
            # Contar data sources: data "tipo" "nome"
            data_pattern = r'data\s+"([^"]+)"\s+"([^"]+)"'
            data_sources = re.findall(data_pattern, content)
            for data_type, _ in data_sources:
                file_summary["data_sources"][data_type] = \
                    file_summary["data_sources"].get(data_type, 0) + 1
            
            # Extrair configurações chave baseado no tipo de arquivo
            if "cluster" in file_path.stem or "compute" in file_path.stem:
                file_summary["key_configs"].extend(self._extract_cluster_configs(content))
            elif "job" in file_path.stem:
                file_summary["key_configs"].extend(self._extract_job_configs(content))
            elif "sql" in file_path.stem or "warehouse" in file_path.stem:
                file_summary["key_configs"].extend(self._extract_sql_configs(content))
            elif "user" in file_path.stem or "group" in file_path.stem:
                file_summary["key_configs"].extend(self._extract_user_configs(content))
                
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
        
        return file_summary
    
    def _extract_cluster_configs(self, content: str) -> List[str]:
        """Extrai configurações chave de clusters"""
        configs = []
        
        # Detectar autoscaling
        if "autoscale" in content:
            configs.append("Has autoscaling configured")
        
        # Detectar node types
        node_types = re.findall(r'node_type_id\s*=\s*"([^"]+)"', content)
        if node_types:
            unique_types = set(node_types)
            configs.append(f"Node types used: {', '.join(list(unique_types)[:5])}")
        
        # Detectar runtime versions
        runtimes = re.findall(r'spark_version\s*=\s*"([^"]+)"', content)
        if runtimes:
            unique_runtimes = set(runtimes)
            configs.append(f"Databricks runtimes: {', '.join(list(unique_runtimes)[:5])}")
        
        return configs
    
    def _extract_job_configs(self, content: str) -> List[str]:
        """Extrai configurações chave de jobs"""
        configs = []
        
        # Contar tasks
        task_count = len(re.findall(r'task\s*{', content))
        if task_count > 0:
            configs.append(f"Total tasks across jobs: {task_count}")
        
        # Detectar schedules
        schedules = re.findall(r'quartz_cron_expression\s*=\s*"([^"]+)"', content)
        if schedules:
            configs.append(f"Scheduled jobs: {len(schedules)}")
        
        # Detectar email notifications
        if "email_notifications" in content:
            configs.append("Email notifications configured")
        
        return configs
    
    def _extract_sql_configs(self, content: str) -> List[str]:
        """Extrai configurações de SQL Warehouses"""
        configs = []
        
        # Detectar cluster sizes
        sizes = re.findall(r'cluster_size\s*=\s*"([^"]+)"', content)
        if sizes:
            unique_sizes = set(sizes)
            configs.append(f"SQL Warehouse sizes: {', '.join(unique_sizes)}")
        
        # Detectar auto_stop
        if "auto_stop_mins" in content:
            configs.append("Auto-stop configured")
        
        return configs
    
    def _extract_user_configs(self, content: str) -> List[str]:
        """Extrai configurações de usuários e grupos"""
        configs = []
        
        # Contar admins
        if "admins" in content.lower():
            admin_count = len(re.findall(r'group_name\s*=\s*"admins"', content, re.IGNORECASE))
            if admin_count > 0:
                configs.append(f"Admin group members: {admin_count}")
        
        return configs
    
    def generate_text_summary(self, summary: Dict[str, Any]) -> str:
        """Gera um resumo em texto legível para o LLM"""
        
        lines = [
            "=" * 80,
            "TERRAFORM INFRASTRUCTURE SUMMARY",
            "=" * 80,
            "",
            f"📁 Total Terraform files: {summary['total_files']}",
            f"📊 Total resources defined: {summary['total_resources']}",
            f"📋 Total data sources: {summary['total_data_sources']}",
            "",
            "=" * 80,
            "RESOURCES BY TYPE",
            "=" * 80,
            ""
        ]
        
        # Listar recursos por tipo, ordenados por quantidade
        sorted_resources = sorted(
            summary["resources_by_type"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for resource_type, count in sorted_resources:
            lines.append(f"  • {resource_type}: {count}")
        
        lines.extend(["", "=" * 80, "CODE FILES", "=" * 80, ""])
        lines.append(f"  • Python notebooks (.py): {summary['python_files']}")
        lines.append(f"  • SQL scripts (.sql): {summary['sql_files']}")
        lines.append(f"  • Total notebook files: {summary['notebooks_count']}")
        
        # Configurações importantes
        if summary["configurations_summary"]:
            lines.extend(["", "=" * 80, "KEY CONFIGURATIONS", "=" * 80, ""])
            
            for file_name, configs in summary["configurations_summary"].items():
                if configs:
                    lines.append(f"\n{file_name}.tf:")
                    for config in configs:
                        lines.append(f"  • {config}")
        
        lines.extend(["", "=" * 80, ""])
        
        return "\n".join(lines)


def summarize_terraform_directory(directory_path: str) -> str:
    """Função helper para resumir um diretório Terraform"""
    summarizer = TerraformSummarizer(directory_path)
    summary = summarizer.analyze_directory()
    return summarizer.generate_text_summary(summary)


if __name__ == "__main__":
    # Teste
    import sys
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        # Example: directory = "/path/to/your/databricks_tf_files"
        directory = os.path.join(os.path.dirname(__file__), '../../../..', 'databricks_tf_files')
    
    summary = summarize_terraform_directory(directory)
    print(summary)

