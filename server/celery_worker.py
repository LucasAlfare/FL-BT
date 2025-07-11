from celery import Celery
from server.lib import single_pipeline

celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)
"""
celery_app: Configured Celery instance using Redis for both messaging and result backend.

- Broker manages task dispatching and queueing.
- Backend stores results for retrieval after task completion.
- Redis chosen for low latency and reliability in distributed task processing.
"""


@celery_app.task
def heavy_processing_entrypoint(video_id: str) -> dict[str, str]:
    """
    Asynchronous Celery task triggering the audio processing pipeline.

    - Logs start of job identified by video_id.
    - Calls single_pipeline to handle download, stem separation, and packaging.
    - Returns a dictionary with the video ID and path to the generated ZIP archive.
    - Enables horizontal scaling of resource-intensive audio tasks without blocking.
    """
    print(f"Starting the job {video_id}...")
    zip_path = single_pipeline(video_id)
    return {"video_id": video_id, "zip_path": zip_path}
