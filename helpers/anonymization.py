import fitz  # PyMuPDF
import cv2
import numpy as np
import os
import pytesseract

def redact_after_meno_ocr(cv_img, redact_width_px):
    """
    Locates 'Meno:' using Tesseract OCR, identifies its right-hand edge,
    and redacts 'redact_width_px' pixels immediately to its right.
    Returns the modified image, the number of redactions found on the page.
    """
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    
    # Run Tesseract with Page Segmentation Mode 6 (Sparse text block)
    data = pytesseract.image_to_data(
        gray, 
        output_type=pytesseract.Output.DICT, 
        config='--psm 6'
    )
    
    n_boxes = len(data['text'])
    found_count = 0

    for i in range(n_boxes):
        word = data['text'][i].strip().lower()
        try:
            conf = float(data['conf'][i])
        except (ValueError, TypeError):
            continue

        # Match or 'meno:' 'men:' 'meno;'
        # OR if it is just meno, but in the beggining of the page
        if ("meno:" in word or "men:" in word or "meno;" in word) or ("meno" == word and i <= 10):
            if(("meno" == word and i <= 10) and not ("meno:" in word or "men:" in word or "meno;" in word)):
                print(f"Found 'meno' at index {i} with confidence {conf}, treating as match.")

            x = data['left'][i]
            y = data['top'][i]
            w = data['width'][i]

            # Calculate start coordinate: right edge of the word 'Meno:'
            x_start = x + w
            
            # Define redaction region coordinates
            x_end = min(cv_img.shape[1], x_start + redact_width_px)
            y_top = 0  # we want to redact from top
            y_bottom = min(cv_img.shape[0], 170)

            # Burn solid black rectangle to zero out pixels
            cv2.rectangle(cv_img, (x_start, y_top), (x_end, y_bottom), (0, 0, 0), -1)
            found_count += 1

    return cv_img, found_count

def process_pdf_exam_redaction(input_pdf_path, output_pdf_path, redact_width_px, dpi=300):
    """
    Renders PDF pages to images, applies OCR anchor-based right-side redaction,
    and outputs the sanitized PDF document.
    Returns a summary dict for the processed PDF.
    """
    doc = fitz.open(input_pdf_path)
    out_doc = fitz.open()

    pdf_pages = 0
    redacted_pages = 0

    for page in doc:
        pdf_pages += 1

        # Render PDF page to high-res OpenCV matrix
        pix = page.get_pixmap(dpi=dpi)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR)

        # Apply redaction
        clean_img, count = redact_after_meno_ocr(
            img_bgr,
            redact_width_px=redact_width_px,
        )

        if count > 0:
            redacted_pages += 1

        # Convert back to clean PDF page
        _, img_encoded = cv2.imencode(".png", clean_img)
        new_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
        new_page.insert_image(new_page.rect, stream=img_encoded.tobytes())

    out_doc.save(output_pdf_path, deflate=True)
    out_doc.close()
    doc.close()

    return {
        "pages_processed": pdf_pages,
        "pages_redacted": redacted_pages,
        "all_pages_redacted": pdf_pages > 0 and redacted_pages == pdf_pages
    }

def process_pdf_exam_redaction_folder(
    input_folder,
    output_folder,
    redact_width_px,
    dpi=300,
):
    """
    Process every PDF file in input_folder and save anonymized copies to output_folder
    with names like <prefix>.pdf, <next>.pdf, ...
    """
    os.makedirs(output_folder, exist_ok=True)

    pdf_files = sorted(
        [
            f
            for f in os.listdir(input_folder)
            if os.path.isfile(os.path.join(input_folder, f))
            and f.lower().endswith(".pdf")
        ]
    )

    total_pdf_count = 0
    total_page_count = 0
    total_redacted_page_count = 0
    total_all_pages_redacted = 0

    for filename in pdf_files:
        total_pdf_count += 1
        input_pdf_path = os.path.join(input_folder, filename)
        output_prefix = os.path.splitext(filename)[0].split("_")[0]
        output_pdf_name = f"{output_prefix}.pdf"
        output_pdf_path = os.path.join(output_folder, output_pdf_name)

        print(f"Anonymizing {filename}")
        result = process_pdf_exam_redaction(
            input_pdf_path=input_pdf_path,
            output_pdf_path=output_pdf_path,
            redact_width_px=redact_width_px,
            dpi=dpi,
        )

        if not result["all_pages_redacted"]:
            output_pdf_name = f"{output_prefix}_check.pdf"
            checked_output_pdf_path = os.path.join(output_folder, output_pdf_name)
            os.replace(output_pdf_path, checked_output_pdf_path)
            output_pdf_path = checked_output_pdf_path

        print(
            f"    pages processed: {result['pages_processed']}, "
            f"pages redacted: {result['pages_redacted']}, "
            f"all pages redacted: {result['all_pages_redacted']}, "
            f"output: {output_pdf_name}"
        )

        total_page_count += result["pages_processed"]
        total_redacted_page_count += result["pages_redacted"]
        if result["all_pages_redacted"]:
            total_all_pages_redacted += 1
    print("\nAnonymization summary:")
    print(f"  PDFs processed: {total_pdf_count}")
    print(f"  pages processed: {total_page_count}")
    print(f"  PDFs with redaction on all pages: {total_all_pages_redacted}")
    print(f"  pages redacted: {total_redacted_page_count}")


if __name__ == "__main__":
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_folder = os.path.join(
        repo_root,
        "assignments",
        "y2026",
        "exam",
        "generated_pdfs",
    )
    output_folder = os.path.join(
        repo_root,
        "assignments",
        "y2026",
        "exam",
        "anonymized_pdfs",
    )

    process_pdf_exam_redaction_folder(
        input_folder=input_folder,
        output_folder=output_folder,
        redact_width_px=1000,  # Change this pixel value if student names are longer
    )

