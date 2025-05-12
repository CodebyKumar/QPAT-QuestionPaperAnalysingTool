#!/usr/bin/env python3
"""
Markdown to PDF Converter

This script converts a specified Markdown file to PDF using the markdown and
weasyprint libraries. Input and output file paths are defined directly in the script.
"""

import markdown
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from fpdf import FPDF
import os
import re
import streamlit as st


def clean_text(text):
    """Clean text to avoid encoding issues"""
    # Replace problematic Unicode characters with ASCII equivalents
    replacements = {
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '—': '-',
        '–': '-',
        '…': '...',
        '•': '*',
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text

def markdown_to_pdf(INPUT_FILE, OUTPUT_FILE):
    """
    Convert the specified Markdown file to PDF
    Returns the path to the generated PDF file
    """
    # Get absolute paths to ensure consistency
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we should use the default paths or use the ones from variables
    input_path = os.path.join(current_dir, INPUT_FILE)
    output_path = os.path.join(current_dir, OUTPUT_FILE)
    
    # If the INPUT_FILE contains a directory separator, don't add the current_dir
    if os.path.sep in INPUT_FILE:
        input_path = INPUT_FILE
    
    # If the OUTPUT_FILE contains a directory separator, don't add the current_dir
    if os.path.sep in OUTPUT_FILE:
        output_path = OUTPUT_FILE
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Read the markdown file
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        print(f"Successfully read '{input_path}'")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return None
    
    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'tables', 'toc']
    )
    
    # Wrap HTML content with proper structure
    html_document = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{os.path.basename(INPUT_FILE)}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                padding: 2em;
                max-width: 900px;
                margin: 0 auto;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 1em;
                border-radius: 4px;
                overflow: auto;
            }}
            code {{
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
                font-size: 0.9em;
                background-color: #f5f5f5;
                padding: 0.2em 0.4em;
                border-radius: 3px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 1em;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #333;
                margin-top: 1.5em;
                margin-bottom: 0.5em;
            }}
            h1 {{
                border-bottom: 1px solid #eaecef;
                padding-bottom: 0.3em;
            }}
            blockquote {{
                border-left: 4px solid #ddd;
                padding-left: 1em;
                color: #666;
                margin-left: 0;
            }}
            img {{
                max-width: 100%;
            }}
            hr {{
                height: 1px;
                background-color: #ddd;
                border: none;
                margin: 2em 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Configure fonts
    font_config = FontConfiguration()
    
    # Convert HTML to PDF
    try:
        HTML(string=html_document).write_pdf(
            output_path,
            font_config=font_config
        )
        print(f"Successfully converted '{input_path}' to '{output_path}'")
        # Verify file existence
        if os.path.exists(output_path):
            print(f"PDF file confirmed at: {output_path}")
            return output_path
        else:
            print(f"PDF file not found at: {output_path}")
            return None
    except Exception as e:
        print(f"Error converting to PDF: {e}")
        
        try:
            # Clean the text to handle problematic unicode characters
            md_content = clean_text(md_content)
            
            # Create a FPDF object
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            
            # Process markdown
            lines = md_content.split('\n')
            for line in lines:
                # Handle headers
                if line.startswith('# '):
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(0, 10, line[2:], ln=True)
                    pdf.ln(5)
                elif line.startswith('## '):
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, line[3:], ln=True)
                    pdf.ln(5)
                elif line.startswith('### '):
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(0, 8, line[4:], ln=True)
                    pdf.ln(3)
                # Handle numbered lists
                elif line.strip() and line[0].isdigit() and '. ' in line:
                    pdf.set_font("Arial", '', 10)
                    # Split at the first occurrence of '. '
                    split_index = line.find('. ')
                    if split_index != -1:
                        number = line[:split_index+1]
                        text = line[split_index+2:]
                        pdf.cell(10, 5, number, ln=0)
                        # Use plain ASCII text for multi_cell
                        plain_text = ''.join(c if ord(c) < 128 else ' ' for c in text)
                        pdf.multi_cell(0, 5, plain_text)
                # Handle regular text
                elif line.strip():
                    pdf.set_font("Arial", '', 10)
                    # Use plain ASCII text for multi_cell
                    plain_text = ''.join(c if ord(c) < 128 else ' ' for c in line)
                    pdf.multi_cell(0, 5, plain_text)
                # Handle empty lines
                else:
                    pdf.ln(3)
            
            # Save the PDF
            pdf.output(output_path)
            print(f"Successfully converted '{input_path}' to '{output_path}' using fallback method")
            
            # Verify file existence
            if os.path.exists(output_path):
                print(f"PDF file confirmed at: {output_path}")
                return output_path
            else:
                print(f"PDF file not found at: {output_path}")
                return None
                
        except Exception as fallback_e:
            print(f"Error in fallback PDF conversion: {fallback_e}")
            return None

# Run the conversion
if __name__ == "__main__":
    markdown_to_pdf()