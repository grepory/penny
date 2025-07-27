"""
Background job service using APScheduler for document processing
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.database import AsyncSessionLocal, SYNC_DATABASE_URL
from app.db.models import ProcessingJob, DocumentMetadata
from app.models.document import DocumentResponse

logger = logging.getLogger(__name__)

# Global scheduler instance (separate from service class)
scheduler = None

async def initialize_global_scheduler():
    """Initialize the global scheduler"""
    global scheduler
    if scheduler is not None and scheduler.running:
        return scheduler
    
    try:
        # Configure job store to use SQLite
        jobstores = {
            'default': SQLAlchemyJobStore(url=SYNC_DATABASE_URL)
        }
        
        # Create scheduler
        scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            job_defaults={
                'coalesce': False,
                'max_instances': 3
            }
        )
        
        # Start scheduler
        scheduler.start()
        logger.info("Global scheduler initialized successfully")
        return scheduler
        
    except Exception as e:
        logger.error(f"Failed to initialize global scheduler: {e}")
        raise

async def shutdown_global_scheduler():
    """Shutdown the global scheduler"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Global scheduler shutdown")
        scheduler = None


async def update_job_progress(job_id: str, progress: float, current_step: str, status: str = "processing"):
    """Update job progress - standalone function for serialization"""
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.id == job_id)
                .values(
                    progress=progress,
                    current_step=current_step,
                    status=status,
                    started_at=datetime.utcnow() if status == "processing" else None
                )
            )
            await session.commit()
            logger.debug(f"Updated job {job_id}: {progress}% - {current_step}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update job progress: {e}")


async def complete_job(job_id: str, success: bool, result: Dict[str, Any] = None, error_message: str = None):
    """Mark job as completed or failed - standalone function for serialization"""
    async with AsyncSessionLocal() as session:
        try:
            status = "completed" if success else "failed"
            progress = 100.0 if success else 0.0
            
            await session.execute(
                update(ProcessingJob)
                .where(ProcessingJob.id == job_id)
                .values(
                    status=status,
                    progress=progress,
                    completed_at=datetime.utcnow(),
                    result=result,
                    error_message=error_message,
                    current_step="Completed" if success else "Failed"
                )
            )
            await session.commit()
            logger.info(f"Job {job_id} {'completed' if success else 'failed'}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to complete job: {e}")


async def store_financial_metadata(document_id: str, financial_data: Dict[str, Any]):
    """Store extracted financial metadata in database - standalone function"""
    async with AsyncSessionLocal() as session:
        try:
            # Check if metadata already exists
            result = await session.execute(
                select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
            )
            existing = result.scalars().first()
            
            # Parse date if available
            invoice_date = None
            if financial_data.get('issue_date'):
                if isinstance(financial_data['issue_date'], str):
                    try:
                        invoice_date = datetime.fromisoformat(financial_data['issue_date'])
                    except:
                        pass
                elif hasattr(financial_data['issue_date'], 'date'):
                    invoice_date = datetime.combine(financial_data['issue_date'], datetime.min.time())
            
            if existing:
                # Update existing metadata
                await session.execute(
                    update(DocumentMetadata)
                    .where(DocumentMetadata.document_id == document_id)
                    .values(
                        document_type=financial_data.get('document_type'),
                        vendor_name=financial_data.get('vendor_name'),
                        total_amount=financial_data.get('total_amount'),
                        invoice_date=invoice_date,
                        project_name=financial_data.get('project_info', {}).get('project_name'),
                        expense_categories=financial_data.get('line_items', []),
                        updated_at=datetime.utcnow()
                    )
                )
            else:
                # Create new metadata record
                metadata = DocumentMetadata(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    filename=financial_data.get('filename', 'unknown'),
                    document_type=financial_data.get('document_type'),
                    vendor_name=financial_data.get('vendor_name'),
                    total_amount=financial_data.get('total_amount'),
                    invoice_date=invoice_date,
                    project_name=financial_data.get('project_info', {}).get('project_name'),
                    expense_categories=financial_data.get('line_items', [])
                )
                session.add(metadata)
            
            await session.commit()
            logger.debug(f"Stored financial metadata for document {document_id}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to store financial metadata: {e}")


