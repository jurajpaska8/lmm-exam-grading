"""Redacts the name field of a non-anonymized submission with OCR (Tesseract),
as used to prepare the released dataset (Section V of the paper).

Needs real data that is NOT part of the repository (git-ignored):
    examples/private/<id>.pdf    one submission with readable name fields

Usage (from the repository root):
    python script_example_anonymization.py          # submission 000
    python script_example_anonymization.py 000

Output: examples/private/output/<id>_anonymized.pdf (also git-ignored). Open it and
check that the name is blacked out on every page.
"""
from helpers.anonymization import process_pdf_exam_redaction
import os
import shutil
import sys
import pytesseract

SUBMISSION_ID = sys.argv[1] if len(sys.argv) > 1 else "000"
SUBMISSION_PDF = f"examples/private/{SUBMISSION_ID}.pdf"
OUTPUT_FOLDER = "examples/private/output"
REDACT_WIDTH_PX = 1000  # same values as for the released dataset
DPI = 300

# Tesseract is often installed without being on PATH on Windows
WINDOWS_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if shutil.which("tesseract") is None and os.path.exists(WINDOWS_TESSERACT):
    pytesseract.pytesseract.tesseract_cmd = WINDOWS_TESSERACT

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
output_pdf = os.path.join(OUTPUT_FOLDER, f"{SUBMISSION_ID}_anonymized.pdf")

result = process_pdf_exam_redaction(
    input_pdf_path=SUBMISSION_PDF,
    output_pdf_path=output_pdf,
    redact_width_px=REDACT_WIDTH_PX,
    dpi=DPI,
)

print(f"Pages processed: {result['pages_processed']}, pages redacted: {result['pages_redacted']}")
if result["all_pages_redacted"]:
    print(f"Name field found and redacted on all pages: {output_pdf}")
else:
    print(f"WARNING: the name field was not found on every page, check manually: {output_pdf}")
