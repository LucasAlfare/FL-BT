import os

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from server.celery_worker import heavy_processing_entrypoint
from server.lib import cleanup_path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
Enable CORS for all origins, methods, and headers.

Allows frontend apps from any domain to access the API.
"""

app.mount("/app", StaticFiles(directory="frontend/dist", html=True), name="frontend")
"""
Serves static frontend files at /app route.

- Serves index.html automatically for SPA support.
- Maps requests under /app to frontend/dist directory.
"""


@app.get("/health")
async def root():
    """Health check endpoint."""
    return {"message": "We are healthy"}


@app.post("/api/submit/{video_id}")
def submit_task(video_id: str):
    """
    Submit a background Celery task for audio processing by video ID.

    Returns:
    - task ID for status tracking.
    - Initial status "PENDING".

    Example:
    curl -X POST http://localhost:8000/api/submit/vjVkXlxsO8Q
    """
    try:
        task = heavy_processing_entrypoint.apply_async(args=[video_id])
    except Exception as e:
        return {"error": str(e)}
    return {"video_id": video_id, "task_id": task.id, "status": "PENDING"}


@app.get("/api/status/{task_id}")
def check_status(task_id: str):
    """
    Check the status of a submitted Celery task by task ID.

    Returns task status and error if task failed.

    Example:
    curl http://localhost:8000/api/status/<task_id>
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
    Returns the ZIP file result for a completed task.

    - Validates task completion and result structure.
    - Schedules cleanup of extracted files after response.
    - Returns ZIP file as application/zip.

    Example:
    curl http://localhost:8000/api/download/<task_id> --output stems.zip
    """
    task_result = AsyncResult(task_id, app=heavy_processing_entrypoint.app)
    if not task_result or task_result.status != "SUCCESS":
        raise HTTPException(status_code=404, detail="Result not available")

    result_data = task_result.result
    if not isinstance(result_data, dict) or "zip_path" not in result_data:
        raise HTTPException(status_code=500, detail="Invalid task result structure")

    zip_path = result_data["zip_path"]
    background_tasks.add_task(cleanup_path, os.path.dirname(zip_path))

    print(f'responding the file of the path [{zip_path}]...')

    return FileResponse(
        path=os.path.abspath(zip_path),
        media_type="application/zip"
    )
