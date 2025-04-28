# tasks.py in your Django app
from celery import shared_task
import subprocess
import logging
from .models import CrawlJob
import docker

logger = logging.getLogger("webserver")


@shared_task
def run_crawl_job(job_id):
    try:
        job = CrawlJob.objects.get(id=job_id)
        job.status = "running"
        job.save()

        logger.info(f"Starting crawl job {job_id}")
        client = docker.from_env()

        # Execute the command directly in the crawler container with the full path
        container = client.containers.get('crawler')

        # This is the exact path to your crawl.py file based on your container exploration
        command = [
            "python",
            "/app/crawling/crawling/crawl.py",
            "--seed-url", job.starting_url,
            "--depth-limit", str(job.crawl_depth),
            "--page-limit", str(job.max_pages),
            "--mongo-collection", job.mongodb_collection
        ]

        logger.info(f"Running command: {command}")
        # Pass the command as a list of arguments, not a string
        result = container.exec_run(command)

        output = result.output.decode()
        logger.info(f"Command output: {output}")
        logger.info(f"Exit code: {result.exit_code}")

        # Check result
        if result.exit_code == 0:
            job.status = "completed"
            job.save()
        else:
            job.status = "failed"
            job.error_message = output
            job.save()

    except Exception as e:
        logger.exception(f"Error in crawl job {job_id}: {str(e)}")
        # Update job status
        try:
            job = CrawlJob.objects.get(id=job_id)
            job.status = "failed"
            job.error_message = str(e)
            job.save()
        except:
            pass