# main.py
import os
from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from server.celery_worker import heavy_processing_entrypoint
from server.lib import cleanup_path
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
def download_result(task_id: str, background_tasks: BackgroundTasks):
    """
    Download ZIP result from completed task.

    Args:
        task_id (str): Task ID.
        background_tasks (BackgroundTasks): For async cleanup.

    Returns:
        FileResponse: ZIP file if successful.
    """
    task_result = AsyncResult(task_id, app=heavy_processing_entrypoint.app)
    if not task_result or task_result.status != "SUCCESS":
        raise HTTPException(status_code=404, detail="Result not available")

    result_data = task_result.result
    if not isinstance(result_data, dict) or "zip_path" not in result_data:
        raise HTTPException(status_code=500, detail="Invalid task result structure")

    zip_path = result_data["zip_path"]
    logger.info(f"Serving file: {zip_path}")
    background_tasks.add_task(cleanup_path, os.path.dirname(zip_path))

    return FileResponse(
        path=os.path.abspath(zip_path),
        media_type="application/zip"
    )
