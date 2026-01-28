import requests
import pdfplumber
from io import BytesIO
from typing import Optional

class PDFService:
    """Handle PDF fetching and text extraction"""
    
    def fetch_pdf(self, url: str) -> bytes:
        """Download PDF from URL"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise ValueError(f"Failed to fetch PDF: {str(e)}")
    
    def extract_text(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF using pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            if not text.strip():
                raise ValueError("No text extracted from PDF")
            
            return text.strip()
        
        except Exception as e:
            raise ValueError(f"Failed to extract text: {str(e)}")
