from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

class DocumentUpload(BaseModel):
    filename: str
    content_type: str

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_path: str
    content_type: str
    file_size: int
    uploaded_at: datetime
    indexed: bool = False
    
    # Enhanced financial metadata
    is_financial_document: bool = False
    financial_document_id: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    processing_status: Optional[str] = None  # "pending", "processed", "failed", "manual_review"
    ocr_confidence: Optional[float] = None

class DocumentQuery(BaseModel):
    query: str
    limit: int = 5

class SearchResult(BaseModel):
    document_id: str
    filename: str
    content: str
    score: float
    
    # Enhanced financial search metadata
    is_financial_document: bool = False
    vendor_name: Optional[str] = None
    total_amount: Optional[float] = None
    invoice_date: Optional[str] = None
    project_name: Optional[str] = None
    categories: Optional[list] = None


class FinancialSearchQuery(BaseModel):
    """Enhanced search query for financial documents"""
    query: str
    limit: int = 5
    
    # Financial filters
    vendor_name: Optional[str] = None
    project_id: Optional[str] = None
    category: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    document_type: Optional[str] = None


class DocumentProcessingResult(BaseModel):
    """Result of document OCR and financial data extraction"""
    document_id: str
    success: bool
    processing_time: float
    confidence_score: Optional[float] = None
    extracted_data: Optional[Dict[str, Any]] = None
    errors: list = []
    warnings: list = []