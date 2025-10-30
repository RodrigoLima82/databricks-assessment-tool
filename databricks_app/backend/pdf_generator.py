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
except (ImportError, OSError) as e:
    WEASYPRINT_AVAILABLE = False
    if "libgobject" in str(e) or "GTK" in str(e):
        logger.info("⚠️  WeasyPrint GTK libraries not found (using alternatives for Windows)")
    else:
        logger.debug(f"WeasyPrint not available: {e}")

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
        import re
        from io import BytesIO
        
        # Clean HTML content - remove problematic elements for xhtml2pdf
        # Remove style tags from content (we'll add our own)
        clean_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Simplified CSS for xhtml2pdf compatibility
        css_string = """
        <style type="text/css">
            @page {
                size: a4 portrait;
                margin: 2cm;
            }
            body {
                font-family: Arial, Helvetica, sans-serif;
                font-size: 11pt;
                color: #333333;
                line-height: 1.6;
            }
            h1 {
                color: #FF3621;
                font-size: 24pt;
                margin-top: 20pt;
                margin-bottom: 10pt;
                page-break-after: avoid;
            }
            h2 {
                color: #FF8A00;
                font-size: 18pt;
                margin-top: 15pt;
                margin-bottom: 8pt;
                page-break-after: avoid;
            }
            h3 {
                color: #1B3139;
                font-size: 14pt;
                margin-top: 12pt;
                margin-bottom: 6pt;
            }
            p {
                margin-bottom: 10pt;
            }
            ul, ol {
                margin-left: 20pt;
                margin-bottom: 10pt;
            }
            li {
                margin-bottom: 5pt;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15pt 0;
            }
            th {
                background-color: #1B3139;
                color: white;
                padding: 8pt;
                text-align: left;
                font-weight: bold;
            }
            td {
                padding: 6pt;
                border-bottom: 1pt solid #dddddd;
            }
            code {
                background-color: #f4f4f4;
                padding: 2pt 4pt;
                font-family: Courier, monospace;
                font-size: 10pt;
            }
            pre {
                background-color: #2d2d2d;
                color: #f8f8f8;
                padding: 10pt;
                font-family: Courier, monospace;
                font-size: 9pt;
                overflow-x: auto;
            }
        </style>
        """
        
        # Build complete HTML document
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
    <title>{title}</title>
    {css_string}
</head>
<body>
    <h1>{title}</h1>
    {clean_content}
