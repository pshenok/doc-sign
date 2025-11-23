import io
import base64
from typing import List, Dict
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image


class PDFService:
    """Service for PDF manipulation and generation."""
    
    @staticmethod
    def get_pdf_info(pdf_path: str) -> Dict:
        """
        Get information about a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing PDF metadata
        """
        reader = PdfReader(pdf_path)
        return {
            "num_pages": len(reader.pages),
            "metadata": reader.metadata
        }
    
    @staticmethod
    def create_overlay(fields: List[Dict], page_num: int, page_width: float, page_height: float) -> bytes:
        """
        Create a PDF overlay with text and signature fields.
        
        Args:
            fields: List of field dictionaries with values
            page_num: Page number to create overlay for
            page_width: Width of the page
            page_height: Height of the page
            
        Returns:
            PDF bytes of the overlay
        """
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
        
        # Filter fields for this page
        page_fields = [f for f in fields if f.get('page') == page_num and f.get('value') is not None]
        
        for field in page_fields:
            field_type = field.get('type')
            x = field.get('x', 0)
            # Convert y coordinate (PDF coordinates start from bottom)
            y = page_height - field.get('y', 0) - field.get('height', 0)
            width = field.get('width', 100)
            height = field.get('height', 20)
            
            if field_type == 'TEXT':
                # Draw text field
                value = field.get('value', '')
                can.setFont("Helvetica", 10)
                can.drawString(x + 2, y + height/2 - 3, value)
                
            elif field_type == 'SIGNATURE':
                # Draw signature image
                signature_data = field.get('signature_data')
                if signature_data:
                    try:
                        # Decode base64 signature
                        if ',' in signature_data:
                            signature_data = signature_data.split(',')[1]
                        
                        img_data = base64.b64decode(signature_data)
                        img = Image.open(io.BytesIO(img_data))
                        
                        # Save to temp buffer
                        img_buffer = io.BytesIO()
                        img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        
                        # Draw image on canvas
                        can.drawImage(ImageReader(img_buffer), x, y, width, height, 
                                     preserveAspectRatio=True, mask='auto')
                    except Exception as e:
                        # If signature fails, just draw placeholder text
                        can.setFont("Helvetica-Oblique", 8)
                        can.drawString(x + 2, y + height/2 - 3, "[Signature]")
        
        can.save()
        packet.seek(0)
        return packet.getvalue()
    
    @staticmethod
    def merge_pdf_with_fields(pdf_path: str, fields: List[Dict]) -> bytes:
        """
        Merge original PDF with field overlays.
        
        Args:
            pdf_path: Path to the original PDF
            fields: List of fields with values to overlay
            
        Returns:
            Bytes of the completed PDF
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Process each page
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # Create overlay for this page
            overlay_bytes = PDFService.create_overlay(
                fields, 
                page_num + 1,  # Pages are 1-indexed in our system
                page_width, 
                page_height
            )
            
            # Merge overlay with original page if there are fields
            if overlay_bytes:
                overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
                if len(overlay_reader.pages) > 0:
                    page.merge_page(overlay_reader.pages[0])
            
            writer.add_page(page)
        
        # Write to bytes
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def validate_pdf(file_path: str) -> bool:
        """
        Validate that a file is a valid PDF.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            reader = PdfReader(file_path)
            # Try to access pages to ensure it's readable
            _ = len(reader.pages)
            return True
        except Exception:
            return False
