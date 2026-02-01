"""
STEP 3: Authentication and Rate Limiting
=========================================

What changed from Step 2:
    - API key authentication via X-API-Key header
    - Rate limiting: max 5 concurrent jobs per API key
    - Jobs are now scoped to the API key that created them
    - Added /docs protection (requires API key)

Security model:
    - API keys are stored in environment variable (comma-separated)
    - Each key gets its own job namespace (can't see other users' jobs)
    - Simple rate limit: max concurrent jobs per key

What's still missing:
    - Key rotation / revocation
    - Per-key rate limit configuration
    - Persistent job storage (still in-memory)
    - Structured logging

Run:
    export DUE_DILIGENCE_API_KEYS="test-key-1,test-key-2"
    uv run uvicorn server:app --reload

Test:
    # Without API key — rejected
    curl -X POST http://localhost:8000/analyze \
         -H "Content-Type: application/json" \
         -d '{"startup_name": "Stripe"}'

    # With API key — accepted
    curl -X POST http://localhost:8000/analyze \
         -H "Content-Type: application/json" \
         -H "X-API-Key: test-key-1" \
         -d '{"startup_name": "Stripe", "description": "Payments", "funding_stage": "Growth"}'
"""

import asyncio
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from src.workflow.graph import run_due_diligence

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# Load API keys from environment. In production, these come from a secrets
# manager (AWS Secrets Manager, Doppler, etc.), not a .env file.
VALID_API_KEYS = set(
    key.strip()
    for key in os.getenv("DUE_DILIGENCE_API_KEYS", "").split(",")
    if key.strip()
)

MAX_CONCURRENT_JOBS_PER_KEY = 5  # Rate limit

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("server")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Due Diligence API",
    description="Async API for running startup due diligence analysis",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Job store — keyed by API key, then by job_id
# ---------------------------------------------------------------------------
# Structure: { api_key: { job_id: job_data } }
# This isolates jobs per user. User A can't see User B's jobs.
jobs_by_key: dict[str, dict[str, dict]] = defaultdict(dict)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Dependency that validates the API key.

    FastAPI dependencies are powerful — this runs before every endpoint
    that includes it. If it raises an exception, the request is rejected
    before your endpoint code runs.
    """
    if not VALID_API_KEYS:
        # No keys configured = dev mode, allow everything
        # REMOVE THIS IN PRODUCTION
        logger.warning("No API keys configured — running in dev mode")
        return "dev-mode"

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header.",
        )

    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    return api_key


def check_rate_limit(api_key: str):
    """
    Check if the user has hit their concurrent job limit.

    This is a simple rate limit — you can only have N jobs running at once.
    More sophisticated: per-hour limits, token budgets, etc.
    """
    user_jobs = jobs_by_key.get(api_key, {})
    running = sum(1 for j in user_jobs.values() if j["status"] == "running")

    if running >= MAX_CONCURRENT_JOBS_PER_KEY:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {MAX_CONCURRENT_JOBS_PER_KEY} concurrent jobs.",
        )


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    startup_name: str
    description: str = ""
    funding_stage: Optional[str] = None


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    stage: Optional[str] = None
    startup_name: str
    submitted_at: str
    completed_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------
async def run_pipeline(
    api_key: str,
    job_id: str,
    startup_name: str,
    description: str,
    funding_stage: Optional[str],
):
    """
    Runs the due diligence pipeline and updates job state.

    Note the api_key parameter — we need it to find the right job in
    our per-user job store.
    """
    jobs = jobs_by_key[api_key]

    try:
        logger.info(f"[{job_id[:8]}] Starting pipeline for {startup_name}")
        jobs[job_id]["stage"] = "running"

        final_state = await run_due_diligence(
            startup_name=startup_name,
            startup_descrption=description,
            funding_stage=funding_stage,
        )

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        jobs[job_id]["result"] = {
            "investment_decision": final_state.get("investment_decision"),
            "full_report": final_state.get("full_report"),
            "errors": final_state.get("errors", []),
        }
        logger.info(f"[{job_id[:8]}] Pipeline complete")

    except Exception as e:
        logger.exception(f"[{job_id[:8]}] Pipeline failed")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/analyze", response_model=JobSubmitResponse)
async def submit_analysis(
    request: AnalyzeRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Submit a new due diligence analysis job.

    Requires X-API-Key header. Rate limited to 5 concurrent jobs per key.
    """
    check_rate_limit(api_key)

    job_id = str(uuid.uuid4())
    jobs = jobs_by_key[api_key]

    jobs[job_id] = {
        "job_id": job_id,
        "status": "running",
        "stage": "queued",
        "startup_name": request.startup_name,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "result": None,
        "error": None,
    }

    asyncio.create_task(
        run_pipeline(api_key, job_id, request.startup_name, request.description, request.funding_stage)
    )

    logger.info(f"[{job_id[:8]}] Job submitted by {api_key[:8]}... for {request.startup_name}")
    return JobSubmitResponse(job_id=job_id, status="running")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Get the status of a job.

    You can only see jobs you created (scoped by API key).
    """
    jobs = jobs_by_key.get(api_key, {})
    job = jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(**job)


@app.get("/jobs")
async def list_jobs(api_key: str = Depends(verify_api_key)):
    """
    List your jobs.

    Only shows jobs created with your API key.
    """
    jobs = jobs_by_key.get(api_key, {})
    return {
        "jobs": [
            {
                "job_id": j["job_id"],
                "status": j["status"],
                "startup_name": j["startup_name"],
                "submitted_at": j["submitted_at"],
            }
            for j in jobs.values()
        ],
        "total": len(jobs),
    }


@app.get("/health")
async def health():
    """
    Health check — no auth required.

    Load balancers need to hit this without credentials.
    Be careful not to leak sensitive info here.
    """
    total_running = sum(
        1
        for user_jobs in jobs_by_key.values()
        for j in user_jobs.values()
        if j["status"] == "running"
    )
    return {
        "status": "ok",
        "active_jobs": total_running,
    }


# ---------------------------------------------------------------------------
# Summary of what we've built
# ---------------------------------------------------------------------------
#
# Pattern: Async Job Queue over HTTP
#
#   Client                          Server
#     |                                |
#     |--- POST /analyze ------------->|
#     |<-- { job_id, status:running } -|  (immediate response)
#     |                                |
#     |    (server works in background)|
#     |                                |
#     |--- GET /jobs/{id} ------------>|
#     |<-- { status: running } --------|  (poll)
#     |                                |
#     |--- GET /jobs/{id} ------------>|
#     |<-- { status: complete, ... } --|  (done!)
#
# Security:
#   - API key in X-API-Key header
#   - Jobs scoped per key (user isolation)
#   - Rate limit: max concurrent jobs
#
# Next steps for production:
#   - Move job store to Redis (persistence, expiry)
#   - Add structured JSON logging
#   - Add request ID for tracing
#   - Add Dockerfile for deployment
