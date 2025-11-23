# E-Signature API

A DocuSign-like API for creating and signing PDF documents with multiple recipients. Built with Python FastAPI and featuring PDF manipulation capabilities.

## Features

- 📄 Upload PDF documents
- 👥 Multi-recipient support
- ✍️ Text and signature field placement
- 🔐 JWT-based secure signing URLs
- 📝 Complete signing workflow
- ⬇️ Download signed documents

## Technology Stack

- **FastAPI** - Modern, fast web framework
- **SQLite** - Lightweight database
- **PyPDF2** - PDF manipulation
- **reportlab** - PDF generation
- **Pillow** - Image processing
- **PyJWT** - Token authentication

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd doc-sign
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env and set your JWT_SECRET
```

### 5. Run the server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

Interactive API documentation at `http://localhost:8000/docs`

## API Endpoints

### 1. Create Document

Upload a PDF and register recipients.

**Endpoint:** `POST /api/documents`

**Request:**
- `pdfFile`: PDF file (multipart/form-data)
- `recipients`: JSON string with recipient data

```bash
curl -X POST http://localhost:8000/api/documents \
  -F 'pdfFile=@document.pdf' \
  -F 'recipients={"recipients":[{"id":"recipient_1","name":"John Doe","email":"john@example.com"}]}'
```

**Response:**
```json
{
  "documentId": "doc_abc123",
  "editorUrl": "http://localhost:8000/editor/doc_abc123",
  "status": "draft"
}
```

### 2. Get Document Status

Retrieve document information and recipient status.

**Endpoint:** `GET /api/documents/{document_id}`

```bash
curl http://localhost:8000/api/documents/doc_abc123
```

### 3. Add Fields

Place text and signature fields on the PDF.

**Endpoint:** `POST /api/documents/{document_id}/fields`

```bash
curl -X POST http://localhost:8000/api/documents/doc_abc123/fields \
  -H "Content-Type: application/json" \
  -d '{
    "fields": [
      {
        "type": "TEXT",
        "recipientId": "recipient_1",
        "page": 1,
        "x": 100,
        "y": 200,
        "width": 200,
        "height": 30,
        "label": "Full Name"
      },
      {
        "type": "SIGNATURE",
        "recipientId": "recipient_1",
        "page": 1,
        "x": 100,
        "y": 500,
        "width": 300,
        "height": 80,
        "label": "Signature"
      }
    ]
  }'
```

### 4. Finalize Document

Generate signing URLs for all recipients.

**Endpoint:** `POST /api/documents/{document_id}/finalize`

```bash
curl -X POST http://localhost:8000/api/documents/doc_abc123/finalize
```

**Response:**
```json
{
  "documentId": "doc_abc123",
  "status": "awaiting_signatures",
  "signingUrls": [
    {
      "recipientId": "recipient_1",
      "recipientName": "John Doe",
      "signingUrl": "http://localhost:8000/sign/doc_abc123?token=..."
    }
  ]
}
```

### 5. Sign Document

Submit signatures and field values.

**Endpoint:** `POST /api/documents/{document_id}/sign`

```bash
curl -X POST http://localhost:8000/api/documents/doc_abc123/sign \
  -H "Content-Type: application/json" \
  -d '{
    "recipientId": "recipient_1",
    "token": "eyJ...",
    "fieldValues": [
      {
        "fieldId": "field_123",
        "value": "John Doe"
      },
      {
        "fieldId": "field_456",
        "type": "SIGNATURE",
        "signatureData": "data:image/png;base64,iVBORw0KGgo..."
      }
    ]
  }'
```

### 6. Download Signed Document

Download the completed PDF with all signatures.

**Endpoint:** `GET /api/documents/{document_id}/download`

```bash
curl http://localhost:8000/api/documents/doc_abc123/download -o signed_document.pdf
```

## Document Status Flow

```
draft → awaiting_signatures → partially_signed → completed
```

- **draft**: Document created, fields being placed
- **awaiting_signatures**: Finalized, waiting for all signatures
- **partially_signed**: Some recipients have signed
- **completed**: All recipients have signed

## Project Structure

```
doc-sign/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database setup and utilities
│   ├── models.py          # Pydantic models
│   ├── routes/
│   │   ├── __init__.py
│   │   └── documents.py   # Document endpoints
│   └── services/
│       ├── __init__.py
│       ├── pdf_service.py     # PDF manipulation
│       ├── token_service.py   # JWT tokens
│       └── storage_service.py # File storage
├── data/                  # SQLite database (auto-created)
└── uploads/              # Uploaded PDFs (auto-created)
```

## Development

### Run with auto-reload

```bash
uvicorn main:app --reload
```

### View API documentation

Open your browser and navigate to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Security Notes

- Change `JWT_SECRET` in production to a secure random value
- In production, configure CORS to allow only specific origins
- Implement proper authentication/authorization for document creation
- Add rate limiting for API endpoints
- Use HTTPS in production

## License

MIT