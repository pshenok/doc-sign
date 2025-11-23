from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import init_directories, settings
from app.database import init_database
from app.routes import documents


# Create FastAPI app
app = FastAPI(
    title="E-Signature API",
    description="API for creating and signing PDF documents with multiple recipients",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("Initializing directories...")
    init_directories()
    
    print("Initializing database...")
    init_database()
    
    print(f"Application started successfully!")
    print(f"Base URL: {settings.base_url}")
    print(f"API Docs: {settings.base_url}/docs")


# Include routers
app.include_router(documents.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "E-Signature API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "create_document": "POST /api/documents",
            "get_document": "GET /api/documents/{id}",
            "add_fields": "POST /api/documents/{id}/fields",
            "finalize": "POST /api/documents/{id}/finalize",
            "sign": "POST /api/documents/{id}/sign",
            "download": "GET /api/documents/{id}/download"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
