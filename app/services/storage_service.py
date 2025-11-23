import shutil
from pathlib import Path
from typing import BinaryIO
from app.config import settings


class StorageService:
    """Service for file storage operations."""
    
    @staticmethod
    def save_pdf(document_id: str, file: BinaryIO) -> str:
        """
        Save an uploaded PDF file.
        
        Args:
            document_id: Unique document identifier
            file: File object to save
            
        Returns:
            Path to the saved file
        """
        # Create document directory
        doc_dir = Path(settings.upload_dir) / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        # Save original PDF
        file_path = doc_dir / "original.pdf"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)
        
        return str(file_path)
    
    @staticmethod
    def get_pdf_path(document_id: str, filename: str = "original.pdf") -> str:
        """
        Get the path to a PDF file.
        
        Args:
            document_id: Document identifier
            filename: Name of the file (default: original.pdf)
            
        Returns:
            Path to the PDF file
        """
        return str(Path(settings.upload_dir) / document_id / filename)
    
    @staticmethod
    def save_completed_pdf(document_id: str, pdf_bytes: bytes) -> str:
        """
        Save the completed/signed PDF.
        
        Args:
            document_id: Document identifier
            pdf_bytes: PDF file bytes
            
        Returns:
            Path to the saved file
        """
        doc_dir = Path(settings.upload_dir) / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = doc_dir / "completed.pdf"
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        
        return str(file_path)
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if a file exists."""
        return Path(file_path).exists()
