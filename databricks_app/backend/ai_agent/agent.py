"""
Modern HTTP-based AI Agent for Databricks Assessment
Refactored for better maintainability and performance
"""
import os
import json
import re
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


# ============================================================================
# DATA CLASSES - Structured data models
# ============================================================================

@dataclass
class ResourceStats:
    """Holds statistics for all Databricks resources"""
    users: int = 0
    service_principals: int = 0
    groups: int = 0
    group_members: int = 0
    clusters: int = 0
    cluster_policies: int = 0
    jobs: int = 0
    notebooks: int = 0
    sql_endpoints: int = 0
    secrets: int = 0
    secret_scopes: int = 0
    permissions: int = 0
    repos: int = 0
    mounts: int = 0
    instance_pools: int = 0
    tokens: int = 0
    ip_access_lists: int = 0
    directories: int = 0
    uc_catalogs: int = 0
    uc_schemas: int = 0
    uc_tables: int = 0
    uc_volumes: int = 0
    uc_grants: int = 0
    uc_external_locations: int = 0
    uc_storage_credentials: int = 0
    uc_system_schemas: int = 0
    uc_models: int = 0
    uc_connections: int = 0
    uc_shares: int = 0
    uc_recipients: int = 0
    vector_search_indexes: int = 0
    vector_search_endpoints: int = 0
    dashboards: int = 0
    queries: int = 0
    alerts: int = 0
    workspace_files: int = 0
    workspace_bindings: int = 0
    model_serving_endpoints: int = 0
    dbfs_files: int = 0
    external_tables: int = 0
    workspace_conf: int = 0
    sql_global_config: int = 0
    notification_destinations: int = 0
    secret_acls: int = 0
    global_init_scripts: int = 0


@dataclass
class ResourceInventory:
    """Detailed inventory of resources with names/examples"""
    users: List[str] = field(default_factory=list)
    service_principals: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    clusters: List[str] = field(default_factory=list)
    cluster_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    cluster_policies: List[str] = field(default_factory=list)
    jobs: List[str] = field(default_factory=list)
    job_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    notebooks: List[str] = field(default_factory=list)
    notebook_languages: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    sql_endpoints: List[str] = field(default_factory=list)
    secret_scopes: List[str] = field(default_factory=list)
    uc_catalogs: List[str] = field(default_factory=list)
    uc_schemas: List[str] = field(default_factory=list)
    uc_tables: List[str] = field(default_factory=list)
    uc_table_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    uc_volumes: List[str] = field(default_factory=list)
    uc_external_locations: List[str] = field(default_factory=list)
    uc_storage_credentials: List[str] = field(default_factory=list)
    uc_models: List[str] = field(default_factory=list)
    vector_search_indexes: List[str] = field(default_factory=list)
    vector_search_endpoints: List[str] = field(default_factory=list)
    dashboards: List[str] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    workspace_files: List[str] = field(default_factory=list)
    workspace_file_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    model_serving_endpoints: List[str] = field(default_factory=list)
    dbfs_files: List[str] = field(default_factory=list)
    notification_destinations: List[str] = field(default_factory=list)
    global_init_scripts: List[str] = field(default_factory=list)


# ============================================================================
# CONTENT CLEANER - Clean LLM responses from JSON artifacts  
# ============================================================================

class ContentCleaner:
    """Clean LLM responses from JSON and formatting artifacts"""
    
    @staticmethod
    def clean_html_to_markdown(content: str) -> str:
        """Convert HTML tables to markdown tables"""
        import re
        
        # Strip all HTML tags except for content extraction
        if '<table' in content.lower() or '<th' in content.lower() or '<td' in content.lower():
            # Extract table rows
            tables = []
            table_pattern = re.compile(r'<table[^>]*>(.*?)</table>', re.IGNORECASE | re.DOTALL)
            
            for table_match in table_pattern.finditer(content):
                table_html = table_match.group(1)
                
                # Extract all rows
                row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.IGNORECASE | re.DOTALL)
                markdown_rows = []
                first_row = True
                
                for row_match in row_pattern.finditer(table_html):
                    row_html = row_match.group(1)
                    
                    # Extract cells (th or td)
                    cell_pattern = re.compile(r'<t[hd][^>]*>(.*?)</t[hd]>', re.IGNORECASE | re.DOTALL)
                    cells = []
                    
                    for cell_match in cell_pattern.finditer(row_html):
                        cell_content = cell_match.group(1).strip()
                        # Remove any remaining HTML tags
                        cell_content = re.sub(r'<[^>]+>', '', cell_content)
                        cells.append(cell_content)
                    
                    if cells:
                        # Create markdown row
                        markdown_row = '| ' + ' | '.join(cells) + ' |'
                        markdown_rows.append(markdown_row)
                        
                        # Add separator after first row (header)
                        if first_row:
                            separator = '|' + '---|' * len(cells)
                            markdown_rows.append(separator)
                            first_row = False
                
                # Replace HTML table with markdown table
                if markdown_rows:
                    markdown_table = '\n'.join(markdown_rows)
                    content = content.replace(table_match.group(0), '\n' + markdown_table + '\n')
        
        # Remove any remaining HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        return content
    
    @staticmethod
    def clean_json_response(content: str) -> str:
        """Aggressively clean JSON artifacts from LLM response"""
        # First clean HTML
        content = ContentCleaner.clean_html_to_markdown(content)
        
        content_stripped = content.strip()
        
        # Quick check: if it doesn't look like JSON, return as-is
        if not (content_stripped.startswith('{') or content_stripped.startswith('[')):
            return content
        
        # Try to parse and extract text from JSON
        try:
            parsed = json.loads(content)
            
            # Pattern 1: {'type': 'reasoning', 'summary': [{'type': 'summary_text', 'text': '...'}]}
            if isinstance(parsed, dict) and parsed.get('type') == 'reasoning':
                summary = parsed.get('summary', [])
                if isinstance(summary, list) and summary:
                    texts = [item['text'] for item in summary if isinstance(item, dict) and 'text' in item]
                    if texts:
                        return '\n\n'.join(texts)
            
            # Pattern 2: {'type': 'text', 'text': '...'}
            if isinstance(parsed, dict) and parsed.get('type') == 'text' and 'text' in parsed:
                return parsed['text']
            
            # Recursive extraction
            extracted = ContentCleaner._extract_text_recursive(parsed)
            if extracted and len(extracted) > 50:
                return extracted
        except:
            pass
        
        # Regex cleaning fallback
        cleaned = re.sub(r"^\s*\{'type':\s*'reasoning',\s*'summary':\s*\[.*?\]\}\s*", '', content, flags=re.DOTALL)
        cleaned = re.sub(r'^\s*{"type":\s*"reasoning",\s*"summary":\s*\[.*?\]\}\s*', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"{\s*['\"]type['\"]:\s*['\"]text['\"],\s*['\"]text['\"]:\s*['\"](.+?)['\"]}", r'\1', cleaned, flags=re.DOTALL)
        
        # Fix escaped characters
        cleaned = cleaned.replace('\\n\\n', '\n\n').replace('\\n', '\n').replace('\\t', '\t')
        
        # Remove Unicode artifacts
        cleaned = re.sub(r'\\u202f', '', cleaned)
        cleaned = re.sub(r'\\u00a0', ' ', cleaned)
        cleaned = re.sub(r'\\u[0-9a-fA-F]{4}', '', cleaned)
        
        return cleaned
    
    @staticmethod
    def _extract_text_recursive(obj):
        """Recursively extract text from nested structures"""
        if isinstance(obj, str):
            return obj
        elif isinstance(obj, dict):
            for key in ['text', 'content', 'markdown', 'summary_text']:
                if key in obj:
                    result = ContentCleaner._extract_text_recursive(obj[key])
                    if result and len(result) > 50:
                        return result
            
            if 'summary' in obj and isinstance(obj['summary'], list):
                texts = [ContentCleaner._extract_text_recursive(item) for item in obj['summary']]
                texts = [t for t in texts if t]
                if texts:
                    return '\n\n'.join(texts)
        elif isinstance(obj, list):
            texts = [ContentCleaner._extract_text_recursive(item) for item in obj]
            texts = [t for t in texts if t]
            if texts:
                return '\n\n'.join(texts)
        return None


