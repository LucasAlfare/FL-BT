# server/main.py

import os

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException
from fastapi import Path
from fastapi.responses import JSONResponse, FileResponse

from celery_app import celery_app  # celery instance import
from lib import cleanup_path
from tasks import process_video_task  # celery task import
from tasks import celery_app

app = FastAPI()


@app.get("/api/health")
def health():
    return "Hello from FastAPI!"


@app.post('/api/video/id/{video_id:path}')
def submit_video(video_id: str = Path(...)):
    task = process_video_task.delay(video_id)
    return JSONResponse({"task_id": task.id})


@app.get('/api/task/status/{task_id}')
def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.successful() else None,
        "error": str(task_result.result) if task_result.failed() else None,
    }
    return JSONResponse(response)


@app.get('/api/task/result/{task_id}')
def download_result(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    if not task_result.successful():
        raise HTTPException(status_code=404, detail="Task result not available")

    zip_path = task_result.result
    if not zip_path or not os.path.isfile(zip_path):
        raise HTTPException(status_code=404, detail="File not found")

    response = FileResponse(zip_path, media_type='application/zip', filename=os.path.basename(zip_path))

    # Clean up after sending file
    cleanup_path(os.path.dirname(zip_path))
    return response
