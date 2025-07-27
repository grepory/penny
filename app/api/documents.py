from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
import uuid
import shutil
from pathlib import Path
from datetime import datetime

from app.core.config import settings
from app.models.document import DocumentResponse, DocumentQuery, SearchResult
from app.services.document_service import DocumentService
from app.services.job_service import job_service

router = APIRouter(prefix="/documents", tags=["documents"])

# Initialize document service
document_service = DocumentService()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document and process it asynchronously
    Returns job ID for tracking progress
    """
    # Validate file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_extension} not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Generate unique filename
    document_id = str(uuid.uuid4())
    file_path = settings.DOCUMENTS_DIR / f"{document_id}_{file.filename}"
    
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Create document response
        document = DocumentResponse(
            id=document_id,
            filename=file.filename,
            file_path=str(file_path),
            content_type=file.content_type,
            file_size=len(content),
            uploaded_at=datetime.now(),
            indexed=False
        )
        
        # Initialize job service if needed
        if not job_service._initialized:
            await job_service.initialize()
        
        # Create async processing job
        job_id = await job_service.create_processing_job(document)
        
        return {
            "message": "File uploaded successfully",
            "document_id": document_id,
            "job_id": job_id,
            "filename": file.filename,
            "file_size": len(content),
            "status": "processing"
        }
        
    except Exception as e:
        # Clean up file if something went wrong
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.post("/search", response_model=List[SearchResult])
async def search_documents(query: DocumentQuery):
    """
    Search documents using vector similarity
    """
    try:
        results = await document_service.search_documents(query.query, query.limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document by ID (removes from disk and ChromaDB)
    """
    try:
        success = await document_service.delete_document(document_id)
        if success:
            return {"message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

@router.get("")
async def list_documents():
    """
    List all uploaded documents
    """
    try:
        documents = []
        for file_path in settings.DOCUMENTS_DIR.glob("*"):
            if file_path.is_file():
                # Extract document ID and original filename
                parts = file_path.name.split("_", 1)
                if len(parts) == 2:
                    doc_id, filename = parts
                    stat = file_path.stat()
                    documents.append({
                        "id": doc_id,
                        "filename": filename,
                        "file_path": str(file_path),
                        "file_size": stat.st_size,
                        "uploaded_at": datetime.fromtimestamp(stat.st_ctime),
                        "indexed": True  # Assume indexed if file exists
                    })
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")