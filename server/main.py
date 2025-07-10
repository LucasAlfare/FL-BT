# main.py
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

app.mount("/app", StaticFiles(directory="frontend/dist", html=True), name="frontend")


@app.get("/health")
async def root():
    return {"message": "We are healthy"}


# curl.exe -X POST http://localhost:8000/api/request/vjVkXlxsO8Q
@app.post("/api/request/{video_id}")
def submit_task(video_id: str):
    try:
        task = heavy_processing_entrypoint.apply_async(args=[video_id])
    except Exception as e:
        return {"error": str(e)}
    return {"video_id": video_id, "task_id": task.id, "status": "PENDING"}


# curl.exe http://localhost:8000/api/status/...
@app.get("/api/status/{task_id}")
def check_status(task_id: str):
    task_result = AsyncResult(task_id, app=heavy_processing_entrypoint.app)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "error": str(task_result.result) if task_result.failed() else None
    }


# curl.exe http://localhost:8000/api/download/...
# TODO: still has bugs in directories. I must take the proper zip dir.
@app.get("/api/download/{task_id}")
def download_result(task_id: str, background_tasks: BackgroundTasks):
    task_result = AsyncResult(task_id, app=heavy_processing_entrypoint.app)
    if not task_result or task_result.status != "SUCCESS":
        raise HTTPException(status_code=404, detail="Result not available")

    result_data = task_result.result
    if not isinstance(result_data, dict) or "zip_path" not in result_data:
        raise HTTPException(status_code=500, detail="Invalid task result structure")

    zip_path = result_data["zip_path"]
    background_tasks.add_task(cleanup_path, os.path.dirname(zip_path))

    filename = os.path.basename(zip_path)
    return FileResponse(
        path=zip_path,
        filename=filename,
        media_type="application/zip"
    )
