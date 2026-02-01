from typing import Optional
import asyncio
import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from redis import Redis, RedisError
from rq import Queue
from rq.job import Job, NoSuchJobError
from rq.exceptions import InvalidJobOperation
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables (12-factor app)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
JOB_TIMEOUT = int(os.getenv('JOB_TIMEOUT', 600))  # 10 minutes default

# Set up FastAPI with metadata
app = FastAPI(
    title="Due Diligence API",
    description="Async multi-agent due diligence analysis",
    version="1.0.0"
)

# CORS middleware for production (configure allowed origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection with error handling
try:
    redis_conn = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=False,  # RQ needs bytes
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    redis_conn.ping()  # Test connection
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except RedisError as e:
    logger.error(f"Failed to connect to Redis: {e}")
    raise

agent_tasks = Queue('agents', connection=redis_conn)

# Request/Response models
class AnalysisRequest(BaseModel):
    startup_name: str = Field(..., min_length=1, max_length=200, description="Name of the startup")
    startup_description: str = Field(..., min_length=10, max_length=5000, description="Description of the startup")
    funding_stage: Optional[str] = Field(None, description="Funding stage (seed, series-a, etc.)")

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    job_id: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued, started, finished, failed
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: Optional[dict] = None


# Worker function (runs in RQ worker process)
def run_agent_pipeline(
    startup_name: str,
    description: str,
    funding_stage: Optional[str] = None
):
    """
    Worker function that runs the due diligence workflow.
    Import happens here to avoid loading heavy dependencies before fork().
    """
    try:
        # Lazy import to prevent macOS fork issues
        from .workflow import run_due_diligence
        
        logger.info(f"Starting due diligence for: {startup_name}")
        result = asyncio.run(
            run_due_diligence(startup_name, description, funding_stage)
        )
        logger.info(f"Completed due diligence for: {startup_name}")
        return result
    except Exception as e:
        logger.error(f"Failed due diligence for {startup_name}: {e}", exc_info=True)
        raise


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint for load balancers/monitoring"""
    try:
        redis_conn.ping()
        redis_healthy = True
    except RedisError:
        redis_healthy = False
    
    return {
        "status": "healthy" if redis_healthy else "degraded",
        "redis": "connected" if redis_healthy else "disconnected",
        "queue_size": len(agent_tasks) if redis_healthy else None
    }


# Submit analysis job
@app.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_analysis(request: AnalysisRequest):
    """
    Submit a due diligence analysis job.
    Returns immediately with a job_id that can be used to check status.
    """
    try:
        job = agent_tasks.enqueue(
            run_agent_pipeline,
            request.startup_name,
            request.startup_description,
            request.funding_stage,
            job_timeout=JOB_TIMEOUT,  # Job will be killed if it takes longer
            result_ttl=86400,  # Keep results for 24 hours
            failure_ttl=86400  # Keep failures for 24 hours for debugging
        )
        
        logger.info(f"Enqueued job {job.id} for {request.startup_name}")
        
        return AnalysisResponse(
            success=True,
            message="Analysis job submitted. Check status at /analyze/status/{job_id}",
            job_id=job.id
        )
    except RedisError as e:
        logger.error(f"Redis error while enqueuing: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue service temporarily unavailable"
        )


# Check job status
@app.get("/analyze/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """
    Check the status of a submitted analysis job.
    Returns job status, result (if complete), or error (if failed).
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        response = JobStatusResponse(
            job_id=job_id,
            status=job.get_status(),
            result=None,
            error=None
        )
        
        # Add result if job finished successfully
        if job.is_finished:
            response.result = job.result
        
        # Add error if job failed
        elif job.is_failed:
            response.error = str(job.exc_info) if job.exc_info else "Job failed with unknown error"
        
        # Add progress info for running jobs
        elif job.is_started:
            response.progress = {
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "message": "Analysis in progress..."
            }
        
        return response
        
    except NoSuchJobError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found. It may have expired (jobs expire after 24 hours)."
        )
    except (RedisError, InvalidJobOperation) as e:
        logger.error(f"Error fetching job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue service temporarily unavailable"
        )


# Cancel a job (optional but useful)
@app.delete("/analyze/{job_id}")
def cancel_job(job_id: str):
    """Cancel a running or queued job"""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        if job.is_finished:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel completed job"
            )
        
        job.cancel()
        logger.info(f"Cancelled job {job_id}")
        
        return {"success": True, "message": f"Job {job_id} cancelled"}
        
    except NoSuchJobError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )


# List recent jobs (useful for debugging/monitoring)
@app.get("/analyze/jobs/recent")
def list_recent_jobs(limit: int = 10):
    """List recent jobs (for monitoring/debugging)"""
    try:
        jobs = agent_tasks.jobs[:limit]
        return {
            "queue_length": len(agent_tasks),
            "recent_jobs": [
                {
                    "job_id": job.id,
                    "status": job.get_status(),
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                }
                for job in jobs
            ]
        }
    except RedisError as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue service temporarily unavailable"
        )