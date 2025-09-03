from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import uuid
from celery_app import celery_app
from tasks import run_ranker_fit_task, run_ranker_predict_task
import uvicorn

app = FastAPI()


class RankerFitRequest(BaseModel):
    pass


class RankerPredictRequest(BaseModel):
    user_persona: str
    user_expertise: str
    query: str
    document: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # "PENDING", "PROGRESS", "SUCCESS", "FAILURE"
    result: Optional[dict] = None
    error: Optional[str] = None


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


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of a ranker job"""

    task = celery_app.AsyncResult(job_id)

    if task.state == "PENDING":
        response = {
            "job_id": job_id,
            "status": task.state,
            "result": None,
            "error": None,
        }
    elif task.state == "PROGRESS":
        response = {
            "job_id": job_id,
            "status": task.state,
            "result": task.info,  # Progress info
            "error": None,
        }
    elif task.state == "SUCCESS":
        response = {
            "job_id": job_id,
            "status": task.state,
            "result": task.result,
            "error": None,
        }
    else:  # FAILURE
        response = {
            "job_id": job_id,
            "status": task.state,
            "result": None,
            "error": str(task.info),  # Error message
        }

    return JobStatusResponse(**response)


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