</body>
</html>"""
        
        # Create PDF
        with open(output_path, "wb") as output_file:
            source = BytesIO(full_html.encode('utf-8'))
            
            pisa_status = pisa.CreatePDF(
                source,
                dest=output_file,
                encoding='utf-8'
            )
        
        # Check for errors
        if pisa_status.err:
            logger.error(f"❌ xhtml2pdf reported {pisa_status.err} error(s)")
            return False
        
        # Verify file was created and has content
        if not Path(output_path).exists():
            logger.error(f"❌ xhtml2pdf did not create file: {output_path}")
            return False
        
        file_size = Path(output_path).stat().st_size
        if file_size < 100:
            logger.error(f"❌ PDF file is too small ({file_size} bytes), probably invalid")
            return False
        
        logger.info(f"✅ PDF generated successfully with xhtml2pdf")
        logger.info(f"   File: {output_path}")
        logger.info(f"   Size: {file_size:,} bytes")
        return True
        
    except Exception as e:
        logger.error(f"❌ xhtml2pdf error: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return False


def html_to_pdf_reportlab(html_content: str, output_path: str, title: str) -> bool:
    """reportlab PDF generation with HTML formatting support (bold, italic, tables)"""
    if not REPORTLAB_AVAILABLE:
        return False
    
    try:
        import re
        from html.parser import HTMLParser
        from reportlab.platypus import Table, TableStyle
        
        logger.info("📝 Using reportlab with formatting support (bold, italic, code, tables)")
        
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
        
        # Strip ALL style tags and their contents
        text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        # Strip script tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Extract and process tables separately BEFORE removing HTML tags
        table_pattern = r'<table[^>]*>(.*?)</table>'
        tables = []
        
        def extract_table(match):
            table_html = match.group(1)
            table_data = []
            
            # Extract rows
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_html, flags=re.DOTALL | re.IGNORECASE)
            for row in rows:
                # Extract cells (th or td)
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, flags=re.DOTALL | re.IGNORECASE)
                row_data = []
                for cell in cells:
                    # Clean cell content
                    cell_text = re.sub(r'<[^>]+>', '', cell).strip()
                    row_data.append(cell_text if cell_text else ' ')
                if row_data:
                    table_data.append(row_data)
            
            tables.append(table_data)
            return f'\n##TABLE{len(tables)-1}##\n'
        
        # Replace tables with markers
        text = re.sub(table_pattern, extract_table, text, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert HTML headings to markers
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n\n##H1## \1 ##H1##\n\n', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n\n##H2## \1 ##H2##\n\n', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n\n##H3## \1 ##H3##\n\n', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Preserve formatting tags that reportlab Paragraph supports
        # Convert <strong> to <b> (reportlab prefers <b>)
        text = re.sub(r'<strong>', r'<b>', text, flags=re.IGNORECASE)
        text = re.sub(r'</strong>', r'</b>', text, flags=re.IGNORECASE)
        
        # Convert <em> to <i> (reportlab prefers <i>)
        text = re.sub(r'<em>', r'<i>', text, flags=re.IGNORECASE)
        text = re.sub(r'</em>', r'</i>', text, flags=re.IGNORECASE)
        
        # Preserve <code> tags (we'll style them later)
        text = re.sub(r'<code>', r'##CODE##', text, flags=re.IGNORECASE)
        text = re.sub(r'</code>', r'##/CODE##', text, flags=re.IGNORECASE)
        
        # Convert lists
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'• \1\n', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</?[uo]l[^>]*>', '', text, flags=re.IGNORECASE)
        
        # Convert paragraphs
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert line breaks
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        
        # Remove all remaining HTML tags EXCEPT <b>, <i>, <u> which reportlab supports
        text = re.sub(r'<(?!/?[biu]>)[^>]+>', '', text)
        
        # Convert ##CODE## markers to styled code format
        # reportlab Paragraph supports <font> tag for inline styling
        text = re.sub(
            r'##CODE##(.*?)##/CODE##',
            r'<font face="Courier" size="9" backColor="#f4f4f4">\1</font>',
            text
        )
        
        # HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # Process lines
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check for table markers
            table_match = re.match(r'##TABLE(\d+)##', line)
            if table_match:
                table_idx = int(table_match.group(1))
                if 0 <= table_idx < len(tables):
                    table_data = tables[table_idx]
                    if table_data:
                        try:
                            # Create reportlab Table
                            t = Table(table_data)
                            
                            # Style the table
                            t.setStyle(TableStyle([
                                # Header row (first row)
                                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B3139')),
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 10),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('TOPPADDING', (0, 0), (-1, 0), 12),
                                
                                # Data rows
                                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                                ('FONTSIZE', (0, 1), (-1, -1), 9),
                                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                                ('TOPPADDING', (0, 1), (-1, -1), 8),
                                
                                # Grid
                                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#1B3139')),
                                
                                # Alternating row colors
                                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f4f4')]),
                            ]))
                            
                            story.append(Spacer(1, 0.1 * inch))
                            story.append(t)
                            story.append(Spacer(1, 0.2 * inch))
                        except Exception as e:
                            logger.warning(f"Failed to create table {table_idx}: {e}")
                continue
            
            # Check for heading markers
            if line.startswith('##H1##') and '##H1##' in line[6:]:
                content = line.replace('##H1##', '').strip()
                if content:
                    h1_style = ParagraphStyle('H1', parent=styles['Heading1'],
                                            fontSize=18, textColor=colors.HexColor('#FF8A00'),
                                            spaceAfter=12, spaceBefore=12)
                    story.append(Paragraph(content, h1_style))
            elif line.startswith('##H2##') and '##H2##' in line[6:]:
                content = line.replace('##H2##', '').strip()
                if content:
                    h2_style = ParagraphStyle('H2', parent=styles['Heading2'],
                                            fontSize=14, textColor=colors.HexColor('#1B3139'),
                                            spaceAfter=10, spaceBefore=10)
                    story.append(Paragraph(content, h2_style))
            elif line.startswith('##H3##') and '##H3##' in line[6:]:
                content = line.replace('##H3##', '').strip()
                if content:
                    h3_style = ParagraphStyle('H3', parent=styles['Heading3'],
                                            fontSize=12, spaceAfter=8, spaceBefore=8)
                    story.append(Paragraph(content, h3_style))
            else:
                # Regular paragraph
                if len(line) > 1:  # Skip very short lines
                    try:
                        story.append(Paragraph(line, styles['BodyText']))
                        story.append(Spacer(1, 0.05 * inch))
                    except:
                        # If paragraph fails, just skip it
                        pass
        
        # Build PDF
        try:
            doc.build(story)
        except Exception as build_error:
            logger.error(f"❌ reportlab build error: {build_error}")
            return False
        
        # Verify file was created
        if not Path(output_path).exists():
            logger.error(f"❌ reportlab did not create file: {output_path}")
            return False
        
        # Check file size
        file_size = Path(output_path).stat().st_size
        if file_size < 100:
            logger.error(f"❌ PDF file is too small ({file_size} bytes), probably invalid")
            return False
        
        logger.info(f"✅ PDF generated successfully with reportlab")
        logger.info(f"   File: {output_path}")
        logger.info(f"   Size: {file_size:,} bytes")
        
        # Try to validate PDF header
        try:
            with open(output_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    logger.warning(f"⚠️  PDF header invalid: {header}")
                else:
                    logger.info(f"   Header: Valid PDF")
        except:
            pass
        
        return True
        
    except Exception as e:
        logger.error(f"❌ reportlab error: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
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

