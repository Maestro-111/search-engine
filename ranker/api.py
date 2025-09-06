from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from celery_app import celery_app
from tasks import run_ranker_fit_task, run_ranker_predict_task
import uvicorn
import redis
from redis.exceptions import RedisError
from ranker_logging import logger

app = FastAPI()


class RankerFitRequest(BaseModel):
    pass


class RankerPredictRequest(BaseModel):
    user_persona: str
    user_expertise: str
    query: str
    documents: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "PENDING", "PROGRESS", "SUCCESS", "FAILURE"
    result: Optional[dict] = None
    error: Optional[str] = None


redis_pool = redis.ConnectionPool(host="redis", port=6379, db=0, max_connections=10)


def get_redis_client():
    try:
        return redis.Redis(connection_pool=redis_pool)
    except RedisError as e:
        logger.error(f"Redis connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection error")


@app.post("/start_ranker_fit", response_model=JobStatusResponse)
async def start_ranker_fit(request: RankerFitRequest):
    """Start a ranking fit job using Celery"""

    # Submit task to Celery
    task = run_ranker_fit_task.apply_async(
        args=[request.dict()], task_id=str(uuid.uuid4())  # Custom task ID
    )

    return JobStatusResponse(job_id=task.id, status=task.state)


@app.post("/start_ranker_predict", response_model=JobStatusResponse)
async def start_ranker_predict(request: RankerPredictRequest):
    """Start a ranking predict job using Celery"""

    # Submit task to Celery
    task = run_ranker_predict_task.apply_async(
        args=[request.model_dump()], task_id=str(uuid.uuid4())  # Custom task ID
    )

    return JobStatusResponse(job_id=task.id, status=task.state)


@app.get("/job_result/{job_id}")
async def get_job_result(job_id: str):
    """Get the result of a completed ranking job"""

    # Get task result from Celery
    from celery.result import AsyncResult

    task = AsyncResult(job_id, app=celery_app)

    if task.state == "SUCCESS":
        result = (
            task.result
        )  # JSON response (FastAPI automatically serializes the dict)
        return {"status": "completed", "result": result}
    elif task.state == "FAILURE":
        return {"status": "failed", "error": str(task.info)}
    else:
        return {"status": task.state, "message": "Job still processing"}


@app.get("/job_status/{job_id}")
async def get_job_status(job_id: str):
    """Check the status of a ranking job"""
    from celery.result import AsyncResult

    task = AsyncResult(job_id, app=celery_app)

    return {
        "job_id": job_id,
        "status": task.state,
        "current": task.info.get("current", 0) if task.info else 0,
        "total": task.info.get("total", 100) if task.info else 100,
    }


@app.delete("/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    celery_app.control.revoke(job_id, terminate=True)
    return {"message": f"Job {job_id} cancelled"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
