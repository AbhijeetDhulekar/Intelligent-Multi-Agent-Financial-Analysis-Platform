import pytesseract
from pdf2image import convert_from_path
import tempfile
import os

class OCRProcessor:
    def extract_text_with_ocr(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            full_text = ""
            
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image)
                full_text += f"--- Page {i+1} ---\n{text}\n"
            
            return full_text
        except Exception as e:
            print(f"OCR failed: {e}")
            return ""