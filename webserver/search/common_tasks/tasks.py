# tasks.py - In your Django app
from celery import shared_task
import requests
import logging
# from source_wikipedia.models import CrawlJob,IndexJob


logger = logging.getLogger("webserver")

@shared_task
def run_index_job(index_job_id):
    """Start a new indexing job and schedule status checking"""

    from source_wikipedia.models import CrawlJob, IndexJob

    try:
        index_job = IndexJob.objects.get(id=index_job_id)
        index_job.status = "running"
        index_job.save()

        logger.info(f"Starting index job {index_job_id}")

        # Call the indexer API to start the job
        response = requests.post(
            "http://indexer:5000/index",  # Adjust hostname as needed
            json={
                "mongo_db": index_job.mongodb_db,
                "mongo_collection": index_job.mongodb_collection,
                "elastic_index": index_job.elastic_index,
                "batch_size": index_job.batch_size
            },
            timeout=30  # Timeout for initial request
        )

        # Check if the request was accepted
        if response.status_code == 200:
            data = response.json()
            indexer_job_id = data["job_id"]

            # Schedule a task to check the status
            check_index_status.apply_async(
                args=[index_job_id, indexer_job_id],
                countdown=10  # Wait 10 seconds before checking
            )

            return {"status": "started", "indexer_job_id": indexer_job_id}

        else:
            index_job.status = "failed"
            index_job.error_message = f"Failed to start indexing: HTTP {response.status_code}"
            index_job.save()
            return {"status": "failed", "error": index_job.error_message}

    except Exception as e:
        logger.exception(f"Error starting index job {index_job_id}: {str(e)}")
        try:
            index_job = IndexJob.objects.get(id=index_job_id)
            index_job.status = "failed"
            index_job.error_message = str(e)
            index_job.save()
        except:
            pass
        return {"status": "failed", "error": str(e)}


@shared_task
def check_index_status(index_job_id, indexer_job_id):
    """Check the status of an indexing job"""
    from source_wikipedia.models import CrawlJob, IndexJob
    try:
        response = requests.get(
            f"http://indexer:5000/status/{indexer_job_id}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Update the job status in our database
            index_job = IndexJob.objects.get(id=index_job_id)
            index_job.status = data["status"]
            if data.get("error"):
                index_job.error_message = data["error"]
            index_job.save()

            # If the job is still running, schedule another check
            if index_job.status in ["queued", "running"]:
                check_index_status.apply_async(
                    args=[index_job_id, indexer_job_id],
                    countdown=30  # Check again in 30 seconds
                )
        else:
            logger.error(f"Error checking index status: HTTP {response.status_code}")

    except Exception as e:
        logger.exception(f"Error checking status for index job {index_job_id}: {str(e)}")


@shared_task
def run_crawl_job(job_id):
    """Start a new crawl job and schedule status checking"""
    from source_wikipedia.models import CrawlJob, IndexJob
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
                "mongodb_collection": job.mongodb_collection,
                "mongo_db": job.mongodb_db,
                "spider_name": job.spider_name,
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
    """Check the status of a crawl job and trigger indexing when complete"""
    from source_wikipedia.models import CrawlJob, IndexJob
    try:
        response = requests.get(
            f"http://crawler:5000/status/{crawler_job_id}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Update the job status in our database
            job = CrawlJob.objects.get(id=job_id)
            previous_status = job.status
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
            # If job completed, trigger the associated index job if it exists
            elif job.status == "completed" and previous_status != "completed":

                try:

                    index_job = IndexJob.objects.get(crawl_job_id=job_id)
                    run_index_job.delay(index_job.id)
                    logger.info(f"Started indexing job {index_job.id} for completed crawl job {job_id}")

                except IndexJob.DoesNotExist:
                    logger.info(f"No index job found for crawl job {job_id}, skipping automatic indexing")

                except IndexJob.MultipleObjectsReturned:
                    logger.error(f"Multiple index jobs found for crawl job {job_id}, not sure which one to run")
                except Exception as e:
                    logger.exception(f"Error starting index job for crawl job {job_id}: {str(e)}")
        else:
            logger.error(f"Error checking crawl status: HTTP {response.status_code}")

    except Exception as e:
        logger.exception(f"Error checking status for job {job_id}: {str(e)}")
