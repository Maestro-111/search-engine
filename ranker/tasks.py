import datetime
from celery_app import celery_app
from ranker_logging import logger
import subprocess
import psutil
import json


@celery_app.task(bind=True, name="ranker.tasks.run_ranker_predict_task")
def run_ranker_predict_task(self, ranker_predict_request_data):
    heartbeat_task_id = None

    # Extract parameters
    user_persona = ranker_predict_request_data["user_persona"]
    user_expertise = ranker_predict_request_data["user_expertise"]
    query = ranker_predict_request_data["query"]
    document = ranker_predict_request_data["document"]

    try:
        self.update_state(state="PROGRESS", meta={"status": "starting", "progress": 0})

        logger.info(
            f"Starting ranker predict {self.request.id} with params: {ranker_predict_request_data}"
        )
        logger.info(
            f"Attempting to schedule heartbeat task for main task {self.request.id}"
        )

        # Schedule heartbeat
        heartbeat_task_id = heartbeat_task.apply_async(
            args=[self.request.id], countdown=10
        )

        logger.info(f"Heartbeat task scheduled with ID: {heartbeat_task_id.id}")

        cmd = [
            "python",
            "/app/ranker/rank_predict.py",
            "--user_persona",
            user_persona,
            "--user_expertise",
            user_expertise,
            "--query",
            query,
            "--document",
            document,
            "--output_format",
            "json",  # Important: get structured output
        ]

        self.update_state(state="PROGRESS", meta={"status": "running", "progress": 25})

        logger.info(f"Starting subprocess for task {self.request.id}")
        logger.info(f"Command: {cmd}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200,
            cwd="/app/ranker",  # Set working directory
        )

        logger.info(
            f"Subprocess completed for task {self.request.id}, exit code: {result.returncode}"
        )

        self.update_state(
            state="PROGRESS", meta={"status": "finishing", "progress": 75}
        )

        # Stop heartbeat task
        if heartbeat_task_id:
            logger.info(f"Revoking heartbeat task {heartbeat_task_id.id}")
            celery_app.control.revoke(heartbeat_task_id.id, terminate=True)
            logger.info(f"Heartbeat task {heartbeat_task_id.id} revoked")

        if result.returncode == 0:
            # Parse JSON output
            try:
                prediction_result = json.loads(result.stdout)
                return {
                    "status": "completed",
                    "exit_code": result.returncode,
                    "score": prediction_result.get("score"),
                    "features": prediction_result.get("features"),
                    "finished_at": datetime.datetime.now(datetime.UTC).isoformat(),
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "status": "completed",
                    "exit_code": result.returncode,
                    "stdout": result.stdout[-1000:],
                    "finished_at": datetime.datetime.now(datetime.UTC).isoformat(),
                }
        else:
            raise Exception(
                f"Ranker predict failed with exit code {result.returncode}: {result.stderr}"
            )

    except subprocess.TimeoutExpired:
        if heartbeat_task_id:
            celery_app.control.revoke(heartbeat_task_id.id, terminate=True)
        raise Exception("Ranker predict process timed out after 2 hours")
    except Exception as e:
        if heartbeat_task_id:
            celery_app.control.revoke(heartbeat_task_id.id, terminate=True)
        logger.exception(f"Error in Ranker predict task: {str(e)}")
        raise


@celery_app.task(bind=True, name="ranker.tasks.run_ranker_fit_task")
def run_ranker_fit_task(self, ranker_fit_request_data):
    heartbeat_task_id = None
    try:
        self.update_state(state="PROGRESS", meta={"status": "starting", "progress": 0})

        logger.info(
            f"Starting ranker fit task {self.request.id} with params: {ranker_fit_request_data}"
        )

        # Start heartbeat task with detailed logging
        logger.info(
            f"Attempting to schedule heartbeat task for main task {self.request.id}"
        )

        heartbeat_task_id = heartbeat_task.apply_async(
            args=[self.request.id], countdown=10
        )

        logger.info(
            f"Heartbeat task scheduled with ID: {heartbeat_task_id.id}, state: {heartbeat_task_id.state}"
        )

        cmd = ["bash", "-c", f"cd /app/ranker && python pipeline.py"]

        self.update_state(state="PROGRESS", meta={"status": "running", "progress": 25})

        logger.info(f"Starting subprocess for task {self.request.id}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)

        logger.info(
            f"Subprocess completed for task {self.request.id}, exit code: {result.returncode}"
        )

        self.update_state(
            state="PROGRESS", meta={"status": "finishing", "progress": 75}
        )

        # Stop heartbeat task
        if heartbeat_task_id:
            logger.info(f"Revoking heartbeat task {heartbeat_task_id.id}")
            celery_app.control.revoke(heartbeat_task_id.id, terminate=True)
            logger.info(f"Heartbeat task {heartbeat_task_id.id} revoked")

        if result.returncode == 0:
            return {
                "status": "completed",
                "exit_code": result.returncode,
                "stdout": result.stdout[-1000:],  # Last 1000 chars to avoid truncation
                "finished_at": datetime.datetime.now(datetime.UTC).isoformat(),
            }
        else:
            raise Exception(
                f"Ranker fit failed with exit code {result.returncode}: {result.stderr}"
            )

    except subprocess.TimeoutExpired:
        if heartbeat_task_id:
            celery_app.control.revoke(heartbeat_task_id.id, terminate=True)
        raise Exception("Ranker fit process timed out after 2 hours")
    except Exception as e:
        if heartbeat_task_id:
            celery_app.control.revoke(heartbeat_task_id.id, terminate=True)
        logger.exception(f"Error in Ranker fit task: {str(e)}")
        raise


@celery_app.task(bind=True, name="ranker.tasks.heartbeat_task")
def heartbeat_task(self, main_task_id):
    """Periodic heartbeat task"""
    import time

    logger.info(
        f"HEARTBEAT TASK STARTED for main task {main_task_id} on worker {self.request.hostname}"
    )

    iteration = 0
    while True:
        try:
            iteration += 1

            # Check if main task is still running
            main_task = celery_app.AsyncResult(main_task_id)
            logger.info(
                f"Heartbeat iteration {iteration}: Main task {main_task_id} state: {main_task.state}"
            )

            if main_task.state in ["SUCCESS", "FAILURE", "REVOKED"]:
                logger.info(
                    f"Main task {main_task_id} finished with state {main_task.state}, stopping heartbeat"
                )
                break

            # Get memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            self.update_state(
                state="PROGRESS",
                meta={
                    "main_task_id": main_task_id,
                    "memory_usage_mb": memory_mb,
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                    "iteration": iteration,
                },
            )

            logger.info(
                f"Heartbeat {iteration} for task {main_task_id}: Memory usage {memory_mb:.2f}MB"
            )
            time.sleep(10)

        except Exception as e:
            logger.error(f"Error in heartbeat iteration {iteration}: {str(e)}")
            time.sleep(10)
