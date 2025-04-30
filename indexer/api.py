
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import asyncio
import subprocess
import uuid
from typing import Optional, Dict, List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# In-memory storage for job status (in production, use a database)
jobs_status = {}


class IndexRequest(BaseModel):
    mongo_db : str
    mongo_collection : str
    elastic_index : str
    batch_size : int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "queued", "running", "completed", "failed"
    error: Optional[str] = None


@app.post("/index", response_model=JobStatusResponse)
async def start_indexer(request: IndexRequest):
    # Generate a unique job ID
    job_id = str(uuid.uuid4())

    # Store initial job status
    jobs_status[job_id] = {
        "status": "queued",
        "error": None
    }

    # Start the crawl process in the background
    asyncio.create_task(run_indexer(job_id, request))

    # Return immediately with the job ID
    return JobStatusResponse(
        job_id=job_id,
        status="queued"
    )


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):
    if job_id not in jobs_status:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job_id,
        status=jobs_status[job_id]["status"],
        error=jobs_status[job_id]["error"]
    )


# Add to your run_crawl function in api.py
async def run_indexer(job_id: str, request: IndexRequest):
    try:

        jobs_status[job_id]["status"] = "running"

        cmd = [
            "bash", "-c",
            f"cd /app/indexer && python mongo_to_elastic.py --mongo-db {request.mongo_db} --mongo-collection {request.mongo_collection} --elastic-index {request.elastic_index} --batch-size {request.batch_size}"
        ]

        logger.info(f"Starting indexer job {job_id} with command: {cmd}")

        # Run the process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()
        stdout_text = stdout.decode()
        stderr_text = stderr.decode()

        # Log the output for debugging
        logger.info(f"Indexer stdout: {stdout_text}")
        if stderr_text:
            logger.warning(f"Indexer stderr: {stderr_text}")


        if process.returncode == 0:
            logger.info(f"Index job {job_id} completed successfully")
            jobs_status[job_id]["status"] = "completed"
        else:
            logger.error(f"Index job {job_id} failed: {stderr_text}")
            jobs_status[job_id]["status"] = "failed"
            jobs_status[job_id]["error"] = stderr_text

    except Exception as e:
        logger.exception(f"Error in Index job {job_id}: {str(e)}")
        jobs_status[job_id]["status"] = "failed"
        jobs_status[job_id]["error"] = str(e)


@app.get("/jobs", response_model=List[JobStatusResponse])
async def list_jobs():
    return [
        JobStatusResponse(job_id=id, status=info["status"], error=info["error"])
        for id, info in jobs_status.items()
    ]


if __name__ == "__main__":

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)