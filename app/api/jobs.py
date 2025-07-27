"""
API endpoints for job tracking and progress monitoring
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.job_service import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status and progress of a specific job
    """
    try:
        # Initialize job service if needed
        if not job_service._initialized:
            await job_service.initialize()
        
        job_status = await job_service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return job_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job status: {str(e)}")


@router.get("/status")
async def get_jobs_by_status(
    status: str = Query(..., description="Job status: pending, processing, completed, failed"),
    limit: int = Query(50, description="Maximum number of jobs to return")
):
    """
    Get jobs by status
    """
    try:
        # Initialize job service if needed
        if not job_service._initialized:
            await job_service.initialize()
        
        # Validate status
        valid_statuses = ["pending", "processing", "completed", "failed"]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )
        
        jobs = await job_service.get_jobs_by_status(status, limit)
        
        return {
            "status": status,
            "count": len(jobs),
            "jobs": jobs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting jobs: {str(e)}")


@router.get("/recent")
async def get_recent_jobs(limit: int = Query(20, description="Maximum number of jobs to return")):
    """
    Get recent processing jobs
    """
    try:
        # Initialize job service if needed
        if not job_service._initialized:
            await job_service.initialize()
        
        jobs = await job_service.get_recent_jobs(limit)
        
        return {
            "count": len(jobs),
            "jobs": jobs
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recent jobs: {str(e)}")


@router.get("/stats")
async def get_job_stats():
    """
    Get job processing statistics
    """
    try:
        # Initialize job service if needed
        if not job_service._initialized:
            await job_service.initialize()
        
        # Get counts by status
        stats = {}
        for status in ["pending", "processing", "completed", "failed"]:
            jobs = await job_service.get_jobs_by_status(status, 1000)  # Get all
            stats[status] = len(jobs)
        
        return {
            "total_jobs": sum(stats.values()),
            "by_status": stats,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job stats: {str(e)}")


@router.get("/progress/{job_id}")
async def get_job_progress(job_id: str):
    """
    Get simplified progress information for a job (for polling)
    """
    try:
        # Initialize job service if needed
        if not job_service._initialized:
            await job_service.initialize()
        
        job_status = await job_service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        # Return simplified progress info
        return {
            "job_id": job_id,
            "status": job_status["status"],
            "progress": job_status["progress"],
            "current_step": job_status["current_step"],
            "error_message": job_status.get("error_message"),
            "completed": job_status["status"] in ["completed", "failed"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job progress: {str(e)}")


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a pending or processing job
    Note: This is a placeholder - actual job cancellation would require 
    more sophisticated implementation with APScheduler
    """
    try:
        # Initialize job service if needed
        if not job_service._initialized:
            await job_service.initialize()
        
        job_status = await job_service.get_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        if job_status["status"] in ["completed", "failed"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel job in status: {job_status['status']}"
            )
        
        # TODO: Implement actual job cancellation with APScheduler
        # For now, just return a message
        return {
            "message": f"Job cancellation requested for {job_id}",
            "note": "Job cancellation is not fully implemented yet"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error canceling job: {str(e)}")