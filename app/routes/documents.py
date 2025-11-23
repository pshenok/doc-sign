import uuid
import time
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import FileResponse

from app.models import (
    DocumentCreate, DocumentResponse, DocumentStatusResponse,
    FieldsCreate, FinalizeResponse, SignDocument,
    RecipientResponse, DocumentStatus
)
from app.database import get_db, dict_from_row
from app.services.storage_service import StorageService
from app.services.token_service import TokenService
from app.services.pdf_service import PDFService
from app.config import settings


router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def create_document(
    recipients: str = File(..., description="JSON string of recipients"),
    pdfFile: UploadFile = File(..., description="PDF file to upload")
):
    """
    Upload a PDF document and create a new document with recipients.
    
    The PDF file is stored and recipients are registered for signing.
    Returns a document ID and editor URL for field placement.
    """
    # Validate PDF file
    if not pdfFile.content_type == "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Parse recipients JSON
    import json
    try:
        recipients_data = json.loads(recipients)
        doc_create = DocumentCreate(**recipients_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid recipients data: {str(e)}")
    
    # Generate document ID
    document_id = f"doc_{uuid.uuid4().hex[:10]}"
    
    # Save PDF file
    try:
        pdf_path = StorageService.save_pdf(document_id, pdfFile.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save PDF: {str(e)}")
    
    # Validate PDF
    if not PDFService.validate_pdf(pdf_path):
        raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file")
    
    # Store document in database
    current_time = int(time.time())
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Insert document
        cursor.execute(
            """
            INSERT INTO documents (id, original_pdf_path, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (document_id, pdf_path, DocumentStatus.DRAFT, current_time, current_time)
        )
        
        # Insert recipients
        for recipient in doc_create.recipients:
            recipient_db_id = f"rec_{uuid.uuid4().hex[:10]}"
            # Generate token for this recipient (will be used later during finalize)
            token = TokenService.generate_token(document_id, recipient.id)
            
            cursor.execute(
                """
                INSERT INTO recipients 
                (id, document_id, recipient_id, name, email, token, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (recipient_db_id, document_id, recipient.id, recipient.name, 
                 recipient.email, token, current_time)
            )
    
    # Generate editor URL
    editor_url = f"{settings.base_url}/editor/{document_id}"
    
    return DocumentResponse(
        documentId=document_id,
        status=DocumentStatus.DRAFT,
        editorUrl=editor_url
    )


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document(document_id: str):
    """
    Get the status and details of a document.
    
    Returns document metadata including all recipients and their signing status.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get document
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        doc_row = cursor.fetchone()
        
        if not doc_row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc = dict_from_row(doc_row)
        
        # Get recipients
        cursor.execute(
            "SELECT * FROM recipients WHERE document_id = ?",
            (document_id,)
        )
        recipients = [dict_from_row(row) for row in cursor.fetchall()]
    
    return DocumentStatusResponse(
        documentId=doc['id'],
        status=doc['status'],
        recipients=[
            RecipientResponse(
                id=r['id'],
                recipient_id=r['recipient_id'],
                name=r['name'],
                email=r['email'],
                signed_at=r['signed_at']
            )
            for r in recipients
        ],
        created_at=doc['created_at'],
        updated_at=doc['updated_at']
    )


@router.post("/{document_id}/fields", status_code=201)
async def add_fields(document_id: str, fields_data: FieldsCreate):
    """
    Add fields (tags) to the document for recipients to fill out.
    
    Fields define where recipients will place their signatures and text inputs.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify document exists and is in draft status
        cursor.execute("SELECT status FROM documents WHERE id = ?", (document_id,))
        doc_row = cursor.fetchone()
        
        if not doc_row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if doc_row[0] != DocumentStatus.DRAFT:
            raise HTTPException(
                status_code=400, 
                detail="Can only add fields to documents in draft status"
            )
        
        # Insert fields
        current_time = int(time.time())
        for field in fields_data.fields:
            field_id = f"field_{uuid.uuid4().hex[:10]}"
            
            cursor.execute(
                """
                INSERT INTO fields 
                (id, document_id, recipient_id, type, page, x, y, width, height, label, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (field_id, document_id, field.recipientId, field.type, 
                 field.page, field.x, field.y, field.width, field.height, 
                 field.label, current_time)
            )
        
        # Update document timestamp
        cursor.execute(
            "UPDATE documents SET updated_at = ? WHERE id = ?",
            (current_time, document_id)
        )
    
    return {"message": "Fields added successfully", "count": len(fields_data.fields)}


@router.post("/{document_id}/finalize", response_model=FinalizeResponse)
async def finalize_document(document_id: str):
    """
    Finalize the document and generate signing URLs for all recipients.
    
    After finalization, recipients can use their unique URLs to sign the document.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get document
        cursor.execute("SELECT status FROM documents WHERE id = ?", (document_id,))
        doc_row = cursor.fetchone()
        
        if not doc_row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if doc_row[0] != DocumentStatus.DRAFT:
            raise HTTPException(
                status_code=400,
                detail="Can only finalize documents in draft status"
            )
        
        # Get recipients
        cursor.execute(
            "SELECT id, recipient_id, name, email, token FROM recipients WHERE document_id = ?",
            (document_id,)
        )
        recipients = [dict_from_row(row) for row in cursor.fetchall()]
        
        if not recipients:
            raise HTTPException(status_code=400, detail="No recipients found")
        
        # Update document status
        current_time = int(time.time())
        cursor.execute(
            "UPDATE documents SET status = ?, updated_at = ? WHERE id = ?",
            (DocumentStatus.AWAITING_SIGNATURES, current_time, document_id)
        )
    
    # Generate signing URLs
    signing_urls = []
    for recipient in recipients:
        signing_url = f"{settings.base_url}/sign/{document_id}?token={recipient['token']}"
        signing_urls.append({
            "recipientId": recipient['recipient_id'],
            "recipientName": recipient['name'],
            "signingUrl": signing_url
        })
    
    from app.models import SigningUrl
    return FinalizeResponse(
        documentId=document_id,
        status=DocumentStatus.AWAITING_SIGNATURES,
        signingUrls=[SigningUrl(**url) for url in signing_urls]
    )


@router.post("/{document_id}/sign")
async def sign_document(document_id: str, sign_data: SignDocument):
    """
    Sign the document by filling out assigned fields.
    
    Recipients submit their field values and signatures through this endpoint.
    """
    # Validate token
    try:
        token_payload = TokenService.validate_token(sign_data.token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    # Verify token matches document and recipient
    if token_payload['document_id'] != document_id:
        raise HTTPException(status_code=401, detail="Token does not match document")
    
    if token_payload['recipient_id'] != sign_data.recipientId:
        raise HTTPException(status_code=401, detail="Token does not match recipient")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verify document status
        cursor.execute("SELECT status FROM documents WHERE id = ?", (document_id,))
        doc_row = cursor.fetchone()
        
        if not doc_row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        status = doc_row[0]
        if status not in [DocumentStatus.AWAITING_SIGNATURES, DocumentStatus.PARTIALLY_SIGNED]:
            raise HTTPException(
                status_code=400,
                detail=f"Document is not available for signing (status: {status})"
            )
        
        # Get recipient
        cursor.execute(
            "SELECT id, signed_at FROM recipients WHERE document_id = ? AND recipient_id = ?",
            (document_id, sign_data.recipientId)
        )
        recipient_row = cursor.fetchone()
        
        if not recipient_row:
            raise HTTPException(status_code=404, detail="Recipient not found")
        
        if recipient_row[1] is not None:
            raise HTTPException(status_code=400, detail="Recipient has already signed")
        
        # Update field values
        current_time = int(time.time())
        for field_value in sign_data.fieldValues:
            if field_value.type == "SIGNATURE":
                cursor.execute(
                    "UPDATE fields SET signature_data = ? WHERE id = ? AND document_id = ?",
                    (field_value.signatureData, field_value.fieldId, document_id)
                )
            else:
                cursor.execute(
                    "UPDATE fields SET value = ? WHERE id = ? AND document_id = ?",
                    (field_value.value, field_value.fieldId, document_id)
                )
        
        # Mark recipient as signed
        cursor.execute(
            "UPDATE recipients SET signed_at = ? WHERE id = ?",
            (current_time, recipient_row[0])
        )
        
        # Check if all recipients have signed
        cursor.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN signed_at IS NOT NULL THEN 1 ELSE 0 END) as signed FROM recipients WHERE document_id = ?",
            (document_id,)
        )
        counts = cursor.fetchone()
        
        new_status = DocumentStatus.COMPLETED if counts[0] == counts[1] else DocumentStatus.PARTIALLY_SIGNED
        
        # Update document status
        cursor.execute(
            "UPDATE documents SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, current_time, document_id)
        )
    
    return {
        "message": "Document signed successfully",
        "status": new_status
    }


@router.get("/{document_id}/download")
async def download_document(document_id: str):
    """
    Download the completed document with all signatures.
    
    Only available when all recipients have signed the document.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get document
        cursor.execute("SELECT status, original_pdf_path FROM documents WHERE id = ?", (document_id,))
        doc_row = cursor.fetchone()
        
        if not doc_row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        status, pdf_path = doc_row
        
        if status != DocumentStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail="Document is not completed yet. All recipients must sign first."
            )
        
        # Check if completed PDF already exists
        completed_path = StorageService.get_pdf_path(document_id, "completed.pdf")
        
        if not StorageService.file_exists(completed_path):
            # Generate completed PDF
            cursor.execute(
                "SELECT id, type, page, x, y, width, height, label, value, signature_data FROM fields WHERE document_id = ?",
                (document_id,)
            )
            fields = [dict_from_row(row) for row in cursor.fetchall()]
            
            # Generate PDF with all field values
            completed_pdf_bytes = PDFService.merge_pdf_with_fields(pdf_path, fields)
            
            # Save completed PDF
            completed_path = StorageService.save_completed_pdf(document_id, completed_pdf_bytes)
        
        # Return the file
        return FileResponse(
            completed_path,
            media_type="application/pdf",
            filename=f"signed_document_{document_id}.pdf"
        )
