#!/usr/bin/env python3
"""
Combine all planning markdown files into a single HTML file for PDF printing.
"""

import os
from pathlib import Path
from datetime import datetime

def read_file_with_fallback(filepath):
    """Read file with encoding fallback."""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {filepath}")

def simple_markdown_to_html(text):
    """Simple markdown to HTML conversion."""
    import re
    
    # Escape HTML
    text = text.replace('&', '&').replace('<', '<').replace('>', '>')
    
    # Code blocks
    text = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', text, flags=re.DOTALL)
    
    # Inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # Headers
    text = re.sub(r'^###### (.+)$', r'<h6>\1</h6>', text, flags=re.MULTILINE)
    text = re.sub(r'^##### (.+)$', r'<h5>\1</h5>', text, flags=re.MULTILINE)
    text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Bold and Italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'___(.+?)___', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    
    # Horizontal rule
    text = re.sub(r'^---+$', r'<hr>', text, flags=re.MULTILINE)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    
    # Unordered lists
    lines = text.split('\n')
    result = []
    in_list = False
    
    for line in lines:
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            content = line.strip()[2:]
            result.append(f'<li>{content}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    
    if in_list:
        result.append('</ul>')
    
    text = '\n'.join(result)
    
    # Paragraphs (simple)
    paragraphs = text.split('\n\n')
    new_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<') and not p.startswith('---'):
            new_paragraphs.append(f'<p>{p}</p>')
        else:
            new_paragraphs.append(p)
    text = '\n\n'.join(new_paragraphs)
    
    # Line breaks
    text = text.replace('\n', '<br>\n')
    
    return text

def combine_files():
    """Combine all planning markdown files."""
    planning_dir = Path(__file__).parent.parent / "planning"
    output_file = Path(__file__).parent.parent / "Oracy-AI-Planning-Documentation.html"
    
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
    
    combined_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            max-width: 210mm;
            margin: 0 auto;
            padding: 20px;
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 0;
            page-break-before: always;
        }}
        
        h1:first-of-type {{
            page-break-before: avoid;
            margin-top: 0;
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
        
        h4, h5, h6 {{
            color: #666;
            margin-top: 15px;
        }}
        
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", "Courier New", monospace;
            font-size: 0.9em;
        }}
        
        pre {{
            background-color: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
            margin: 15px 0;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            display: block;
            white-space: pre;
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
        
        ul, ol {{
            padding-left: 25px;
            margin: 10px 0;
        }}
        
        li {{
            margin: 5px 0;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }}
        
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .title-page {{
            text-align: center;
            padding-top: 200px;
            page-break-after: always;
        }}
        
        .title-page h1 {{
            border: none;
            font-size: 32pt;
            margin-bottom: 50px;
        }}
        
        .title-page .meta {{
            color: #666;
            font-size: 14pt;
        }}
        
        @media print {{
            body {{
                padding: 0;
            }}
            
            h1 {{
                page-break-before: always;
            }}
            
            h1:first-of-type {{
                page-break-before: avoid;
            }}
            
            pre {{
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        }}
    </style>
</head>
<body>
    <div class="title-page">
        <h1>Oracy AI<br>Planning Documentation</h1>
        <div class="meta">
            <p><strong>Complete Technical Specification</strong></p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>MVP Implementation Plan</p>
        </div>
    </div>
"""
    
    for filename in files_order:
        filepath = planning_dir / filename
        if filepath.exists():
            try:
                content = read_file_with_fallback(filepath)
                html_content = simple_markdown_to_html(content)
                combined_html += f'\n<div class="section">\n{html_content}\n</div>\n'
                print(f"[OK] Added: {filename}")
            except Exception as e:
                print(f"[ERR] Error reading {filename}: {e}")
        else:
            print(f"[MISSING] Not found: {filename}")
    
    combined_html += """
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_html)
    
    file_size = output_file.stat().st_size / 1024
    print(f"\n[SUCCESS] HTML file created successfully!")
    print(f"Location: {output_file}")
    print(f"File size: {file_size:.2f} KB")
    print(f"\nTo create PDF:")
    print(f"   1. Open the HTML file in Chrome/Edge")
    print(f"   2. Press Ctrl+P (or Cmd+P on Mac)")
    print(f"   3. Select 'Save as PDF'")
    print(f"   4. Choose A4 paper size")
    print(f"   5. Save the PDF")

if __name__ == "__main__":
    combine_files()
