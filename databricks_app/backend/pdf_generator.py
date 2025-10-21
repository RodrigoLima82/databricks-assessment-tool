"""
PDF Generation module - CROSS-PLATFORM
Tries multiple libraries in order of preference:
1. WeasyPrint (best quality, macOS/Linux with GTK)
2. xhtml2pdf (good quality, pure Python, Windows-friendly)
3. reportlab (fallback, always works, limited HTML)
"""

import os
import platform
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Try to import PDF libraries (in order of preference)
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
    logger.info("✅ WeasyPrint available (best quality)")
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.debug("WeasyPrint not available (OK on Windows)")

try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
    logger.info("✅ xhtml2pdf available (Windows-friendly)")
except ImportError:
    XHTML2PDF_AVAILABLE = False
    logger.debug("xhtml2pdf not available")

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_AVAILABLE = True
    logger.info("✅ reportlab available (fallback)")
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.debug("reportlab not available")


def html_to_pdf_weasyprint(html_content: str, output_path: str, title: str) -> bool:
    """WeasyPrint PDF generation (best quality, requires GTK)"""
    if not WEASYPRINT_AVAILABLE:
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
        
        logger.info(f"✅ PDF generated successfully (WeasyPrint): {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"WeasyPrint error: {e}")
        return False


def html_to_pdf_xhtml2pdf(html_content: str, output_path: str, title: str) -> bool:
    """xhtml2pdf PDF generation (Windows-friendly, pure Python)"""
    if not XHTML2PDF_AVAILABLE:
        return False
    
    try:
        # CSS simplificado para xhtml2pdf (suporte CSS mais limitado)
        css_string = """
        <style>
            @page { size: A4; margin: 2cm; }
            body { font-family: Arial, sans-serif; font-size: 11pt; color: #333; }
            h1 { color: #FF3621; border-bottom: 3px solid #FF3621; padding-bottom: 10px; }
            h2 { color: #FF8A00; border-left: 4px solid #FF8A00; padding-left: 10px; }
            h3 { color: #1B3139; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th { background-color: #1B3139; color: white; padding: 12px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #ddd; }
            tr:nth-child(even) { background-color: #f8f9fa; }
            code { background-color: #f4f4f4; padding: 2px 6px; font-family: monospace; }
            pre { background-color: #1B3139; color: #fff; padding: 15px; }
        </style>
        """
        
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            {css_string}
        </head>
        <body>
            <h1 style="text-align: center;">{title}</h1>
            <hr/>
            {html_content}
        </body>
        </html>
        """
        
        with open(output_path, "wb") as output_file:
            pisa_status = pisa.CreatePDF(
                full_html.encode('utf-8'),
                dest=output_file,
                encoding='utf-8'
            )
        
        if pisa_status.err:
            logger.error(f"xhtml2pdf errors: {pisa_status.err}")
            return False
        
        logger.info(f"✅ PDF generated successfully (xhtml2pdf): {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"xhtml2pdf error: {e}")
        return False


def html_to_pdf_reportlab(html_content: str, output_path: str, title: str) -> bool:
    """reportlab PDF generation (fallback, limited HTML support)"""
    if not REPORTLAB_AVAILABLE:
        return False
    
    try:
        import re
        
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#FF3621'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Simple HTML to text conversion
        text = html_content
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n\n## \1 ##\n\n', text, flags=re.DOTALL)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n\n# \1 #\n\n', text, flags=re.DOTALL)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n\n> \1\n\n', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        
        # Add paragraphs
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('## ') and line.endswith(' ##'):
                h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#FF8A00'))
                story.append(Paragraph(line[3:-3], h1_style))
                story.append(Spacer(1, 0.2 * inch))
            elif line.startswith('# ') and line.endswith(' #'):
                h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1B3139'))
                story.append(Paragraph(line[2:-2], h2_style))
                story.append(Spacer(1, 0.15 * inch))
            elif line.startswith('> '):
                h3_style = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=12)
                story.append(Paragraph(line[2:], h3_style))
                story.append(Spacer(1, 0.1 * inch))
            else:
                story.append(Paragraph(line, styles['BodyText']))
                story.append(Spacer(1, 0.1 * inch))
        
        doc.build(story)
        
        logger.info(f"✅ PDF generated successfully (reportlab): {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"reportlab error: {e}")
        return False


def html_to_pdf(html_content: str, output_path: str, title: str = "Databricks Assessment Report") -> bool:
    """
    Convert HTML to PDF using best available method.
    Tries in order: WeasyPrint → xhtml2pdf → reportlab
    
    Args:
        html_content: HTML string to convert
        output_path: Where to save the PDF
        title: Document title
    
    Returns:
        True if successful, False otherwise
    """
    # Try WeasyPrint first (best quality)
    if WEASYPRINT_AVAILABLE:
        logger.info("Attempting PDF generation with WeasyPrint...")
        if html_to_pdf_weasyprint(html_content, output_path, title):
            return True
        logger.warning("WeasyPrint failed, trying alternatives...")
    
    # Try xhtml2pdf (Windows-friendly)
    if XHTML2PDF_AVAILABLE:
        logger.info("Attempting PDF generation with xhtml2pdf...")
        if html_to_pdf_xhtml2pdf(html_content, output_path, title):
            return True
        logger.warning("xhtml2pdf failed, trying alternatives...")
    
    # Try reportlab (fallback)
    if REPORTLAB_AVAILABLE:
        logger.info("Attempting PDF generation with reportlab...")
        if html_to_pdf_reportlab(html_content, output_path, title):
            return True
        logger.error("reportlab failed")
    
    # No library available or all failed
    logger.error("❌ PDF generation failed: No working library available")
    logger.error("Install one of: pip install weasyprint xhtml2pdf reportlab")
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