# ============================================================================
# TERRAFORM PARSER - Extract resources from .tf files
# ============================================================================

class TerraformResourceExtractor:
    """Extract and parse Databricks resources from Terraform files"""
    
    @staticmethod
    def extract_value(lines: List[str], start_idx: int, key: str, max_lines: int = 10) -> Optional[str]:
        """Extract a value from Terraform file lines"""
        for i in range(start_idx, min(start_idx + max_lines, len(lines))):
            if key in lines[i] and '=' in lines[i]:
                match = re.search(rf'{key}\s*=\s*"([^"]+)"', lines[i])
                if match:
                    return match.group(1)
        return None
    
    @staticmethod
    def extract_users(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract user resources"""
        for i, line in enumerate(lines):
            if 'data "databricks_user"' in line or 'resource "databricks_user"' in line:
                stats.users += 1
                user_name = TerraformResourceExtractor.extract_value(lines, i+1, 'user_name')
                if user_name and len(inventory.users) < 100:
                    inventory.users.append(user_name)
    
    @staticmethod
    def extract_groups(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract group resources"""
        for i, line in enumerate(lines):
            if ('data "databricks_group"' in line or 'resource "databricks_group"' in line) and 'member' not in line:
                stats.groups += 1
                display_name = TerraformResourceExtractor.extract_value(lines, i+1, 'display_name')
                if display_name and len(inventory.groups) < 100:
                    inventory.groups.append(display_name)
    
    @staticmethod
    def extract_clusters(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract cluster resources"""
        for i, line in enumerate(lines):
            if ('resource "databricks_cluster"' in line or 'data "databricks_cluster"' in line) and 'policy' not in line:
                stats.clusters += 1
                cluster_name = TerraformResourceExtractor.extract_value(lines, i+1, 'cluster_name', 30)
                node_type = TerraformResourceExtractor.extract_value(lines, i+1, 'node_type_id', 30)
                
                if cluster_name and len(inventory.clusters) < 50:
                    inventory.clusters.append(cluster_name)
                if node_type:
                    inventory.cluster_types[node_type] += 1
    
    @staticmethod
    def extract_cluster_policies(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract cluster policy resources"""
        for i, line in enumerate(lines):
            if 'resource "databricks_cluster_policy"' in line or 'data "databricks_cluster_policy"' in line:
                stats.cluster_policies += 1
                policy_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 20)
                if policy_name and len(inventory.cluster_policies) < 50:
                    inventory.cluster_policies.append(policy_name)
    
    @staticmethod
    def extract_jobs(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract job resources"""
        for i, line in enumerate(lines):
            if 'resource "databricks_job"' in line or 'data "databricks_job"' in line:
                stats.jobs += 1
                
                # Extract job name and type
                for j in range(i+1, min(i+50, len(lines))):
                    if 'name' in lines[j] and '=' in lines[j] and 'task' not in lines[j]:
                        match = re.search(r'name\s*=\s*"([^"]+)"', lines[j])
                        if match and len(inventory.jobs) < 50:
                            inventory.jobs.append(match.group(1))
                    
                    # Detect job types
                    job_types_map = {
                        'notebook_task': 'Notebook',
                        'spark_jar_task': 'JAR',
                        'spark_python_task': 'Python',
                        'spark_submit_task': 'Spark Submit'
                    }
                    for task_key, task_name in job_types_map.items():
                        if task_key in lines[j]:
                            inventory.job_types[task_name] += 1
    
    @staticmethod
    def extract_notebooks(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract notebook resources"""
        for i, line in enumerate(lines):
            if 'resource "databricks_notebook"' in line or 'data "databricks_notebook"' in line:
                stats.notebooks += 1
                
                notebook_path = TerraformResourceExtractor.extract_value(lines, i+1, 'path', 15)
                notebook_lang = TerraformResourceExtractor.extract_value(lines, i+1, 'language', 15)
                
                # Add notebook only if not a Terraform variable and not duplicate
                if notebook_path and not notebook_path.startswith('${') and notebook_path not in inventory.notebooks:
                    if len(inventory.notebooks) < 200:
                        inventory.notebooks.append(notebook_path)
                
                if notebook_lang:
                    inventory.notebook_languages[notebook_lang.upper()] += 1
    
    @staticmethod
    def extract_sql_analytics(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract SQL Analytics resources (queries, dashboards, alerts, endpoints)"""
        # SQL Queries
        for i, line in enumerate(lines):
            if 'resource "databricks_query"' in line or 'data "databricks_query"' in line:
                stats.queries += 1
                query_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 20)
                if query_name and len(inventory.queries) < 100:
                    inventory.queries.append(query_name)
        
        # Dashboards
        for i, line in enumerate(lines):
            if 'resource "databricks_dashboard"' in line or 'data "databricks_dashboard"' in line:
                stats.dashboards += 1
                dashboard_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 20)
                if dashboard_name and len(inventory.dashboards) < 100:
                    inventory.dashboards.append(dashboard_name)
        
        # Alerts
        for i, line in enumerate(lines):
            if 'resource "databricks_alert"' in line or 'data "databricks_alert"' in line:
                stats.alerts += 1
                alert_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 20)
                if alert_name and len(inventory.alerts) < 100:
                    inventory.alerts.append(alert_name)
        
        # SQL Endpoints
        for i, line in enumerate(lines):
            if 'resource "databricks_sql_endpoint"' in line or 'data "databricks_sql_endpoint"' in line:
                stats.sql_endpoints += 1
    
    @staticmethod
    def extract_ml_resources(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract Machine Learning resources (models, model serving, vector search)"""
        # Registered Models
        for i, line in enumerate(lines):
            if 'resource "databricks_registered_model"' in line or 'data "databricks_registered_model"' in line:
                stats.uc_models += 1
                model_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 15)
                if model_name and len(inventory.uc_models) < 50:
                    inventory.uc_models.append(model_name)
        
        # Model Serving Endpoints
        for i, line in enumerate(lines):
            if 'resource "databricks_model_serving"' in line or 'data "databricks_model_serving"' in line:
                stats.model_serving_endpoints += 1
                endpoint_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 15)
                if endpoint_name and len(inventory.model_serving_endpoints) < 50:
                    inventory.model_serving_endpoints.append(endpoint_name)
        
        # Vector Search Indexes
        for i, line in enumerate(lines):
            if 'resource "databricks_vector_search_index"' in line or 'data "databricks_vector_search_index"' in line:
                stats.vector_search_indexes += 1
                index_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 15)
                if index_name and len(inventory.vector_search_indexes) < 50:
                    inventory.vector_search_indexes.append(index_name)
        
        # Vector Search Endpoints
        for i, line in enumerate(lines):
            if 'resource "databricks_vector_search_endpoint"' in line or 'data "databricks_vector_search_endpoint"' in line:
                stats.vector_search_endpoints += 1
                endpoint_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 15)
                if endpoint_name and len(inventory.vector_search_endpoints) < 50:
                    inventory.vector_search_endpoints.append(endpoint_name)
    
    @staticmethod
    def extract_secrets(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract Secret resources (scopes, secrets, ACLs)"""
        # Secret Scopes
        for i, line in enumerate(lines):
            if 'resource "databricks_secret_scope"' in line or 'data "databricks_secret_scope"' in line:
                stats.secret_scopes += 1
                scope_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 10)
                if scope_name and len(inventory.secret_scopes) < 50:
                    inventory.secret_scopes.append(scope_name)
        
        # Secrets (count only, don't list names for security)
        for i, line in enumerate(lines):
            if 'resource "databricks_secret"' in line:
                stats.secrets += 1
    
    @staticmethod
    def extract_workspace_resources(lines: List[str], stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract Workspace resources (files, directories, repos)"""
        # Workspace Files
        for i, line in enumerate(lines):
            if 'resource "databricks_workspace_file"' in line or 'data "databricks_workspace_file"' in line:
                stats.workspace_files += 1
                file_path = TerraformResourceExtractor.extract_value(lines, i+1, 'path', 10)
                if file_path and len(inventory.workspace_files) < 50:
                    inventory.workspace_files.append(file_path)
                    # Extract file extension
                    if '.' in file_path:
                        ext = file_path.split('.')[-1]
                        inventory.workspace_file_types[ext] += 1
        
        # Directories (count only)
        for i, line in enumerate(lines):
            if 'resource "databricks_directory"' in line or 'data "databricks_directory"' in line:
                stats.directories += 1
        
        # Repos
        for i, line in enumerate(lines):
            if 'resource "databricks_repo"' in line or 'data "databricks_repo"' in line:
                stats.repos += 1
    
    @staticmethod
    def extract_uc_resources(lines: List[str], content: str, stats: ResourceStats, inventory: ResourceInventory) -> None:
        """Extract Unity Catalog resources"""
        # Catalogs
        for i, line in enumerate(lines):
            if 'resource "databricks_catalog"' in line or 'data "databricks_catalog"' in line:
                stats.uc_catalogs += 1
                name = TerraformResourceExtractor.extract_value(lines, i+1, 'name')
                if name and len(inventory.uc_catalogs) < 50:
                    inventory.uc_catalogs.append(name)
        
        # Schemas
        for i, line in enumerate(lines):
            if 'resource "databricks_schema"' in line or 'data "databricks_schema"' in line:
                stats.uc_schemas += 1
                schema_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 15)
                catalog_name = TerraformResourceExtractor.extract_value(lines, i+1, 'catalog_name', 15)
                
                if schema_name and catalog_name and len(inventory.uc_schemas) < 100:
                    inventory.uc_schemas.append(f"{catalog_name}.{schema_name}")
                elif schema_name and len(inventory.uc_schemas) < 100:
                    inventory.uc_schemas.append(schema_name)
        
        # Tables (Unity Catalog)
        for i, line in enumerate(lines):
            # Support both databricks_table (UC managed) and databricks_sql_table (SQL tables)
            if ('resource "databricks_table"' in line or 'data "databricks_table"' in line or
                'resource "databricks_sql_table"' in line or 'data "databricks_sql_table"' in line):
                stats.uc_tables += 1
                
                # Try to extract table name, schema, catalog
                table_name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 25)
                schema_name = TerraformResourceExtractor.extract_value(lines, i+1, 'schema_name', 25)
                catalog_name = TerraformResourceExtractor.extract_value(lines, i+1, 'catalog_name', 25)
                table_type = TerraformResourceExtractor.extract_value(lines, i+1, 'table_type', 25)
                
                if table_type:
                    inventory.uc_table_types[table_type] += 1
                
                if table_name and schema_name and catalog_name and len(inventory.uc_tables) < 100:
                    inventory.uc_tables.append(f"{catalog_name}.{schema_name}.{table_name}")
                elif table_name and len(inventory.uc_tables) < 100:
                    inventory.uc_tables.append(table_name)
        
        # Volumes
        for i, line in enumerate(lines):
            if 'resource "databricks_volume"' in line or 'data "databricks_volume"' in line:
                stats.uc_volumes += 1
                name = TerraformResourceExtractor.extract_value(lines, i+1, 'name', 15)
                if name and len(inventory.uc_volumes) < 50:
                    inventory.uc_volumes.append(name)
        
        # Grants (count only)
        stats.uc_grants += content.count('resource "databricks_grants"')
        stats.uc_grants += content.count('data "databricks_grants"')
        
        # External Locations
        for i, line in enumerate(lines):
            if 'resource "databricks_external_location"' in line or 'data "databricks_external_location"' in line:
                stats.uc_external_locations += 1
        
        # Storage Credentials
        for i, line in enumerate(lines):
            if 'resource "databricks_storage_credential"' in line or 'data "databricks_storage_credential"' in line:
                stats.uc_storage_credentials += 1
        
        # System Schemas
        for i, line in enumerate(lines):
            if 'resource "databricks_system_schema"' in line or 'data "databricks_system_schema"' in line:
                stats.uc_system_schemas += 1
        
        # Recipients (Delta Sharing)
        for i, line in enumerate(lines):
            if 'resource "databricks_recipient"' in line or 'data "databricks_recipient"' in line:
                stats.uc_recipients += 1
    
    @staticmethod
    def extract_simple_counts(content: str, stats: ResourceStats) -> None:
        """Extract simple resource counts"""
        count_mappings = {
            'group_members': ['resource "databricks_group_member"', 'data "databricks_group_member"'],
            'secrets': ['resource "databricks_secret"', 'data "databricks_secret"'],
            'permissions': ['resource "databricks_permissions"', 'data "databricks_permissions"'],
            'repos': ['resource "databricks_repo"', 'data "databricks_repo"'],
            'mounts': ['resource "databricks_mount"', 'data "databricks_mount"'],
            'instance_pools': ['resource "databricks_instance_pool"', 'data "databricks_instance_pool"'],
            'tokens': ['resource "databricks_token"'],
            'ip_access_lists': ['resource "databricks_ip_access_list"', 'data "databricks_ip_access_list"'],
            'directories': ['resource "databricks_directory"', 'data "databricks_directory"'],
            'uc_connections': ['resource "databricks_connection"', 'data "databricks_connection"'],
            'uc_shares': ['resource "databricks_share"', 'data "databricks_share"'],
            'workspace_bindings': ['resource "databricks_workspace_binding"', 'data "databricks_workspace_binding"'],
            'workspace_conf': ['resource "databricks_workspace_conf"', 'data "databricks_workspace_conf"'],
            'sql_global_config': ['resource "databricks_sql_global_config"', 'data "databricks_sql_global_config"'],
            'notification_destinations': ['resource "databricks_notification_destination"', 'data "databricks_notification_destination"'],
            'secret_acls': ['resource "databricks_secret_acl"', 'data "databricks_secret_acl"'],
            'dbfs_files': ['resource "databricks_file"', 'data "databricks_file"'],
        }
        
        for stat_key, patterns in count_mappings.items():
            count = sum(content.count(pattern) for pattern in patterns)
            setattr(stats, stat_key, getattr(stats, stat_key) + count)


