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


@app.post("/api/request/{video_id}")
def submit_task(video_id: str):
    try:
        task = heavy_processing_entrypoint.apply_async(args=[video_id], task_id=video_id)
    except Exception as e:
        return {"error": str(e)}
    return {"video_id": video_id, "status": "PENDING"}


@app.get("/api/status/{video_id}")
def check_status(video_id: str):
    task_result = AsyncResult(video_id, app=heavy_processing_entrypoint.app)
    return {
        "video_id": video_id,
        "status": task_result.status,
        "error": "None"
    }


@app.get("/api/download/{video_id}")
def download_result(video_id: str, background_tasks: BackgroundTasks):
    task_result = AsyncResult(video_id, app=heavy_processing_entrypoint.app)
    if not task_result or task_result.status != "SUCCESS":
        raise HTTPException(status_code=404, detail="Result not available")

    zip_path = task_result.result
    background_tasks.add_task(cleanup_path, os.path.dirname(zip_path))

    return FileResponse(
        path=zip_path,
        filename=f"{video_id}.zip",
        media_type="application/zip"
    )

    # TODO: retrieve zip_path from task_result.result to get the file and "schedule" to clean up

    # base_dir = f"{BASE_TEMP_DIR}/{video_id}"
    # background_tasks.add_task(cleanup_path, base_dir)
    #
    # return FileResponse(
    #     path=result_path,
    #     filename=f"{video_id}.zip",
    #     media_type="application/zip"
    # )

# start_background_workers()
#
#
# @app.post("/api/request/{video_id}")
# def submit_task(video_id: str):
#     task = queue_task(video_id)
#     return {"video_id": video_id, "status": task["status"]}
#
#
# @app.get("/api/status/{video_id}")
# def check_status(video_id: str):
#     task = get_task_status(video_id)
#     if not task:
#         raise HTTPException(status_code=404, detail="Task not found")
#     return {
#         "video_id": video_id,
#         "status": task["status"],
#         "error": task["error"]
#     }
#
#
# @app.get("/api/download/{video_id}")
# def download_result(video_id: str, background_tasks: BackgroundTasks):
#     task = get_task_status(video_id)
#     if not task or task["status"] != TaskStatus.SUCCESS:
#         raise HTTPException(status_code=404, detail="Result not available")
#
#     result_path = task["result_path"]
#     if not result_path or not os.path.exists(result_path):
#         raise HTTPException(status_code=500, detail="Result file missing")
#
#     base_dir = f"{BASE_TEMP_DIR}/{video_id}"
#     background_tasks.add_task(cleanup_path, base_dir)
#
#     return FileResponse(
#         path=result_path,
#         filename=f"{video_id}.zip",
#         media_type="application/zip"
#     )
