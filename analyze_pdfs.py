#!/usr/bin/env python3
"""
PDF Analysis Script for CloudSim Project Investigation
Extracts and analyzes content from all project-related PDFs
"""

import os
import sys
from pathlib import Path

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    print("Installing required libraries...")
    os.system("pip install PyPDF2 pdfplumber --quiet")
    import PyPDF2
    import pdfplumber

def extract_text_pypdf2(pdf_path):
    """Extract text using PyPDF2"""
    text = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            print(f"  Pages: {num_pages}")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text.append(f"\n{'='*80}\nPAGE {page_num + 1}\n{'='*80}\n")
                    text.append(page_text)
    except Exception as e:
        print(f"  PyPDF2 Error: {e}")
    
    return '\n'.join(text)

def extract_text_pdfplumber(pdf_path):
    """Extract text using pdfplumber (better for complex layouts)"""
    text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            print(f"  Pages: {num_pages}")
            
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text.append(f"\n{'='*80}\nPAGE {page_num + 1}\n{'='*80}\n")
                    text.append(page_text)
                    
                # Also extract tables if present
                tables = page.extract_tables()
                if tables:
                    text.append(f"\n[TABLES FOUND ON PAGE {page_num + 1}]\n")
                    for table_num, table in enumerate(tables):
                        text.append(f"\nTable {table_num + 1}:")
                        for row in table:
                            text.append(' | '.join(str(cell) if cell else '' for cell in row))
    except Exception as e:
        print(f"  pdfplumber Error: {e}")
    
    return '\n'.join(text)

def analyze_pdf(pdf_path):
    """Analyze a single PDF file"""
    print(f"\n{'#'*80}")
    print(f"Analyzing: {pdf_path}")
    print(f"Size: {os.path.getsize(pdf_path):,} bytes")
    print(f"{'#'*80}")
    
    # Try pdfplumber first (better quality)
    text = extract_text_pdfplumber(pdf_path)
    
    # Fallback to PyPDF2 if pdfplumber fails
    if not text or len(text) < 100:
        print("  Trying PyPDF2 as fallback...")
        text = extract_text_pypdf2(pdf_path)
    
    return text

def main():
    # PDF files found on Desktop
    pdf_files = [
        r"C:\Users\Fabiola\Desktop\maze game\Distributed Storage System Documentation.pdf",
        r"C:\Users\Fabiola\Desktop\maze game\Complete Setup Guide and Demo Script.pdf",
        r"C:\Users\Fabiola\Desktop\GROUP 17.pdf",
    ]
    
    output_dir = Path(r"C:\Users\Fabiola\Desktop\CloudSim\pdf_analysis")
    output_dir.mkdir(exist_ok=True)
    
    all_content = []
    
    for pdf_path in pdf_files:
        if os.path.exists(pdf_path):
            text = analyze_pdf(pdf_path)
            
            # Save individual analysis
            output_file = output_dir / f"{Path(pdf_path).stem}_extracted.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"  Saved to: {output_file}")
            
            all_content.append(f"\n\n{'#'*100}\n")
            all_content.append(f"SOURCE: {pdf_path}\n")
            all_content.append(f"{'#'*100}\n\n")
            all_content.append(text)
        else:
            print(f"File not found: {pdf_path}")
    
    # Save combined analysis
    combined_file = output_dir / "ALL_PDFs_COMBINED.txt"
    with open(combined_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_content))
    
    print(f"\n{'='*80}")
    print(f"ANALYSIS COMPLETE!")
    print(f"Combined output: {combined_file}")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

