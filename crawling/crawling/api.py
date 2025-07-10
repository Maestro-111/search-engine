import redis
from redis.exceptions import RedisError
import json
import logging
import asyncio
import uuid
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Optional
import pymongo
import psutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


class CrawlRequest(BaseModel):
    starting_url: HttpUrl
    crawl_depth: int = 1
    max_pages: int = 5
    mongo_db: str
    mongodb_collection: str
    spider_name: str

    def model_dump(self):
        return {
            "starting_url": str(self.starting_url),
            "crawl_depth": self.crawl_depth,
            "max_pages": self.max_pages,
            "mongo_db": self.mongo_db,
            "mongodb_collection": self.mongodb_collection,
            "spider_name": self.spider_name,
        }


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "queued", "running", "completed", "failed"
    error: Optional[str] = None


redis_pool = redis.ConnectionPool(host="redis", port=6379, db=0, max_connections=10)


def get_redis_client():
    try:
        return redis.Redis(connection_pool=redis_pool)
    except RedisError as e:
        logger.error(f"Redis connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")


def get_memory_usage():
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


@app.post("/crawl", response_model=JobStatusResponse)
async def start_crawl(request: CrawlRequest):

    job_id = str(uuid.uuid4())
    redis_client = get_redis_client()

    job_data = {
        "status": "queued",
        "error": None,
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "crawl_request": request.model_dump(),  # Use model_dump instead of dict
    }

    redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=7200)

    asyncio.create_task(run_crawl(job_id, request))

    # Return immediately with the job ID
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


async def heartbeat(job_id):

    while True:

        try:
            redis_client = get_redis_client()

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


async def run_crawl(job_id: str, request: CrawlRequest):

    heartbeat_task = None

    try:

        redis_client = get_redis_client()

        job_data_str = redis_client.get(f"job:{job_id}")
        job_data = json.loads(job_data_str)

        job_data["status"] = "running"
        job_data["started_at"] = datetime.datetime.now(datetime.UTC).isoformat()

        redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=7200)

        logger.info(f"Starting crawl job {job_id} with params: {request.model_dump()}")

        # Start heartbeat task
        heartbeat_task = asyncio.create_task(heartbeat(job_id))

        max_runtime = 7200  # seconds

        if (
            request.spider_name == "dota_spider"
        ):  # not really a crawl - just collect the needed info
            cmd = [
                "bash",
                "-c",
                f"cd /app/crawling && python crawling/crawl.py --mongo-db {request.mongo_db} --mongo-collection {request.mongodb_collection} --spider-name {request.spider_name}",
            ]
        else:
            cmd = [
                "bash",
                "-c",
                f"cd /app/crawling && python crawling/crawl.py --seed-url {request.starting_url} --depth-limit {request.crawl_depth} --page-limit {request.max_pages} --mongo-db "
                f"{request.mongo_db} --mongo-collection {request.mongodb_collection} --spider-name {request.spider_name}",
            ]

        logger.info(f"Starting crawl job {job_id} with command: {cmd}")
        logger.info(f"Memory usage before starting crawler: {get_memory_usage():.2f}MB")

        # Run the process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async def read_stream_chunks(stream, cb):
            buffer = b""
            while True:
                chunk = await stream.read(8192)  # Read in chunks instead of lines
                if not chunk:  # EOF
                    if buffer:  # Process any remaining data
                        try:
                            text = buffer.decode("utf-8", errors="replace")
                            if text.strip():
                                cb(text.strip())
                        except Exception as e:
                            logger.error(f"Error processing buffer: {str(e)}")
                    break

                buffer += chunk

                # Process complete lines from buffer
                try:
                    text = buffer.decode("utf-8", errors="replace")
                    if "\n" in text:
                        lines = text.split("\n")
                        # Keep the last (potentially incomplete) line in the buffer
                        for line in lines[:-1]:
                            if line.strip():
                                cb(line.strip())
                        buffer = lines[-1].encode("utf-8")
                    else:
                        # If no newlines but buffer is getting large, process it anyway
                        if len(buffer) > 65536:  # 64KB
                            cb(text.strip())
                            buffer = b""
                except Exception as e:
                    logger.error(f"Error processing chunk: {str(e)}")
                    buffer = b""  # Reset buffer on error

        # Run with timeout
        try:
            # Run stdout/stderr readers and process waiter with timeout
            await asyncio.wait_for(
                asyncio.gather(
                    read_stream_chunks(
                        process.stdout, lambda x: logger.info(f"Crawler stdout: {x}")
                    ),
                    read_stream_chunks(
                        process.stderr, lambda x: logger.warning(f"Crawler stderr: {x}")
                    ),
                    process.wait(),
                ),
                timeout=max_runtime,
            )

            exit_code = process.returncode
            logger.info(f"Crawler process exited with code: {exit_code}")

            try:
                mongo_uri = "mongodb://root:example@mongodb:27017/"
                client = pymongo.MongoClient(mongo_uri)
                db = client[request.mongo_db]
                collections = db.list_collection_names()
                logger.info(f"Available MongoDB collections: {collections}")

                if request.mongodb_collection in collections:
                    count = db[request.mongodb_collection].count_documents({})
                    logger.info(
                        f"Collection {request.mongodb_collection} contains {count} documents"
                    )
                else:
                    logger.warning(
                        f"Collection {request.mongodb_collection} was not created"
                    )
            except Exception as e:
                logger.error(f"Error checking MongoDB: {str(e)}")

            job_data_str = redis_client.get(f"job:{job_id}")
            job_data = json.loads(job_data_str)

            if exit_code == 0:
                logger.info(f"Crawl job {job_id} completed successfully")
                job_data["status"] = "completed"
            else:
                logger.error(f"Crawl job {job_id} failed with exit code {exit_code}")
                job_data["status"] = "failed"
                job_data["error"] = f"Process exited with code {exit_code}"

            job_data["finished_at"] = datetime.datetime.now(datetime.UTC).isoformat()
            redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=7200)

        except asyncio.TimeoutError:
            # Kill the process if it times out
            logger.error(f"Crawl job {job_id} timed out after {max_runtime} seconds")
            process.kill()

            job_data_str = redis_client.get(f"job:{job_id}")
            job_data = json.loads(job_data_str)
            job_data["status"] = "failed"
            job_data["error"] = f"Job timed out after {max_runtime} seconds"
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


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer."""
    return {"status": "healthy"}


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