# ============================================================================
# REPORT FORMATTER - Generate markdown reports  
# ============================================================================

class ReportFormatter:
    """Format analysis results into structured markdown reports"""
    
    @staticmethod
    def format_identity_section(stats: ResourceStats, inventory: ResourceInventory, labels: Dict) -> List[str]:
        """Format identity and access control section"""
        lines = [f"\n## 1. {labels['section_identity']}\n"]
        
        # Users
        lines.append(f"### 👥 {labels['users_title']}: {stats.users} {labels['users_title'].lower()} totais")
        if inventory.users:
            domains = defaultdict(int)
            for user in inventory.users:
                if '@' in user:
                    domain = user.split('@')[1]
                    domains[domain] += 1
            
            if domains:
                lines.append(f"\n**{labels['distribution_by_domain']}:**\n")
                lines.append("| Domínio | Quantidade |")
                lines.append("|---|---|")
            for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"| {domain} | {count} |")
        
        # Groups
        lines.append(f"\n### 👨‍👩‍👧‍👦 {labels['groups_title']}: {stats.groups} {labels['groups_title'].lower()}")
        
        # Permissions
        if stats.permissions:
            lines.append(f"\n### 🔐 {labels['permissions_title']}: {stats.permissions} {labels['permissions_acl']}")
        
        return lines
    
    @staticmethod
    def format_compute_section(stats: ResourceStats, inventory: ResourceInventory, labels: Dict) -> List[str]:
        """Format compute resources section"""
        lines = [f"\n## 2. {labels['section_compute']}\n"]
        
        lines.append(f"### 💻 {labels['clusters_title']}: {stats.clusters} {labels['clusters_configured']}")
        
        if inventory.cluster_types:
            lines.append(f"\n**{labels['node_types_title']}:**\n")
            # Use proper markdown table instead of list
            lines.append("| Tipo de Nó | Quantidade |")
            lines.append("|---|---|")
            for node_type, count in sorted(inventory.cluster_types.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {node_type} | {count} |")
        
        if stats.instance_pools:
            lines.append(f"\n### 🏊 {labels['instance_pools_title']}: {stats.instance_pools} {labels['pools']}")
        
        return lines
    
    @staticmethod
    def format_sql_analytics_section(stats: ResourceStats, inventory: ResourceInventory, labels: Dict) -> List[str]:
        """Format SQL Analytics section"""
        lines = [f"\n## 3. SQL ANALYTICS & BUSINESS INTELLIGENCE\n"]
        
        if stats.queries:
            lines.append(f"### 🔍 Queries SQL: {stats.queries} queries")
            if inventory.queries and len(inventory.queries) > 0:
                lines.append(f"\n**Amostra de Queries ({min(10, len(inventory.queries))}/{len(inventory.queries)}):**")
                for query in sorted(inventory.queries)[:10]:
                    lines.append(f"  - {query}")
        
        if stats.dashboards:
            lines.append(f"\n### 📊 Dashboards: {stats.dashboards} dashboards")
            if inventory.dashboards and len(inventory.dashboards) > 0:
                lines.append(f"\n**Amostra de Dashboards ({min(10, len(inventory.dashboards))}/{len(inventory.dashboards)}):**")
                for dashboard in sorted(inventory.dashboards)[:10]:
                    lines.append(f"  - {dashboard}")
        
        if stats.alerts:
            lines.append(f"\n### 🔔 Alertas: {stats.alerts} alertas configurados")
            if inventory.alerts and len(inventory.alerts) > 0:
                lines.append(f"\n**Amostra de Alertas ({min(10, len(inventory.alerts))}/{len(inventory.alerts)}):**")
                for alert in sorted(inventory.alerts)[:10]:
                    lines.append(f"  - {alert}")
        
        if stats.sql_endpoints:
            lines.append(f"\n### 🏢 SQL Warehouses: {stats.sql_endpoints} endpoints")
        
        if stats.sql_global_config:
            lines.append(f"\n### ⚙️ SQL Global Config: {stats.sql_global_config} configurações globais")
        
        return lines
    
    @staticmethod
    def format_ml_section(stats: ResourceStats, inventory: ResourceInventory, labels: Dict) -> List[str]:
        """Format Machine Learning section"""
        lines = [f"\n## 4. MACHINE LEARNING & AI\n"]
        
        if stats.uc_models:
            lines.append(f"### 🤖 Registered Models: {stats.uc_models} modelos")
            if inventory.uc_models and len(inventory.uc_models) > 0:
                lines.append(f"\n**Amostra de Modelos ({min(10, len(inventory.uc_models))}/{len(inventory.uc_models)}):**")
                for model in sorted(inventory.uc_models)[:10]:
                    lines.append(f"  - {model}")
        
        if stats.model_serving_endpoints:
            lines.append(f"\n### 🚀 Model Serving: {stats.model_serving_endpoints} endpoints")
            if inventory.model_serving_endpoints:
                for endpoint in sorted(inventory.model_serving_endpoints):
                    lines.append(f"  - {endpoint}")
        
        if stats.vector_search_indexes:
            lines.append(f"\n### 🔍 Vector Search Indexes: {stats.vector_search_indexes} índices")
            if inventory.vector_search_indexes:
                for index in sorted(inventory.vector_search_indexes)[:10]:
                    lines.append(f"  - {index}")
        
        if stats.vector_search_endpoints:
            lines.append(f"\n### 📡 Vector Search Endpoints: {stats.vector_search_endpoints} endpoints")
        
        return lines
    
    @staticmethod
    def format_secrets_section(stats: ResourceStats, inventory: ResourceInventory, labels: Dict) -> List[str]:
        """Format Secrets & Security section"""
        lines = [f"\n## 5. SECRETS & SEGURANÇA\n"]
        
        if stats.secret_scopes:
            lines.append(f"### 🔐 Secret Scopes: {stats.secret_scopes} scopes")
            if inventory.secret_scopes:
                lines.append(f"\n**Scopes configurados:**")
                for scope in sorted(inventory.secret_scopes):
                    lines.append(f"  - {scope}")
        
        if stats.secrets:
            lines.append(f"\n### 🔑 Secrets: {stats.secrets} secrets (não listados por segurança)")
        
        if stats.secret_acls:
            lines.append(f"\n### 🔒 Secret ACLs: {stats.secret_acls} ACLs de secrets")
        
        if stats.cluster_policies:
            lines.append(f"\n### 📋 Cluster Policies: {stats.cluster_policies} políticas")
            if inventory.cluster_policies:
                lines.append(f"\n**Políticas configuradas:**")
                for policy in sorted(inventory.cluster_policies):
                    lines.append(f"  - {policy}")
        
        return lines
    
    @staticmethod
    def format_workspace_section(stats: ResourceStats, inventory: ResourceInventory, labels: Dict) -> List[str]:
        """Format Workspace section"""
        lines = [f"\n## 6. WORKSPACE & ARQUIVOS\n"]
        
        if stats.workspace_files:
            lines.append(f"### 📄 Workspace Files: {stats.workspace_files} arquivos")
            if inventory.workspace_file_types:
                lines.append(f"\n**Tipos de arquivo:**\n")
                lines.append("| Extensão | Quantidade |")
                lines.append("|---|---|")
                for ext, count in sorted(inventory.workspace_file_types.items(), key=lambda x: x[1], reverse=True)[:10]:
                    lines.append(f"| .{ext} | {count} |")
        
        if stats.directories:
            lines.append(f"\n### 📁 Directories: {stats.directories} diretórios")
        
        if stats.repos:
            lines.append(f"\n### 🔗 Repos: {stats.repos} repositórios")
        
        if stats.notification_destinations:
            lines.append(f"\n### 📬 Notification Destinations: {stats.notification_destinations} destinos")
        
        if stats.workspace_bindings:
            lines.append(f"\n### 🔗 Workspace Bindings: {stats.workspace_bindings} bindings (Unity Catalog)")
        
        if stats.workspace_conf:
            lines.append(f"\n### ⚙️ Workspace Configuration: {stats.workspace_conf} configurações")
        
        if stats.dbfs_files:
            lines.append(f"\n### 💾 DBFS Files: {stats.dbfs_files} arquivos no DBFS")
        
        return lines
    
    @staticmethod
    def format_unity_catalog_section(stats: ResourceStats, inventory: ResourceInventory, labels: Dict) -> List[str]:
        """Format Unity Catalog section"""
        lines = [f"\n## 7. {labels['section_unity_catalog']}\n"]
        
        if stats.uc_catalogs:
            lines.append(f"### 📚 {labels['catalogs_title']}: {stats.uc_catalogs} {labels['catalogs']}")
            if inventory.uc_catalogs:
                lines.append(f"**{labels['catalogs_configured']}:**")
                for catalog in sorted(inventory.uc_catalogs):
                    lines.append(f"  - {catalog}")
        
        if stats.uc_schemas:
            lines.append(f"\n### 📂 {labels['schemas_title']}: {stats.uc_schemas} {labels['schemas']}")
        
        if stats.uc_tables:
            lines.append(f"\n### 📊 {labels['tables_title']}: {stats.uc_tables} {labels['tables_managed']}")
        
        if stats.uc_volumes:
            lines.append(f"\n### 📦 {labels['volumes_title']}: {stats.uc_volumes} {labels['volumes']}")
        
        if stats.uc_external_locations:
            lines.append(f"\n### 📍 External Locations: {stats.uc_external_locations} localizações externas")
        
        if stats.uc_storage_credentials:
            lines.append(f"\n### 🔑 Storage Credentials: {stats.uc_storage_credentials} credenciais de armazenamento")
        
        if stats.uc_system_schemas:
            lines.append(f"\n### 🗂️ System Schemas: {stats.uc_system_schemas} schemas de sistema")
        
        if stats.uc_recipients:
            lines.append(f"\n### 🤝 Recipients (Delta Sharing): {stats.uc_recipients} recipients")
        
        if stats.uc_grants:
            lines.append(f"\n### 🔐 Grants: {stats.uc_grants} permissões Unity Catalog")
        
        return lines
    
    @staticmethod
    def format_executive_summary(stats: ResourceStats, tf_files: List[Path], labels: Dict) -> List[str]:
        """Format executive summary"""
        lines = [f"\n## {labels['section_summary']}\n"]
        
        total_resources = sum(getattr(stats, field) for field in vars(stats) if isinstance(getattr(stats, field), int))
        total_size_kb = sum(f.stat().st_size for f in tf_files) / 1024
        
        lines.append(f"📊 **{labels['total_resources']}:** {total_resources}")
        lines.append(f"📁 **{labels['config_files']}:** {len(tf_files)}")
        lines.append(f"💾 **{labels['total_size']}:** {total_size_kb:.1f} KB")
        
        lines.append(f"\n**{labels['main_categories']}:**")
        lines.append(f"  - **{labels['users_title']}:** {stats.users}")
        lines.append(f"  - **{labels['groups_title']}:** {stats.groups}")
        lines.append(f"  - **{labels['clusters_title']}:** {stats.clusters}")
        lines.append(f"  - **Jobs:** {stats.jobs}")
        lines.append(f"  - **Notebooks:** {stats.notebooks}")
        
        if stats.uc_catalogs > 0:
            lines.append(f"\n**{labels['unity_catalog_governance']}:**")
            lines.append(f"  - {labels['catalogs_title']}: {stats.uc_catalogs}")
            lines.append(f"  - {labels['schemas_title']}: {stats.uc_schemas}")
            lines.append(f"  - {labels['tables_title']}: {stats.uc_tables}")
        
        return lines


# ============================================================================
# MAIN AGENT CLASS  
# ============================================================================

class SimpleDatabricksAgent:
    """Lightweight agent using direct HTTP calls to Databricks Model Serving"""
    
    def __init__(self, language='pt-BR'):
        """Initialize with Databricks endpoint and language"""
        self.databricks_host = os.getenv("DATABRICKS_HOST")
        self.databricks_token = os.getenv("DATABRICKS_TOKEN")
        self.databricks_endpoint = os.getenv("DATABRICKS_ENDPOINT")
        
        if not self.databricks_host or not self.databricks_token:
            raise ValueError("DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env file")
        
        if not self.databricks_endpoint:
            raise ValueError("DATABRICKS_ENDPOINT must be set in .env file (e.g., /serving-endpoints/databricks-gpt-oss-120b/invocations)")
        
        # Validate endpoint format
        if not self.databricks_endpoint.startswith('/serving-endpoints/'):
            print(f"⚠️  Warning: Endpoint should start with /serving-endpoints/")
            print(f"   Current: {self.databricks_endpoint}")
            print(f"   Expected format: /serving-endpoints/<model-name>/invocations")
        
        self.api_url = f"{self.databricks_host.rstrip('/')}{self.databricks_endpoint}"
        self.model_name = self.databricks_endpoint.split('/')[-2] if '/serving-endpoints/' in self.databricks_endpoint else 'unknown'
        
        # Setup paths
        project_root = os.getenv('PROJECT_ROOT')
        base_path = Path(project_root) if project_root else Path(__file__).parent.parent.parent.parent.parent
        
        self.tf_files_dir = base_path / "databricks_tf_files"
        self.ucx_dir = base_path / "ucx_export"
        self.output_dir = base_path / "output_summary_agent"
        
        self.language = language
        self.prompts = self._load_prompts(language)
        
        print(f"[Agent] API: {self.api_url}")
        print(f"[Agent] Model: {self.model_name}")
        print(f"[Agent] Language: {self.language}")
    
    def _load_prompts(self, language: str) -> Dict:
        """Load prompts from JSON"""
        prompts_file = Path(__file__).parent / "prompts.json"
        
        print(f"[Agent] Loading prompts from: {prompts_file}")
        print(f"[Agent] File exists: {prompts_file.exists()}")
        
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                all_prompts = json.load(f)
            
            print(f"[Agent] Loaded prompts for languages: {list(all_prompts.keys())}")
            
            if language not in all_prompts:
                print(f"⚠️  Language '{language}' not found, using pt-BR")
                language = 'pt-BR'
            
            prompts = all_prompts[language]
            print(f"[Agent] Using language: {language}")
            print(f"[Agent] Prompt keys available: {list(prompts.keys())}")
            
            # Validate required keys
            required_keys = ['report_title', 'inventory_section', 'ucx_section', 'detailed_section', 'prompts']
            missing_keys = [key for key in required_keys if key not in prompts]
            if missing_keys:
                print(f"⚠️  Missing keys in prompts.json: {missing_keys}")
            
            return prompts
            
        except FileNotFoundError as e:
            print(f"❌ Error: prompts.json not found at {prompts_file}")
            print(f"   Using fallback prompts (English)")
            return self._get_fallback_prompts()
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in prompts.json: {e}")
            print(f"   Using fallback prompts (English)")
            return self._get_fallback_prompts()
        except Exception as e:
            print(f"❌ Error loading prompts: {e}")
            print(f"   Using fallback prompts (English)")
            return self._get_fallback_prompts()
    
    def _get_fallback_prompts(self) -> Dict:
        """Return fallback prompts in English"""
        return {
            'report_title': 'Databricks Assessment Report',
            'inventory_section': 'INFRASTRUCTURE INVENTORY',
            'ucx_section': 'UCX ANALYSIS',
            'detailed_section': 'DETAILED ANALYSIS',
            'prompts': {
                'summary': 'Summarize:\n{terraform_analysis}',
                'detailed': 'Detailed analysis:\n{terraform_analysis}',
                'ucx': 'UCX analysis:\n{inventory_text}'
            },
            'labels': {}
            }
    
    def _call_llm(self, system_message: str, user_message: str, max_tokens: int = 1000) -> str:
        """Call Databricks LLM via HTTP"""
        headers = {
            "Authorization": f"Bearer {self.databricks_token}",
            "Content-Type": "application/json"
        }
        
        # Limit max_tokens based on model - increased for complete reports
        if "gpt-5" in self.model_name.lower():
            max_tokens = min(max_tokens, 32000)  # GPT-5 can handle much more
        elif "gemini" in self.model_name.lower():
            max_tokens = min(max_tokens, 32000)  # Gemini 2.5 supports higher limits
        else:
            max_tokens = min(max_tokens, 8192)  # Other models increased to 8K
        
        payload = {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            "max_tokens": max_tokens
        }
        
        # Only add temperature if model supports it (databricks-gpt-5 doesn't support custom temperature)
        if "gpt-5" not in self.model_name.lower():
            payload["temperature"] = 0.7
        
        try:
            print(f"   Calling LLM: {self.model_name} (max_tokens: {max_tokens})")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"\n❌ HTTP Error {e.response.status_code}")
            print(f"   URL: {self.api_url}")
            print(f"   Model: {self.model_name}")
            try:
                error_detail = e.response.json()
                print(f"   Error: {error_detail}")
            except:
                print(f"   Response: {e.response.text[:500]}")
            raise Exception(f"LLM API Error: {e.response.status_code} - Check endpoint and model configuration")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Handle different formats
        if isinstance(content, list):
            content = '\n'.join(str(item) for item in content)
        elif isinstance(content, dict):
            content = content.get('text') or content.get('content') or str(content)
        
        return ContentCleaner.clean_json_response(str(content))
    
    def analyze_terraform(self) -> str:
        """Analyze Terraform files"""
        labels = self.prompts.get('labels', {})
        print(f"\n🔍 {labels.get('analyzing_terraform', 'Analyzing Terraform...')}")
        
        tf_files = list(self.tf_files_dir.glob("*.tf"))
        print(f"   {labels.get('found_files', 'Found {count} files').format(count=len(tf_files))}")
        
        stats = ResourceStats()
        inventory = ResourceInventory()
        
        for tf_file in tf_files:
            try:
                content = tf_file.read_text()
                lines = content.split('\n')
                
                TerraformResourceExtractor.extract_users(lines, stats, inventory)
                TerraformResourceExtractor.extract_groups(lines, stats, inventory)
                TerraformResourceExtractor.extract_clusters(lines, stats, inventory)
                TerraformResourceExtractor.extract_cluster_policies(lines, stats, inventory)
                TerraformResourceExtractor.extract_jobs(lines, stats, inventory)
                TerraformResourceExtractor.extract_notebooks(lines, stats, inventory)
                TerraformResourceExtractor.extract_sql_analytics(lines, stats, inventory)
                TerraformResourceExtractor.extract_ml_resources(lines, stats, inventory)
                TerraformResourceExtractor.extract_secrets(lines, stats, inventory)
                TerraformResourceExtractor.extract_workspace_resources(lines, stats, inventory)
                TerraformResourceExtractor.extract_uc_resources(lines, content, stats, inventory)
                TerraformResourceExtractor.extract_simple_counts(content, stats)
            except Exception as e:
                print(f"   Warning: {tf_file.name}: {e}")
        
        print(f"   ✓ {labels.get('users_title', 'Users')}: {stats.users}")
        print(f"   ✓ {labels.get('clusters_title', 'Clusters')}: {stats.clusters}")
        print(f"   ✓ Jobs: {stats.jobs}")
        
        analysis_parts = [
            f"*{labels.get('analysis_intro', 'Analysis of {count} Terraform files').format(count=len(tf_files))}*\n"
        ]
        
        analysis_parts.extend(ReportFormatter.format_identity_section(stats, inventory, labels))
        analysis_parts.extend(ReportFormatter.format_compute_section(stats, inventory, labels))
        analysis_parts.extend(ReportFormatter.format_sql_analytics_section(stats, inventory, labels))
        analysis_parts.extend(ReportFormatter.format_ml_section(stats, inventory, labels))
        analysis_parts.extend(ReportFormatter.format_secrets_section(stats, inventory, labels))
        analysis_parts.extend(ReportFormatter.format_workspace_section(stats, inventory, labels))
        analysis_parts.extend(ReportFormatter.format_unity_catalog_section(stats, inventory, labels))
        analysis_parts.extend(ReportFormatter.format_executive_summary(stats, tf_files, labels))
        
        return '\n'.join(analysis_parts)
    
    def analyze_ucx(self) -> str:
        """Analyze UCX files"""
        labels = self.prompts.get('labels', {})
        print(f"\n🔍 {labels.get('analyzing_ucx', 'Analyzing UCX...')}")
        
        if not self.ucx_dir.exists():
            return f"# 📊 {self.prompts['ucx_section']}\n\n⚠️ {labels.get('ucx_not_found', 'UCX directory not found')}"
        
        excel_files = list(self.ucx_dir.glob("*.xlsx"))
        if not excel_files:
            return f"# 📊 {self.prompts['ucx_section']}\n\n⚠️ {labels.get('no_excel_found', 'No Excel files found')}"
        
        # Build inventory summary of UCX data with STRUCTURED AGGREGATION
        inventory_parts = []
        summary_table_data = []  # For aggregated summary table
        readiness_summary = None  # For the main readiness table
        
        for excel_file in excel_files:
            inventory_parts.append(f"\n## Arquivo: {excel_file.name}")
            
            try:
                xl_file = pd.ExcelFile(excel_file)
                inventory_parts.append(f"Total de abas: {len(xl_file.sheet_names)}\n")
                
                # First, try to read the main readiness summary (05_0_object_readiness)
                readiness_sheet_names = [name for name in xl_file.sheet_names if 'object_readiness' in name.lower() or '05_0' in name]
                if readiness_sheet_names:
                    try:
                        readiness_df = pd.read_excel(excel_file, sheet_name=readiness_sheet_names[0])
                        if not readiness_df.empty:
                            inventory_parts.append(f"\n### 📊 TABELA RESUMO DE PRONTIDÃO (de {readiness_sheet_names[0]})\n")
                            inventory_parts.append("| Tipo de objeto | Total identificado | Prontos | Necessitam de ajuste |")
                            inventory_parts.append("|---|---|---|---|")
                            
                            for _, row in readiness_df.iterrows():
                                # Try to extract the columns (may vary in naming)
                                obj_type = str(row.iloc[0]) if len(row) > 0 else ''
                                total = str(row.iloc[1]) if len(row) > 1 else '0'
                                ready = str(row.iloc[2]) if len(row) > 2 else '0'
                                need_adjust = str(row.iloc[3]) if len(row) > 3 else '-'
                                
                                if obj_type and obj_type != 'nan' and not obj_type.startswith('Unnamed'):
                                    inventory_parts.append(f"| {obj_type} | {total} | {ready} | {need_adjust} |")
                            
                            inventory_parts.append("\n")
                            readiness_summary = True
                    except Exception as e:
                        print(f"   ⚠️ Erro ao ler aba de prontidão: {e}")
                
                # Collect summary of each sheet WITH ACTUAL VALUES
                for sheet_name in xl_file.sheet_names[:20]:  # Increased to 20 sheets
                    try:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name)
                        rows, cols = df.shape
                        
                        # Skip the readiness summary sheet as we already processed it above
                        if 'object_readiness' in sheet_name.lower() or '05_0' in sheet_name:
                            continue
                        
                        inventory_parts.append(f"\n### Aba: {sheet_name}")
                        inventory_parts.append(f"- Registros: {rows}")
                        
                        if not df.empty and rows > 0:
                            # Extract ACTUAL VALUES from the sheet
                            
                            # Look for readiness/compatibility scores (common in UCX)
                            for col in df.columns:
                                col_lower = str(col).lower()
                                if any(keyword in col_lower for keyword in ['readiness', 'compatibility', 'score', 'percent', '%']):
                                    values = df[col].dropna()
                                    if len(values) > 0:
                                        # Try to get numeric values
                                        try:
                                            numeric_vals = pd.to_numeric(values, errors='coerce').dropna()
                                            if len(numeric_vals) > 0:
                                                avg_val = numeric_vals.mean()
                                                max_val = numeric_vals.max()
                                                inventory_parts.append(f"- **{col}**: {avg_val:.1f}% (média), máximo: {max_val:.1f}%")
                                        except:
                                            # If not numeric, show first unique values
                                            unique_vals = values.unique()[:5]
                                            inventory_parts.append(f"- **{col}**: {', '.join(str(v) for v in unique_vals)}")
                            
                            # Show key metrics columns with actual data
                            key_cols = [col for col in df.columns if any(keyword in str(col).lower() 
                                       for keyword in ['name', 'table', 'database', 'catalog', 'object', 'type', 'status', 'ready', 'failure'])]
                            
                            if key_cols:
                                # Count by status/type if exists
                                status_cols = [col for col in key_cols if any(kw in str(col).lower() for kw in ['status', 'type', 'ready'])]
                                if status_cols:
                                    for status_col in status_cols[:2]:
                                        value_counts = df[status_col].value_counts().head(5)
                                        if len(value_counts) > 0:
                                            inventory_parts.append(f"- **{status_col} (contagem)**:")
                                            for val, count in value_counts.items():
                                                inventory_parts.append(f"  - {val}: {count}")
                                
                                # Show sample of first few rows with key columns
                                sample_cols = key_cols[:5]
                                if len(sample_cols) > 0 and rows > 0:
                                    sample_df = df[sample_cols].head(5)
                                    # Convert to readable format
                                    inventory_parts.append(f"- **Amostra de dados ({min(5, rows)} de {rows} registros)**:")
                                    for idx, row in sample_df.iterrows():
                                        row_data = ' | '.join([f"{col}: {row[col]}" for col in sample_cols if pd.notna(row[col])])
                                        if row_data:
                                            inventory_parts.append(f"  - {row_data[:200]}")
                            
                            # Show totals/aggregations for numeric columns
                            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                            if len(numeric_cols) > 0 and len(numeric_cols) <= 10:
                                inventory_parts.append(f"- **Métricas numéricas**:")
                                for num_col in numeric_cols[:5]:
                                    col_sum = df[num_col].sum()
                                    col_count = df[num_col].count()
                                    if col_sum > 0 or col_count > 0:
                                        inventory_parts.append(f"  - {num_col}: Total={col_sum:.0f}, Registros={col_count}")
                            
                                
                    except Exception as e:
                        inventory_parts.append(f"   ⚠️ Erro ao ler aba: {str(e)[:100]}")
                
                if len(xl_file.sheet_names) > 15:
                    inventory_parts.append(f"\n_... e mais {len(xl_file.sheet_names) - 15} abas_")
                    
            except Exception as e:
                inventory_parts.append(f"❌ Erro: {str(e)}")
        
        inventory_text = '\n'.join(inventory_parts)
        
        # Now call LLM with UCX prompt to generate professional analysis
        print(f"   📊 Gerando análise UCX via LLM...")
        ucx_prompt = self.prompts['prompts']['ucx'].format(inventory_text=inventory_text)
        
        ucx_analysis = self._call_llm(
            "You are a Unity Catalog migration expert. "
            "CRITICAL: Write ONLY in pure MARKDOWN format. "
            "For tables, use ONLY: | col1 | col2 | with |---|---| separator. "
            "NEVER use HTML tags. ONLY markdown. "
            "Provide a professional executive analysis in markdown.",
            ucx_prompt,
            max_tokens=15000  # Increased for complete UCX analysis
        )
        
        return f"# 📊 {self.prompts['ucx_section']}\n\n{ucx_analysis}"
    
    def generate_report(self, terraform_analysis: str, ucx_analysis: str = "") -> str:
        """Generate final report"""
        labels = self.prompts.get('labels', {})
        print(f"\n📝 {labels.get('generating_report', 'Generating report...')}")
        
        report_parts = [
            f"# {self.prompts['report_title']}\n",
            "---\n\n"
        ]
        
        # Executive Summary via LLM
        summary_context = f"{terraform_analysis}\n{ucx_analysis}"
        prompt = self.prompts['prompts']['summary'].format(terraform_analysis=summary_context)
        
        summary = self._call_llm(
            "You are a technical consultant. Write in pure MARKDOWN format. NO HTML tags allowed. Return only markdown text.",
            prompt,
            10000  # Increased for complete summary
        )
        
        report_parts.append(f"## 📊 {labels.get('section_summary', 'EXECUTIVE SUMMARY')}\n\n")
        report_parts.append(summary)
        report_parts.append("\n\n---\n\n")
        
        # Infrastructure
        report_parts.append(f"## 📦 {self.prompts['inventory_section']}\n\n")
        report_parts.append(terraform_analysis)
        report_parts.append("\n\n---\n\n")
        
        # UCX
        if ucx_analysis:
            report_parts.append(ucx_analysis)
            report_parts.append("\n\n---\n\n")
        
        # Detailed Analysis (via LLM)
        print("\n🤖 Gerando análise técnica detalhada...")
        prompt_detailed = self.prompts['prompts']['detailed'].format(terraform_analysis=terraform_analysis)
        
        detailed = self._call_llm(
            "You are a Databricks expert writing a technical report. "
            "CRITICAL: Write ONLY in pure MARKDOWN format. "
            "For tables, use ONLY this format: | col1 | col2 | with |---|---| separator. "
            "NEVER use HTML tags like <table>, <tr>, <td>, <th>. "
            "NEVER use HTML. ONLY markdown. "
            "Return pure markdown text without any HTML tags.",
            prompt_detailed,
            max_tokens=30000  # Maximum for complete detailed analysis
        )
        
        report_parts.append(f"# 🔍 {self.prompts['detailed_section']}\n\n")
        report_parts.append(detailed)
        report_parts.append("\n\n---\n\n")
        
        return ''.join(report_parts)
    
    def _generate_html(self, markdown_content: str) -> str:
        """Convert markdown to styled HTML"""
        import markdown
        
        # Convert markdown to HTML
        html_body = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
        # Wrap in HTML template with styling
        html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Databricks Assessment Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
            color: #333;
        }}
        h1 {{
            color: #FF3621;
            border-bottom: 3px solid #FF3621;
            padding-bottom: 10px;
            margin-top: 40px;
        }}
        h2 {{
            color: #1b3139;
            margin-top: 30px;
            padding-left: 10px;
            border-left: 4px solid #FF3621;
        }}
        h3 {{
            color: #2c5282;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #1b3139;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}
        tr:hover {{
            background: #f7fafc;
        }}
        code {{
            background: #2d3748;
            color: #68d391;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 8px 0;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e2e8f0;
            margin: 40px 0;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .export-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #FF3621;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(255, 54, 33, 0.3);
            transition: all 0.3s ease;
            z-index: 1000;
        }}
        .export-button:hover {{
            background: #e62e1a;
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(255, 54, 33, 0.4);
        }}
        .export-button:active {{
            transform: translateY(0);
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
            .export-button {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <button class="export-button" onclick="window.print()">📄 Export to PDF</button>
    <div class="container">
        {html_body}
    </div>
</body>
</html>"""
        
        return html_template
    
    def run(self) -> Dict[str, str]:
        """Run analysis workflow"""
        print("\n" + "="*80)
        print("🤖 Starting Analysis")
        print("="*80)
        
        try:
            terraform_analysis = self.analyze_terraform()
            ucx_analysis = self.analyze_ucx()
            final_report = self.generate_report(terraform_analysis, ucx_analysis)
            
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save Markdown
            report_file = self.output_dir / "Databricks_Assessment_Report.md"
            report_file.write_text(final_report)
            
            # Generate HTML
            html_file = self.output_dir / "Databricks_Assessment_Report.html"
            html_content = self._generate_html(final_report)
            html_file.write_text(html_content, encoding='utf-8')
            
            labels = self.prompts.get('labels', {})
            print(f"\n✅ {labels.get('report_saved', 'Report saved')}:")
            print(f"   📄 Markdown: {report_file}")
            print(f"   🌐 HTML: {html_file}")
            
            return {
                "success": True,
                "terraform_analysis": terraform_analysis,
                "ucx_analysis": ucx_analysis,
                "final_report": final_report,
                "report_file": str(report_file),
                "html_file": str(html_file)
            }
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        agent = SimpleDatabricksAgent()
        agent.run()
        print("\n✅ Complete!")
        return 0
    else:
        print("Usage: python langchain.py run")
        return 1


if __name__ == "__main__":
    exit(main())
