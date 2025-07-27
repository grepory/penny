"""
SQLAlchemy models for job tracking and async processing
"""

from sqlalchemy import Column, String, Text, DateTime, Float, Integer, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()


class ProcessingJob(Base):
    """Model for tracking document processing jobs"""
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True)  # UUID
    document_id = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Job status and progress
    status = Column(String, nullable=False, default="pending", index=True)  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)  # 0.0 to 100.0
    current_step = Column(String, nullable=True)  # Current processing step
    total_steps = Column(Integer, default=4)  # Total number of processing steps
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results and errors
    result = Column(JSON, nullable=True)  # Processing results
    error_message = Column(Text, nullable=True)
    
    # Processing details
    llamaparse_job_id = Column(String, nullable=True)  # LlamaParse job ID
    financial_data_extracted = Column(Boolean, default=False)
    indexed_in_chroma = Column(Boolean, default=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "llamaparse_job_id": self.llamaparse_job_id,
            "financial_data_extracted": self.financial_data_extracted,
            "indexed_in_chroma": self.indexed_in_chroma,
            "result": self.result
        }


class DocumentMetadata(Base):
    """Extended document metadata storage"""
    __tablename__ = "document_metadata"
    
    id = Column(String, primary_key=True)  # Same as document_id
    document_id = Column(String, nullable=False, unique=True, index=True)
    filename = Column(String, nullable=False)
    
    # Financial metadata extracted from documents
    document_type = Column(String, nullable=True)  # invoice, receipt, estimate, etc.
    vendor_name = Column(String, nullable=True, index=True)
    vendor_address = Column(Text, nullable=True)
    vendor_phone = Column(String, nullable=True)
    vendor_email = Column(String, nullable=True)
    
    # Financial details
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(DateTime, nullable=True, index=True)
    due_date = Column(DateTime, nullable=True)
    total_amount = Column(Float, nullable=True, index=True)
    currency = Column(String, default="USD")
    
    # Project association
    project_name = Column(String, nullable=True, index=True)
    project_id = Column(String, nullable=True, index=True)
    
    # Categories and tags
    expense_categories = Column(JSON, nullable=True)  # List of categories
    tags = Column(JSON, nullable=True)  # List of tags
    
    # Processing metadata
    confidence_score = Column(Float, nullable=True)  # Extraction confidence
    manually_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "filename": self.filename,
            "document_type": self.document_type,
            "vendor_name": self.vendor_name,
            "vendor_address": self.vendor_address,
            "vendor_phone": self.vendor_phone,
            "vendor_email": self.vendor_email,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "project_name": self.project_name,
            "project_id": self.project_id,
            "expense_categories": self.expense_categories,
            "tags": self.tags,
            "confidence_score": self.confidence_score,
            "manually_verified": self.manually_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }