from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import redis
from redis.exceptions import RedisError
import uuid
from typing import Optional
import logging
import datetime
import json
import psutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

redis_pool = redis.ConnectionPool(host="redis", port=6379, db=0, max_connections=10)


def get_redis_client():
    try:
        return redis.Redis(connection_pool=redis_pool)
    except RedisError as e:
        logger.error(f"Redis connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")


class IndexRequest(BaseModel):
    mongo_db: str
    mongo_collection: str
    elastic_index: str
    batch_size: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "queued", "running", "completed", "failed"
    error: Optional[str] = None


@app.post("/index", response_model=JobStatusResponse)
async def start_indexer(request: IndexRequest):
    """
    start indexer job, return json response immediately
    """

    job_id = str(uuid.uuid4())
    redis_client = get_redis_client()

    job_data = {
        "status": "queued",
        "error": None,
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=7200)
    asyncio.create_task(run_indexer(job_id, request))

    return JobStatusResponse(job_id=job_id, status="queued")


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):

    redis_client = get_redis_client()
    job_data_str = redis_client.get(f"job:{job_id}")

    if not job_data_str:
        logger.error(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = json.loads(job_data_str)
    logger.info(f"Job {job_id} status: {job_data['status']}")

    return JobStatusResponse(
        job_id=job_id, status=job_data["status"], error=job_data["error"]
    )


def get_memory_usage():
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


async def heartbeat(job_id):

    redis_client = get_redis_client()

    while True:
        try:
            current_memory = get_memory_usage()
            job_data_str = redis_client.get(f"job:{job_id}")
            if job_data_str:
                job_data = json.loads(job_data_str)
                job_data["last_heartbeat"] = datetime.datetime.now(
                    datetime.UTC
                ).isoformat()
                job_data["memory_usage_mb"] = current_memory
                redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=7200)
                logger.debug(
                    f"Heartbeat for job {job_id}: Memory usage {current_memory:.2f}MB"
                )
        except Exception as e:
            logger.error(f"Error in heartbeat for job {job_id}: {str(e)}")
        await asyncio.sleep(30)


async def run_indexer(job_id: str, request: IndexRequest):

    heartbeat_task = None

    try:

        redis_client = get_redis_client()

        job_data_str = redis_client.get(f"job:{job_id}")
        job_data = json.loads(job_data_str)

        job_data["status"] = "running"
        job_data["started_at"] = datetime.datetime.now(datetime.UTC).isoformat()

        redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=7200)

        logger.info(f"Starting crawl job {job_id} with params: {request.model_dump()}")

        heartbeat_task = asyncio.create_task(heartbeat(job_id))

        cmd = [
            "bash",
            "-c",
            f"cd /app/indexer && python mongo_to_elastic.py --mongo-db {request.mongo_db} --mongo-collection {request.mongo_collection} --elastic-index {request.elastic_index} --batch-size {request.batch_size}",
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()
        stdout_text = stdout.decode()
        stderr_text = stderr.decode()

        logger.info(f"Indexer stdout: {stdout_text}")
        if stderr_text:
            logger.warning(f"Indexer stderr: {stderr_text}")

        job_data_str = redis_client.get(f"job:{job_id}")
        job_data = json.loads(job_data_str)

        if process.returncode == 0:
            logger.info(f"Index job {job_id} completed successfully")
            job_data["status"] = "completed"
        else:
            logger.error(f"Index job {job_id} failed: {stderr_text}")
            job_data["status"] = "failed"
            job_data["error"] = stderr_text

        job_data["finished_at"] = datetime.datetime.now(datetime.UTC).isoformat()
        redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=7200)

    except Exception as e:

        logger.exception(f"Error in crawl job {job_id}: {str(e)}")

        try:
            job_data_str = redis_client.get(f"job:{job_id}")
            job_data = json.loads(job_data_str)
            job_data["status"] = "failed"
            job_data["error"] = str(e)
            job_data["finished_at"] = datetime.datetime.now(datetime.UTC).isoformat()
            redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=7200)

        except Exception as redis_error:
            logger.error(f"Failed to update Redis after error: {str(redis_error)}")

    finally:

        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
