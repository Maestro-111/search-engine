# tasks.py - In your Django app
from celery import shared_task
import requests
import logging
from .models import CrawlJob

logger = logging.getLogger("webserver")


@shared_task
def run_crawl_job(job_id):
    """Start a new crawl job and schedule status checking"""
    try:
        job = CrawlJob.objects.get(id=job_id)
        job.status = "running"
        job.save()

        logger.info(f"Starting crawl job {job_id}")

        # Call the crawler API to start the job
        response = requests.post(
            "http://crawler:5000/crawl",
            json={
                "starting_url": job.starting_url,
                "crawl_depth": job.crawl_depth,
                "max_pages": job.max_pages,
                "mongodb_collection": job.mongodb_collection
            },
            timeout=30  # Timeout for initial request
        )

        # Check if the request was accepted
        if response.status_code == 200:
            data = response.json()
            crawler_job_id = data["job_id"]

            # Schedule a task to check the status
            check_crawl_status.apply_async(
                args=[job_id, crawler_job_id],
                countdown=10  # Wait 10 seconds before checking
            )

            return {"status": "started", "crawler_job_id": crawler_job_id}
        else:
            job.status = "failed"
            job.error_message = f"Failed to start crawl: HTTP {response.status_code}"
            job.save()
            return {"status": "failed", "error": job.error_message}

    except Exception as e:
        logger.exception(f"Error starting crawl job {job_id}: {str(e)}")
        try:
            job = CrawlJob.objects.get(id=job_id)
            job.status = "failed"
            job.error_message = str(e)
            job.save()
        except:
            pass
        return {"status": "failed", "error": str(e)}


@shared_task
def check_crawl_status(job_id, crawler_job_id):
    """Check the status of a crawl job"""
    try:
        response = requests.get(
            f"http://crawler:5000/status/{crawler_job_id}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Update the job status in our database
            job = CrawlJob.objects.get(id=job_id)
            job.status = data["status"]
            if data.get("error"):
                job.error_message = data["error"]
            job.save()

            # If the job is still running, schedule another check
            if job.status in ["queued", "running"]:
                check_crawl_status.apply_async(
                    args=[job_id, crawler_job_id],
                    countdown=30  # Check again in 30 seconds
                )
        else:
            logger.error(f"Error checking crawl status: HTTP {response.status_code}")

    except Exception as e:
        logger.exception(f"Error checking status for job {job_id}: {str(e)}")

