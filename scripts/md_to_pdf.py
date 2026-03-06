#!/usr/bin/env python3
"""
Convert planning markdown files to a single PDF.
Requires: pip install markdown weasyprint
"""

import os
import sys
from pathlib import Path

def combine_markdown_files():
    """Combine all planning markdown files into one."""
    planning_dir = Path(__file__).parent.parent / "planning"
    
    files_order = [
        "index.md",
        "01-architecture-overview.md",
        "02-tech-stack.md",
        "03-aws-infrastructure.md",
        "04-ai-ml-pipeline.md",
        "05-backend-structure.md",
        "06-frontend-structure.md",
        "07-database-schema.md",
        "08-security-compliance.md",
        "09-development-roadmap.md",
        "10-deployment-strategy.md"
    ]
    
    combined_content = f"""# Oracy AI - Planning Documentation

**Generated:** {__import__('datetime').datetime.now().isoformat()}

---

"""
    
    for filename in files_order:
        filepath = planning_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                combined_content += content
                combined_content += "\n\n---\n\n"
                print(f"✓ Added: {filename}")
        else:
            print(f"✗ Skipped (not found): {filename}")
    
    return combined_content

def convert_to_pdf():
    """Convert combined markdown to PDF."""
    try:
        import markdown
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except ImportError:
        print("Installing required packages...")
        os.system(f"{sys.executable} -m pip install markdown weasyprint")
        import markdown
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    
    print("\nCombining markdown files...")
    md_content = combine_markdown_files()
    
    # Convert markdown to HTML
    print("Converting markdown to HTML...")
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'toc', 'nl2br']
    )
    
    # Wrap in proper HTML structure with styling
    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Oracy AI - Planning Documentation</title>
    <style>
        @page {{
            size: A4;
            margin: 2cm;
            @bottom-center {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            page-break-before: always;
        }}
        h1:first-of-type {{
            page-break-before: avoid;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
            margin-top: 25px;
        }}
        h3 {{
            color: #555;
            margin-top: 20px;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
        }}
        pre code {{
            background: none;
            padding: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 10pt;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 15px 0;
            padding: 10px 20px;
            background-color: #f8f9fa;
            color: #555;
        }}
        ul, ol {{
            padding-left: 25px;
        }}
        li {{
            margin: 5px 0;
        }}
        hr {{
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
    
    # Save HTML temporarily
    output_dir = Path(__file__).parent.parent
    html_path = output_dir / "temp-planning.html"
    pdf_path = output_dir / "Oracy-AI-Planning-Documentation.pdf"
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print("Converting HTML to PDF...")
    font_config = FontConfiguration()
    HTML(string=full_html).write_pdf(
        str(pdf_path),
        font_config=font_config
    )
    
    # Clean up temp file
    html_path.unlink()
    
    file_size = pdf_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ PDF created successfully!")
    print(f"📄 Location: {pdf_path}")
    print(f"📊 File size: {file_size:.2f} MB")

if __name__ == "__main__":
    try:
        convert_to_pdf()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
