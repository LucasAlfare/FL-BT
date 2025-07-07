# queue_manager.py
import threading
import time
from enum import Enum
from lib import single_pipeline, BASE_TEMP_DIR
import os

task_queue: list[str] = []
task_map: dict[str, dict] = {}
lock = threading.Lock()

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    EXPIRED = "EXPIRED"

def queue_task(video_id: str):
    with lock:
        if video_id not in task_map:
            task_map[video_id] = {
                "status": TaskStatus.PENDING,
                "result_path": None,
                "error": None,
                "created_at": time.time(),
                "completed_at": None
            }
            task_queue.append(video_id)
        return task_map[video_id]

def get_task_status(video_id: str):
    with lock:
        return task_map.get(video_id)

def worker_loop():
    while True:
        with lock:
            if not task_queue:
                task = None
            else:
                video_id = task_queue.pop(0)
                task = task_map[video_id]
                task["status"] = TaskStatus.PROCESSING

        if not task:
            time.sleep(0.1)
            continue

        try:
            single_pipeline(video_id)
            result_path = os.path.join(BASE_TEMP_DIR, video_id, f"{video_id}.zip")
            with lock:
                task["status"] = TaskStatus.SUCCESS
                task["result_path"] = result_path
                task["completed_at"] = time.time()
        except Exception as e:
            with lock:
                task["status"] = TaskStatus.FAILURE
                task["error"] = str(e)

def start_background_workers():
    threading.Thread(target=worker_loop, daemon=True).start()