
from celery import Celery
import subprocess
import os

# Configure Celery
app = Celery('crawler')
app.config_from_object('celeryconfig')


@app.task(bind=True)
def run_crawl_job(self, job_id, params):
    """Run the crawl job as a Celery task with proper error handling"""
    try:
        # Update status to running (you'll need a database or Redis to store job statuses)
        update_job_status(job_id, "running")

        # Build command
        cmd = [
            'python', 'crawl.py',
            '--seed-url', params['starting_url'],
            '--depth-limit', str(params['crawl_depth']),
            '--page-limit', str(params['max_pages']),
            '--mongo-collection', params['mongodb_collection']
        ]

        # Run process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = process.communicate()

        # Check if successful
        if process.returncode == 0:
            update_job_status(job_id, "completed", stdout=stdout.decode())
            return {"status": "completed", "job_id": job_id}
        else:
            update_job_status(job_id, "failed", error=stderr.decode())
            return {"status": "failed", "job_id": job_id, "error": stderr.decode()}
    except Exception as e:
        # Handle any exceptions
        update_job_status(job_id, "failed", error=str(e))
        return {"status": "failed", "job_id": job_id, "error": str(e)}