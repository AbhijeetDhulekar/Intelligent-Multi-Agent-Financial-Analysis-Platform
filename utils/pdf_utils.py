import PyPDF2
from pathlib import Path
from typing import List, Dict, Any

class PDFValidator:
    """Utility class for PDF validation and information extraction"""
    
    @staticmethod
    def validate_pdf(file_path: str) -> Dict[str, Any]:
        """Validate PDF file and extract basic information"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                info = {
                    "is_valid": True,
                    "total_pages": len(pdf_reader.pages),
                    "has_text": False,
                    "file_size_mb": round(Path(file_path).stat().st_size / (1024 * 1024), 2),
                    "metadata": pdf_reader.metadata or {}
                }
                
                # Check if PDF contains extractable text
                for page in pdf_reader.pages[:3]:  # Check first 3 pages
                    text = page.extract_text()
                    if text and len(text.strip()) > 100:  # Reasonable amount of text
                        info["has_text"] = True
                        break
                
                return info
                
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e)
            }
    
    @staticmethod
    def extract_page_text(file_path: str, page_number: int) -> str:
        """Extract text from specific page"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if page_number < len(pdf_reader.pages):
                    return pdf_reader.pages[page_number].extract_text() or ""
                return ""
        except Exception as e:
            print(f"Error extracting text from page {page_number}: {str(e)}")
            return ""
    
    @staticmethod
    def get_pdf_info(file_path: str) -> Dict[str, Any]:
        """Get comprehensive PDF information"""
        validation = PDFValidator.validate_pdf(file_path)
        
        if not validation["is_valid"]:
            return validation
        
        # Additional info for valid PDFs
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            info = {
                **validation,
                "encrypted": pdf_reader.is_encrypted,
                "pages": []
            }
            
            # Sample text from first few pages
            for i in range(min(3, len(pdf_reader.pages))):
                text = pdf_reader.pages[i].extract_text() or ""
                info["pages"].append({
                    "page_number": i + 1,
                    "text_preview": text[:200] + "..." if len(text) > 200 else text,
                    "has_content": len(text.strip()) > 0
                })
            
            return info

# Example usage
if __name__ == "__main__":
    validator = PDFValidator()
    info = validator.get_pdf_info("data_raw/Financial_Statements/FAB_2022_Q1_Financial_Statement.pdf")
    print(f"PDF Info: {info}")
    