async def process_document_job(job_id: str):
    """Standalone job function for processing documents - can be serialized by APScheduler"""
    try:
        logger.info(f"Starting document processing job {job_id}")
        
        # Get job details
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ProcessingJob).where(ProcessingJob.id == job_id)
            )
            job = result.scalars().first()
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
        
        # Step 1: Validate file exists
        await update_job_progress(job_id, 10.0, "Validating file")
        
        file_path = Path(job.file_path)
        if not file_path.exists():
            await complete_job(
                job_id, False, 
                error_message=f"File not found: {job.file_path}"
            )
            return
        
        # Step 2: Create DocumentResponse object
        await update_job_progress(job_id, 25.0, "Preparing document")
        
        document = DocumentResponse(
            id=job.document_id,
            filename=job.filename,
            file_path=job.file_path,
            content_type="application/pdf",  # Default, could be improved
            file_size=job.file_size,
            uploaded_at=datetime.utcnow(),
            indexed=False
        )
        
        # Step 3: Parse financial data (if available)
        financial_data = None
        try:
            from app.services.financial_parser import FinancialDocumentParser
            financial_parser = FinancialDocumentParser()
            
            await update_job_progress(job_id, 40.0, "Parsing financial data with LlamaParse")
            
            financial_data = await financial_parser.parse_document(document)
            
            # Update job with LlamaParse job ID if available
            if financial_data and financial_data.get('llamaparse_job_id'):
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(ProcessingJob)
                        .where(ProcessingJob.id == job_id)
                        .values(llamaparse_job_id=financial_data['llamaparse_job_id'])
                    )
                    await session.commit()
            
            # Store financial metadata
            if financial_data and financial_data.get('extracted_data'):
                await store_financial_metadata(job.document_id, financial_data['extracted_data'])
                
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(ProcessingJob)
                        .where(ProcessingJob.id == job_id)
                        .values(financial_data_extracted=True)
                    )
                    await session.commit()
            
        except Exception as e:
            logger.warning(f"Financial parsing failed for job {job_id}: {e}")
            # Continue with indexing even if financial parsing fails
        
        # Step 4: Index document in ChromaDB
        await update_job_progress(job_id, 75.0, "Indexing document in vector database")
        
        try:
            from app.services.document_service import DocumentService
            document_service = DocumentService()
            await document_service.index_document(document)
            
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(ProcessingJob)
                    .where(ProcessingJob.id == job_id)
                    .values(indexed_in_chroma=True)
                )
                await session.commit()
            
        except Exception as e:
            logger.error(f"Document indexing failed for job {job_id}: {e}")
            await complete_job(
                job_id, False,
                error_message=f"Document indexing failed: {str(e)}"
            )
            return
        
        # Step 5: Complete successfully
        await update_job_progress(job_id, 100.0, "Processing completed")
        
        result = {
            "document_id": job.document_id,
            "filename": job.filename,
            "financial_data_extracted": financial_data is not None,
            "indexed": True
        }
        
        await complete_job(job_id, True, result)
        logger.info(f"Document processing job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Document processing job {job_id} failed: {e}")
        await complete_job(
            job_id, False,
            error_message=f"Processing failed: {str(e)}"
        )


class JobService:
    """Service for managing background document processing jobs"""
    
    def __init__(self):
        self.document_service = None
        self.financial_parser = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the job service and scheduler"""
        if self._initialized:
            return
        
        try:
            # Initialize global scheduler
            await initialize_global_scheduler()
            
            # Initialize services
            from app.services.document_service import DocumentService
            self.document_service = DocumentService()
            
            try:
                from app.services.financial_parser import FinancialDocumentParser
                self.financial_parser = FinancialDocumentParser()
            except Exception as e:
                logger.warning(f"Financial parser not available: {e}")
                self.financial_parser = None
            
            self._initialized = True
            logger.info("Job service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize job service: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the job service"""
        await shutdown_global_scheduler()
    
    async def create_processing_job(self, document: DocumentResponse) -> str:
        """Create a new document processing job"""
        job_id = str(uuid.uuid4())
        
        async with AsyncSessionLocal() as session:
            try:
                # Create job record
                job = ProcessingJob(
                    id=job_id,
                    document_id=document.id,
                    filename=document.filename,
                    file_path=document.file_path,
                    file_size=document.file_size,
                    status="pending",
                    progress=0.0,
                    current_step="Queued for processing"
                )
                
                session.add(job)
                await session.commit()
                
                # Schedule the processing job using standalone function and global scheduler
                global scheduler
                if scheduler is None:
                    raise RuntimeError("Scheduler not initialized")
                
                scheduler.add_job(
                    process_document_job,
                    'date',  # Run once immediately
                    args=[job_id],
                    id=f"process_doc_{job_id}",
                    replace_existing=True
                )
                
                logger.info(f"Created processing job {job_id} for document {document.id}")
                return job_id
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to create processing job: {e}")
                raise
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a processing job"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(ProcessingJob).where(ProcessingJob.id == job_id)
                )
                job = result.scalars().first()
                
                if job:
                    return job.to_dict()
                return None
                
            except Exception as e:
                logger.error(f"Failed to get job status: {e}")
                return None
    
    async def get_jobs_by_status(self, status: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get jobs by status"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(ProcessingJob)
                    .where(ProcessingJob.status == status)
                    .order_by(ProcessingJob.created_at.desc())
                    .limit(limit)
                )
                jobs = result.scalars().all()
                
                return [job.to_dict() for job in jobs]
                
            except Exception as e:
                logger.error(f"Failed to get jobs by status: {e}")
                return []
    
    async def get_recent_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent processing jobs"""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(ProcessingJob)
                    .order_by(ProcessingJob.created_at.desc())
                    .limit(limit)
                )
                jobs = result.scalars().all()
                
                return [job.to_dict() for job in jobs]
                
            except Exception as e:
                logger.error(f"Failed to get recent jobs: {e}")
                return []
    


# Global job service instance
job_service = JobService()