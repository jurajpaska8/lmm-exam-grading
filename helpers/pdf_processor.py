import pypdfium2 as pdfium
from PIL.Image import Image

class PDFProcessor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    @staticmethod
    def _extract_page_images(pdf_file: str, first_page: int, last_page: int | None = None) -> list[Image]:
        pdf = pdfium.PdfDocument(pdf_file)
        images = []
        start_idx = max(0, first_page - 1)
        end_idx = len(pdf) if last_page is None else min(last_page, len(pdf))
        
        for i in range(start_idx, end_idx):
            page = pdf[i]
            # scale=4 roughly translates to ~288 DPI.
            pil_image = page.render(scale=4).to_pil()
            pil_image = pil_image.convert("L") # Convert to grayscale to match previous behaviour
            images.append(pil_image)
            
        return images