# celery_worker.py
import asyncio

from celery import Celery
from server.lib import single_pipeline
from server.logging_config import logger

# Celery application instance
celery_app = Celery(
    "worker",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)


@celery_app.task
def heavy_processing_entrypoint(video_id: str) -> dict[str, str]:
    """
    Celery task to run full processing pipeline.

    Args:
        video_id (str): YouTube video ID.

    Returns:
        dict[str, str]: Dictionary with video_id and url to the ZIP file in a CDN.
    """
    logger.info(f"Received task to process video ID: {video_id}.")
    url = asyncio.run(single_pipeline(video_id))
    return {"video_id": video_id, "url": url}
