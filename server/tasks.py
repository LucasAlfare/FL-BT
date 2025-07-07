# server/tasks.py

import os
import uuid
from lib import download_youtube_audio, separate_4stems, create_zip_from_folder
from celery_app import celery_app


@celery_app.task(name="tasks.process_video_task", bind=True)
def process_video_task(self, video_id: str) -> str:
    base_dir = f'temp/{uuid.uuid4()}'
    download_dir = f'{base_dir}/download'
    separate_dir = f'{base_dir}/separated'

    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(separate_dir, exist_ok=True)

    downloaded = download_youtube_audio(f'https://youtube.com/watch?v={video_id}', download_dir)
    if not downloaded:
        raise Exception("Download failed")

    separated = separate_4stems(downloaded.output_os_path, separate_dir)
    if not separated:
        raise Exception("Separation failed")

    zip_file_name = f'{downloaded.title.replace(" ", "_")}.zip'
    zip_path = f'{base_dir}/{zip_file_name}'
    create_zip_from_folder(separate_dir, zip_path)

    return zip_path
