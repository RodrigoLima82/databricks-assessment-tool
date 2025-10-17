"""
UCX Assessment Analyzer Tool

Reads and analyzes UCX (Unity Catalog Migration) assessment files
from Excel or CSV format.
"""

from crewai_tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import pandas as pd
import os
from pathlib import Path


class UCXAnalyzerToolInput(BaseModel):
    """Input schema for UCX Analyzer Tool."""
    ucx_directory: str = Field(
        ...,
        description="Path to directory containing UCX assessment files (.xlsx or .csv)"
    )


class UCXAnalyzerTool(BaseTool):
    name: str = "UCX Assessment Analyzer"
    description: str = (
        "Analyzes Unity Catalog Migration (UCX) assessment files. "
        "Reads Excel or CSV files containing UCX assessment data and extracts "
        "key metrics, issues, and migration readiness information."
    )
    args_schema: Type[BaseModel] = UCXAnalyzerToolInput

    def _run(self, ucx_directory: str) -> str:
        """
        Execute the UCX assessment analysis.
        
        Args:
            ucx_directory: Path to directory with UCX files
            
        Returns:
            Formatted summary of UCX assessment findings
        """
        try:
            ucx_path = Path(ucx_directory)
            
            if not ucx_path.exists():
                return f"❌ UCX directory not found: {ucx_directory}"
            
            # Find all Excel and CSV files
            excel_files = list(ucx_path.glob("*.xlsx")) + list(ucx_path.glob("*.xls"))
            csv_files = list(ucx_path.glob("*.csv"))
            
            if not excel_files and not csv_files:
                return f"⚠️ No UCX assessment files (.xlsx, .csv) found in: {ucx_directory}"
            
            all_files = excel_files + csv_files
            summary_parts = []
            
            summary_parts.append("=" * 100)
            summary_parts.append("UCX (UNITY CATALOG MIGRATION) DETAILED ASSESSMENT ANALYSIS")
            summary_parts.append("=" * 100)
            summary_parts.append("")
            summary_parts.append(f"📁 Assessment Files Found: {len(all_files)}")
            summary_parts.append("")
            
            # Process each file
            for idx, file_path in enumerate(all_files, 1):
                client_name = file_path.stem.replace("_ucx_assessment", "").replace("_", " ").title()
                
                summary_parts.append(f"\n{'=' * 100}")
                summary_parts.append(f"CLIENT {idx}: {client_name}")
                summary_parts.append(f"File: {file_path.name}")
                summary_parts.append(f"{'=' * 100}")
                summary_parts.append("")
                
                try:
                    # Read the file
                    if file_path.suffix in ['.xlsx', '.xls']:
                        # Read all sheets
                        xl = pd.ExcelFile(file_path)
                        summary_parts.append(f"📊 Total Sheets: {len(xl.sheet_names)}")
                        summary_parts.append("")
                        
                        # Process structured UCX sheets
                        self._process_ucx_structured_file(file_path, summary_parts)
                    
                    elif file_path.suffix == '.csv':
                        df = pd.read_csv(file_path)
                        summary_parts.append(f"📊 CSV Data:")
                        summary_parts.append(f"  Rows: {len(df)}")
                        summary_parts.append(f"  Columns: {len(df.columns)}")
                        summary_parts.append(f"  Fields: {', '.join(df.columns.tolist())}")
                        summary_parts.append("")
                        self._analyze_dataframe_details(df, "main", summary_parts)
                    
                except Exception as e:
                    summary_parts.append(f"  ⚠️ Error reading file: {str(e)}")
                    import traceback
                    summary_parts.append(f"  {traceback.format_exc()}")
                
                summary_parts.append("")
            
            summary_parts.append("=" * 100)
            summary_parts.append("END OF UCX ASSESSMENT ANALYSIS")
            summary_parts.append("=" * 100)
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            import traceback
            return f"❌ Error analyzing UCX assessments: {str(e)}\n{traceback.format_exc()}"
    
    def _process_ucx_structured_file(self, file_path: Path, summary_parts: list):
        """Process a structured UCX assessment Excel file with known sheet patterns."""
        
        # Sheets to IGNORE (usually too large or not relevant)
        ignored_sheets = [
            "40_3_logs",  # 63 rows - logs are repetitive and not critical (~2.5k tokens)
            "00_1_count_table_failures",  # Usually empty or minimal
        ]
        
        # Define sheet groups and their purpose
        sheet_groups = {
            "Summary Metrics": [
                "00_2_count_total_databases",
                "00_3_count_total_tables", 
                "00_4_count_total_views",
                "01_1_count_jobs",
                "01_0_compatibility"
            ],
            "Inventory": [
                "10_0_database_summary",
                "10_1_all_tables",
                "30_3_jobs"
            ],
            "Issues & Blockers": [
                "35_2_code_compatibility_problem",
                "36_1_direct_filesystem_accesses",
                "15_3_mount_points"
                # 40_3_logs removed - too large
            ],
            "Readiness": [
                "05_0_object_readiness",
                "05_2_assessment_summary"
            ],
            "Usage": [
                "37_1_used_tables",  # Important - shows table usage patterns
                "38_1_dashboards"
            ]
        }
        
        # Add note about ignored sheets
        if ignored_sheets:
            summary_parts.append(f"ℹ️  Ignored sheets (too large/not relevant): {', '.join(ignored_sheets)}")
            summary_parts.append("")
        
        # Process each group
        for group_name, sheet_names in sheet_groups.items():
            summary_parts.append(f"\n{'─' * 100}")
            summary_parts.append(f"📊 {group_name.upper()}")
            summary_parts.append(f"{'─' * 100}")
            summary_parts.append("")
            
            for sheet_name in sheet_names:
                # Skip ignored sheets
                if sheet_name in ignored_sheets:
                    summary_parts.append(f"⏭️  Skipping {sheet_name} (ignored)")
                    continue
                
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    self._analyze_dataframe_details(df, sheet_name, summary_parts)
                except ValueError:
                    # Sheet doesn't exist in this file
                    continue
                except Exception as e:
                    summary_parts.append(f"⚠️ Error reading sheet '{sheet_name}': {str(e)}")
            
            summary_parts.append("")
    
    def _analyze_dataframe_details(self, df: pd.DataFrame, sheet_name: str, summary_parts: list):
        """Detailed analysis of a DataFrame with real data extraction."""
        
        summary_parts.append(f"\n📄 {sheet_name}")
        summary_parts.append(f"   Total Rows: {len(df)}")
        summary_parts.append(f"   Columns: {', '.join(df.columns.tolist())}")
        
        if len(df) == 0:
            summary_parts.append("   ⚠️ No data in this sheet")
            return
        
        # For single-row summary sheets (counts, metrics)
        if len(df) == 1:
            summary_parts.append(f"\n   📊 Metrics:")
            for col in df.columns:
                value = df[col].iloc[0]
                summary_parts.append(f"      • {col}: {value}")
        
        # For multi-row data sheets
        elif len(df) > 1:
            # Show value counts for categorical columns
            categorical_cols = []
            for col in df.columns:
                if df[col].dtype == 'object' or df[col].nunique() < 20:
                    categorical_cols.append(col)
            
            if categorical_cols:
                summary_parts.append(f"\n   📊 Value Distributions:")
                for col in categorical_cols[:3]:  # First 3 categorical columns
                    value_counts = df[col].value_counts()
                    summary_parts.append(f"\n      {col}:")
                    for value, count in list(value_counts.items())[:5]:  # Top 5 values
                        percentage = (count / len(df)) * 100
                        summary_parts.append(f"         • {value}: {count} ({percentage:.1f}%)")
            
            # Show sample rows (reduced to 2 for token efficiency)
            summary_parts.append(f"\n   📋 Sample Data (first 2 rows):")
            for i, row in df.head(2).iterrows():
                summary_parts.append(f"\n      Row {i + 1}:")
                for col in df.columns[:6]:  # First 6 columns
                    value = str(row[col])[:50]  # Truncate long values
                    summary_parts.append(f"         {col}: {value}")
            
            # Identify blockers and issues (reduced for token efficiency)
            blocker_keywords = ['error', 'issue', 'problem', 'blocker', 'failure', 'warning']
            for col in df.columns:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in blocker_keywords):
                    summary_parts.append(f"\n   ⚠️ ISSUES FOUND in column '{col}':")
                    issues_shown = 0
                    for i, row in df.iterrows():
                        if pd.notna(row[col]) and str(row[col]).strip():
                            summary_parts.append(f"      • {str(row[col])[:80]}")  # Truncate issues
                            issues_shown += 1
                            if issues_shown >= 10:  # Limit to first 10 issues
                                remaining = len(df) - issues_shown
                                if remaining > 0:
                                    summary_parts.append(f"      ... and {remaining} more")
                                break
        
        summary_parts.append("")

