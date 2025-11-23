from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class DocumentStatus(str, Enum):
    """Document status enumeration."""
    DRAFT = "draft"
    AWAITING_SIGNATURES = "awaiting_signatures"
    PARTIALLY_SIGNED = "partially_signed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FieldType(str, Enum):
    """Field type enumeration."""
    TEXT = "TEXT"
    SIGNATURE = "SIGNATURE"


# Request Models
class RecipientCreate(BaseModel):
    """Schema for creating a recipient."""
    id: str = Field(..., description="Unique identifier for the recipient")
    name: str = Field(..., min_length=1, description="Recipient's full name")
    email: EmailStr = Field(..., description="Recipient's email address")


class DocumentCreate(BaseModel):
    """Schema for creating a document."""
    recipients: List[RecipientCreate] = Field(..., min_items=1, description="List of recipients")


class FieldCreate(BaseModel):
    """Schema for creating a field."""
    type: FieldType
    recipientId: str = Field(..., alias="recipientId")
    page: int = Field(..., ge=1)
    x: float = Field(..., ge=0)
    y: float = Field(..., ge=0)
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    label: str = Field(..., min_length=1)
    
    class Config:
        populate_by_name = True


class FieldsCreate(BaseModel):
    """Schema for adding multiple fields."""
    fields: List[FieldCreate]


class FieldValue(BaseModel):
    """Schema for a field value during signing."""
    fieldId: str = Field(..., alias="fieldId")
    value: Optional[str] = None
    type: Optional[FieldType] = None
    signatureData: Optional[str] = Field(None, alias="signatureData")
    
    class Config:
        populate_by_name = True


class SignDocument(BaseModel):
    """Schema for signing a document."""
    recipientId: str = Field(..., alias="recipientId")
    token: str
    fieldValues: List[FieldValue] = Field(..., alias="fieldValues")
    
    class Config:
        populate_by_name = True


# Response Models
class RecipientResponse(BaseModel):
    """Schema for recipient response."""
    id: str
    recipient_id: str
    name: str
    email: str
    signed_at: Optional[int] = None


class SigningUrl(BaseModel):
    """Schema for a signing URL."""
    recipientId: str = Field(..., alias="recipientId")
    recipientName: str = Field(..., alias="recipientName")
    signingUrl: str = Field(..., alias="signingUrl")
    
    class Config:
        populate_by_name = True


class DocumentResponse(BaseModel):
    """Schema for document response."""
    documentId: str = Field(..., alias="documentId")
    status: DocumentStatus
    editorUrl: Optional[str] = Field(None, alias="editorUrl")
    
    class Config:
        populate_by_name = True


class DocumentStatusResponse(BaseModel):
    """Schema for document status response."""
    documentId: str = Field(..., alias="documentId")
    status: DocumentStatus
    recipients: List[RecipientResponse]
    created_at: int
    updated_at: int
    
    class Config:
        populate_by_name = True


class FinalizeResponse(BaseModel):
    """Schema for finalize response."""
    documentId: str = Field(..., alias="documentId")
    status: DocumentStatus
    signingUrls: List[SigningUrl] = Field(..., alias="signingUrls")
    
    class Config:
        populate_by_name = True


class FieldResponse(BaseModel):
    """Schema for field response."""
    id: str
    type: FieldType
    recipientId: str = Field(..., alias="recipientId")
    page: int
    x: float
    y: float
    width: float
    height: float
    label: str
    value: Optional[str] = None
    
    class Config:
        populate_by_name = True
