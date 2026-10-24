import csv
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Tuple

import pypdfium2 as pdfium
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, NumberObject
import os

SCRIPT_DIR = Path(__file__).resolve().parent
ASSIGNMENTS_CSV = SCRIPT_DIR.parent / "results-pairing" / "actual_assignments.csv"
OUTPUT_DIR = SCRIPT_DIR.parent / "generated_pdfs"
PDF_COLUMNS = [
    "b-k-1-2.pdf",
    "b-k-3-4.pdf",
    "b-k-5-6.pdf",
    "b-k-7-8.pdf",
    "l-z-1-2.pdf",
    "l-z-3-4.pdf",
    "l-z-5-6.pdf",
    "l-z-7-8.pdf",
]


def load_actual_assignments(csv_path: Path) -> List[Dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def build_student_pages(student_row: Dict[str, str]) -> List[Tuple[Path, int]]:
    pages = []
    for column in PDF_COLUMNS:
        value = student_row.get(column, "-1").strip()
        if value and value != "-1":
            try:
                page_number = int(value)
            except ValueError:
                continue
            source_pdf = SCRIPT_DIR.parent / "raw_pdfs" / column
            pages.append((source_pdf, page_number))
    return pages


def render_pdf_page(pdf_path: Path, page_number: int) -> Image.Image:
    if not pdf_path.exists():
        raise FileNotFoundError(f"Source PDF not found: {pdf_path}")

    doc = pdfium.PdfDocument(str(pdf_path))
    try:
        if page_number < 0 or page_number >= len(doc):
            raise IndexError(f"Page {page_number} out of range for {pdf_path}")
        page = doc.get_page(page_number)
        try:
            try:
                pil_image = page.render_topil(scale=2).convert("RGB")
            except AttributeError:
                bitmap = page.render(scale=2)
                try:
                    pil_image = bitmap.to_pil().convert("RGB")
                finally:
                    bitmap.close()
        finally:
            page.close()
    finally:
        doc.close()
    return pil_image


def sanitize_filename(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", ascii_value)
    return cleaned.strip("_") or "student"


def save_student_pdf(student_idx: str, student_name: str, page_definitions: List[Tuple[Path, int]], output_dir: Path) -> Path:
    """
    Assemble a PDF by copying original pages (lossless) from source PDFs.
    Each copied page is rotated by 270 degrees (clockwise) to match required orientation.
    """
    writer = PdfWriter()

    for source_pdf, source_page in page_definitions:
        if not source_pdf.exists():
            raise FileNotFoundError(f"Source PDF not found: {source_pdf}")

        reader = PdfReader(str(source_pdf))
        if source_page < 0 or source_page >= len(reader.pages):
            raise IndexError(f"Page {source_page} out of range for {source_pdf}")

        page = reader.pages[source_page]

        # Set /Rotate entry to rotate page by 270 degrees (clockwise)
        try:
            current = page.get("/Rotate", 0)
            current_val = int(current) if current is not None else 0
        except Exception:
            current_val = 0

        try:
            page[NameObject("/Rotate")] = NumberObject((current_val + 270) % 360)
        except Exception:
            try:
                page.rotate_clockwise(270)
            except Exception:
                try:
                    page.rotate_counter_clockwise(90)
                except Exception:
                    pass

        writer.add_page(page)

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(student_name)
    filename = f"{int(student_idx):0>3}_{safe_name}.pdf"
    output_path = output_dir / filename

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def main() -> None:
    assignments = load_actual_assignments(ASSIGNMENTS_CSV)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for student in assignments:
        student_idx = student.get("student_idx", "unknown")
        student_name = student.get("student_name", "Unknown")
        page_defs = build_student_pages(student)

        if not page_defs:
            print(f"Skipping student {student_idx} ({student_name}) because no pages were assigned.")
            continue

        if len(page_defs) not in {2, 4}:
            print(
                f"Warning: student {student_idx} ({student_name}) has {len(page_defs)} pages assigned. "
                "Expected 2 or 4 pages. PDF will still be created."
            )

        output_path = save_student_pdf(student_idx, student_name, page_defs, OUTPUT_DIR)
        print(f"Created: {output_path} ({len(page_defs)} pages)")

    print(f"\nFinished generating PDFs in: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()

