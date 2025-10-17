"""
PDF Generation module using WeasyPrint (HTML to PDF)
No external dependencies like pandoc required!
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint not available. PDF export will be limited.")


def html_to_pdf(html_content: str, output_path: str, title: str = "Databricks Assessment Report") -> bool:
    """
    Convert HTML content to PDF using WeasyPrint.
    
    Args:
        html_content: HTML string to convert
        output_path: Where to save the PDF
        title: Document title
    
    Returns:
        True if successful, False otherwise
    """
    if not WEASYPRINT_AVAILABLE:
        logger.error("WeasyPrint not installed. Install with: pip install weasyprint")
        return False
    
    try:
        # Custom CSS for better PDF styling
        css_string = """
        @page {
            size: A4;
            margin: 2cm;
            @top-center {
                content: "Databricks Assessment Report";
                font-size: 10pt;
                color: #666;
            }
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }
        
        h1 {
            color: #FF3621;
            border-bottom: 3px solid #FF3621;
            padding-bottom: 10px;
            margin-top: 30px;
            font-size: 24pt;
        }
        
        h2 {
            color: #FF8A00;
            margin-top: 25px;
            font-size: 18pt;
            border-left: 4px solid #FF8A00;
            padding-left: 10px;
        }
        
        h3 {
            color: #1B3139;
            margin-top: 20px;
            font-size: 14pt;
        }
        
        .metric-card {
            background: #f8f9fa;
            border-left: 4px solid #FF3621;
            padding: 15px;
            margin: 15px 0;
            page-break-inside: avoid;
        }
        
        .critical {
            background: #fff5f5;
            border-color: #dc3545;
        }
        
        .warning {
            background: #fffbf0;
            border-color: #ffc107;
        }
        
        .success {
            background: #f0fff4;
            border-color: #28a745;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            page-break-inside: avoid;
        }
        
        th {
            background: #1B3139;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        
        tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 10pt;
        }
        
        pre {
            background: #1B3139;
            color: #fff;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            page-break-inside: avoid;
        }
        
        .summary-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            page-break-inside: avoid;
        }
        
        .recommendation {
            background: #e7f3ff;
            border-left: 4px solid #0066cc;
            padding: 15px;
            margin: 15px 0;
            page-break-inside: avoid;
        }
        """
        
        # Wrap HTML content with proper structure
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Generate PDF
        html_doc = HTML(string=full_html)
        css = CSS(string=css_string)
        
        html_doc.write_pdf(output_path, stylesheets=[css])
        
        logger.info(f"✅ PDF generated successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.exception(f"Error generating PDF: {e}")
        return False


def markdown_to_html(markdown_content: str) -> str:
    """
    Convert Markdown to HTML for display with proper formatting.
    Handles tables, code blocks, and basic markdown syntax.
    
    Args:
        markdown_content: Markdown string
    
    Returns:
        Styled HTML string
    """
    try:
        import markdown
        
        # Convert markdown to HTML with extensions
        html = markdown.markdown(
            markdown_content,
            extensions=[
                'tables',
                'fenced_code',
                'nl2br',
                'sane_lists'
            ]
        )
        
        # Add CSS for better styling
        styled_html = f"""
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: #FF3621;
                border-bottom: 3px solid #FF3621;
                padding-bottom: 10px;
                margin-top: 30px;
            }}
            h2 {{
                color: #FF8A00;
                border-left: 4px solid #FF8A00;
                padding-left: 10px;
                margin-top: 25px;
            }}
            h3 {{
                color: #1B3139;
                margin-top: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th {{
                background: #1B3139;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }}
            td {{
                padding: 10px 12px;
                border-bottom: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background: #f8f9fa;
            }}
            tr:hover {{
                background: #e9ecef;
            }}
            code {{
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }}
            pre {{
                background: #1B3139;
                color: #fff;
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
            blockquote {{
                border-left: 4px solid #FF8A00;
                margin: 20px 0;
                padding: 10px 20px;
                background: #fff8f0;
            }}
            strong {{
                color: #1B3139;
                font-weight: 600;
            }}
            p {{
                margin: 12px 0;
            }}
        </style>
        {html}
        """
        
        return styled_html
        
    except ImportError:
        logger.warning("markdown library not available, using basic conversion")
        # Fallback: basic conversion with minimal styling
        html = markdown_content
        html = html.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html = html.replace('\n\n', '</p><p>')
        html = html.replace('\n', '<br>')
        html = f'<div style="font-family: sans-serif; padding: 20px;"><p>{html}</p></div>'
        return html

