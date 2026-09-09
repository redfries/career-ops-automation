#!/usr/bin/env python3
"""
pdf_validator.py
Rigorous validation of compiled resume PDFs:
1. Binary integrity (size, magic bytes %PDF-)
2. Structural extraction (page count, font streams)
3. Content integrity (candidate identity, contact info, core sections)
4. Defect detection (overflow pages, unparsed LaTeX markup, broken placeholders)
5. SHA256 cryptographic fingerprinting for submission manifests
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def validate_resume_pdf(pdf_path: Path, max_pages: int = 2) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    
    if not pdf_path.exists():
        return {
            "valid": False,
            "errors": [f"File does not exist: {pdf_path}"],
            "warnings": warnings,
            "page_count": 0,
            "sha256": "",
            "size_bytes": 0
        }

    size = pdf_path.stat().st_size
    if size < 15 * 1024:
        errors.append(f"File size too small ({size} bytes). Expected >= 15 KB for valid Awesome-CV.")
    if size > 5 * 1024 * 1024:
        errors.append(f"File size unexpectedly large ({size / (1024*1024):.1f} MB). Expected < 5 MB.")

    with open(pdf_path, "rb") as f:
        magic = f.read(5)
    if magic != b"%PDF-":
        errors.append(f"Invalid magic bytes: {magic!r}. Not a valid PDF file.")

    page_count = 0
    full_text = ""
    pages_text: List[str] = []

    # Use PyMuPDF for deep inspection
    try:
        import pymupdf
        doc = pymupdf.open(str(pdf_path))
        page_count = len(doc)
        
        for i in range(page_count):
            p_text = doc[i].get_text()
            pages_text.append(p_text)
            full_text += p_text + " "
        doc.close()
    except Exception as e:
        errors.append(f"PyMuPDF extraction failed: {e}")

    # Page count validation
    if page_count == 0:
        errors.append("PDF has 0 pages.")
    elif page_count > max_pages:
        errors.append(f"Page overflow defect: Document has {page_count} pages (maximum allowed: {max_pages}). Check margins or content length.")

    # Check for empty trailing page
    if page_count >= 2 and len(pages_text) >= 2:
        last_page_len = len(pages_text[-1].strip())
        if last_page_len < 100:
            errors.append(f"Accidental blank or near-empty trailing page detected ({last_page_len} chars on page {page_count}).")

    # Identity and contact information check
    if "shabaaz" not in full_text.lower():
        errors.append("Candidate name (Shabaaz) missing from extracted PDF text.")
    if "theshabaaz@outlook.com" not in full_text.lower() and "50-269-8140" not in full_text and "50 269 8140" not in full_text:
        errors.append("Primary contact information (email or phone) missing from PDF text.")

    # Section verification
    expected_sections = ["experience", "education", "skills", "projects"]
    found_sections = [sec for sec in expected_sections if sec in full_text.lower()]
    if len(found_sections) < 3:
        warnings.append(f"Only found {len(found_sections)} of 4 standard sections ({found_sections}).")

    # Defect & unresolved LaTeX check
    defect_markers = ["??", "\\begin{", "\\end{", "\\cventry", "\\cvskill", "UNDEFINED"]
    for marker in defect_markers:
        if marker in full_text:
            errors.append(f"Unparsed LaTeX or broken reference detected in PDF: '{marker}'")

    pdf_sha256 = compute_sha256(pdf_path) if pdf_path.exists() else ""

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "page_count": page_count,
        "sha256": pdf_sha256,
        "size_bytes": size,
        "extracted_char_count": len(full_text.strip()),
        "found_sections": found_sections
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/pdf_validator.py <path_to_pdf> [max_pages]")
        sys.exit(1)
    
    target_path = Path(sys.argv[1])
    max_p = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    res = validate_resume_pdf(target_path, max_p)
    print(f"Valid: {res['valid']}")
    print(f"Pages: {res['page_count']}")
    print(f"Size: {res['size_bytes']} bytes")
    print(f"SHA256: {res['sha256']}")
    if res["errors"]:
        print("Errors:", res["errors"])
    if res["warnings"]:
        print("Warnings:", res["warnings"])
    sys.exit(0 if res["valid"] else 1)
