# main.py
from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.celery_worker import heavy_processing_entrypoint
from server.logging_config import logger

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend files. These files are pre-built in Docker stage, then they are accessible here.
app.mount("/app", StaticFiles(directory="frontend/dist", html=True), name="frontend")


@app.get("/health")
async def root():
    """
    Health check endpoint.
    """
    return {"message": "We are healthy"}


@app.post("/api/submit/{video_id}")
def submit_task(video_id: str):
    """
    Submit a video processing job to Celery.

    Args:
        video_id (str): YouTube video ID.

    Returns:
        dict: Submission result.
    """
    try:
        task = heavy_processing_entrypoint.apply_async(args=[video_id])
        logger.info(f"Task submitted for video_id={video_id}, task_id={task.id}")
    except Exception as e:
        logger.error(f"Failed to submit task: {e}")
        return {"error": str(e)}
    return {"video_id": video_id, "task_id": task.id, "status": "PENDING"}


@app.get("/api/status/{task_id}")
def check_status(task_id: str):
    """
    Check status of a Celery task.

    Args:
        task_id (str): Task ID.

    Returns:
        dict: Task status info.
    """
    task_result = AsyncResult(task_id, app=heavy_processing_entrypoint.app)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "error": str(task_result.result) if task_result.failed() else None
    }


@app.get("/api/download/{task_id}")
def download_result(task_id: str):
    """
    Returns the URL from the ZIP file generated after pipeline processing.

    Args:
        task_id (str): Task ID.

    Returns:
        dict: URL of the ZIP file in the CDN.
    """
    task_result = AsyncResult(task_id, app=heavy_processing_entrypoint.app)
    if not task_result or task_result.status != "SUCCESS":
        raise HTTPException(status_code=404, detail="Result not available")

    result_data = task_result.result
    if not isinstance(result_data, dict) or "url" not in result_data:
        raise HTTPException(status_code=500, detail="Invalid task result structure")

    return {"url": result_data["url"]}
