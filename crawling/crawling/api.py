# api.py - Place this in your crawler container
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


class CrawlRequest(BaseModel):

    starting_url: HttpUrl
    crawl_depth: int = 1
    max_pages: int = 5
    mongo_db: str
    mongodb_collection: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "queued", "running", "completed", "failed"
    error: Optional[str] = None


@app.post("/crawl", response_model=JobStatusResponse)
async def start_crawl(request: CrawlRequest):
    # Generate a unique job ID
    job_id = str(uuid.uuid4())

    # Store initial job status
    jobs_status[job_id] = {
        "status": "queued",
        "error": None
    }

    # Start the crawl process in the background
    asyncio.create_task(run_crawl(job_id, request))

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
async def run_crawl(job_id: str, request: CrawlRequest):
    try:
        # Update status to running
        jobs_status[job_id]["status"] = "running"

        # Build the command to run crawl.py
        # cmd = [
        #     "python",
        #     "-m", "crawling.crawling.crawl",  # Full module path
        #     "--seed-url", str(request.starting_url),
        #     "--depth-limit", str(request.crawl_depth),
        #     "--page-limit", str(request.max_pages),
        #     "--mongo-collection", request.mongodb_collection
        # ]

        cmd = [
            "bash", "-c",
            f"cd /app/crawling && python crawling/crawl.py --seed-url {request.starting_url} --depth-limit {request.crawl_depth} --page-limit {request.max_pages} --mongo-db {request.mongo_db} --mongo-collection {request.mongodb_collection}"
        ]

        logger.info(f"Starting crawl job {job_id} with command: {cmd}")

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
        logger.info(f"Crawler stdout: {stdout_text}")
        if stderr_text:
            logger.warning(f"Crawler stderr: {stderr_text}")

        # Check MongoDB for the collection
        import pymongo
        try:
            mongo_uri = "mongodb://root:example@mongodb:27017/"
            client = pymongo.MongoClient(mongo_uri)
            db = client["wikipedia_db"]
            collections = db.list_collection_names()
            logger.info(f"Available MongoDB collections: {collections}")

            if request.mongodb_collection in collections:
                count = db[request.mongodb_collection].count_documents({})
                logger.info(f"Collection {request.mongodb_collection} contains {count} documents")
            else:
                logger.warning(f"Collection {request.mongodb_collection} was not created")
        except Exception as e:
            logger.error(f"Error checking MongoDB: {str(e)}")

        # Check if successful
        if process.returncode == 0:
            logger.info(f"Crawl job {job_id} completed successfully")
            jobs_status[job_id]["status"] = "completed"
        else:
            logger.error(f"Crawl job {job_id} failed: {stderr_text}")
            jobs_status[job_id]["status"] = "failed"
            jobs_status[job_id]["error"] = stderr_text

    except Exception as e:
        logger.exception(f"Error in crawl job {job_id}: {str(e)}")
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