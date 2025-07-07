# main.py
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from queue_manager import queue_task, get_task_status, start_background_workers, TaskStatus
from lib import cleanup_path, BASE_TEMP_DIR

app = FastAPI()
start_background_workers()

@app.post("/api/request/{video_id}")
def submit_task(video_id: str):
    task = queue_task(video_id)
    return {"video_id": video_id, "status": task["status"]}

@app.get("/api/status/{video_id}")
def check_status(video_id: str):
    task = get_task_status(video_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "video_id": video_id,
        "status": task["status"],
        "error": task["error"]
    }

@app.get("/api/download/{video_id}")
def download_result(video_id: str, background_tasks: BackgroundTasks):
    task = get_task_status(video_id)
    if not task or task["status"] != TaskStatus.SUCCESS:
        raise HTTPException(status_code=404, detail="Result not available")

    result_path = task["result_path"]
    if not result_path or not os.path.exists(result_path):
        raise HTTPException(status_code=500, detail="Result file missing")

    base_dir = f"{BASE_TEMP_DIR}/{video_id}"
    background_tasks.add_task(cleanup_path, base_dir)

    return FileResponse(
        path=result_path,
        filename=f"{video_id}.zip",
        media_type="application/zip"
    )