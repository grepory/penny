import shutil
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import uuid
from pathlib import Path
from pydantic import BaseModel

router = APIRouter(prefix="/api/files", tags=["files"])

# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class FileResponse(BaseModel):
    id: str
    name: str
    size: int
    type: str
    upload_date: datetime

def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (this is an approximation since we don't read the full file)
    if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file"""
    try:
        validate_file(file)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix.lower()
        unique_filename = f"{file_id}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file stats
        file_stats = file_path.stat()
        
        return {
            "id": file_id,
            "name": file.filename,
            "size": file_stats.st_size,
            "type": file.content_type,
            "upload_date": datetime.fromtimestamp(file_stats.st_mtime),
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        # Clean up file if it was partially created
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/", response_model=List[FileResponse])
async def list_files():
    """List all uploaded files"""
    try:
        files = []
        
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_stats = file_path.stat()
                file_id = file_path.stem  # filename without extension
                
                # Try to get original filename from a metadata file, or use the current name
                original_name = file_path.name
                
                # Determine content type based on extension
                file_ext = file_path.suffix.lower()
                content_type = {
                    '.pdf': 'application/pdf',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png'
                }.get(file_ext, 'application/octet-stream')
                
                files.append({
                    "id": file_id,
                    "name": original_name,
                    "size": file_stats.st_size,
                    "type": content_type,
                    "upload_date": datetime.fromtimestamp(file_stats.st_mtime)
                })
        
        # Sort by upload date (newest first)
        files.sort(key=lambda x: x["upload_date"], reverse=True)
        return files
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """Delete a file by ID"""
    try:
        # Find file with matching ID (stem)
        matching_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = matching_files[0]
        file_path.unlink()
        
        return {"message": "File deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.get("/{file_id}/info")
async def get_file_info(file_id: str):
    """Get information about a specific file"""
    try:
        # Find file with matching ID
        matching_files = list(UPLOAD_DIR.glob(f"{file_id}.*"))
        
        if not matching_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = matching_files[0]
        file_stats = file_path.stat()
        
        # Determine content type
        file_ext = file_path.suffix.lower()
        content_type = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png'
        }.get(file_ext, 'application/octet-stream')
        
        return {
            "id": file_id,
            "name": file_path.name,
            "size": file_stats.st_size,
            "type": content_type,
            "upload_date": datetime.fromtimestamp(file_stats.st_mtime),
            "path": str(file_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")