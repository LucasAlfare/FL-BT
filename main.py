#  main.py file

from lib import *
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi import Path
from fastapi import BackgroundTasks
import uuid

app = FastAPI()


@app.get("/api/health")
def health():
    return "Hello from FastAPI!"


# cls; curl.exe -X POST "http://localhost:8000/api/video/id/7085PPuxRiQ"
@app.post('/api/video/id/{video_id:path}')
async def yt_path(background_tasks: BackgroundTasks, video_id: str = Path(...)):
    base_dir = f'temp/{uuid.uuid4()}'
    download_dir = f'{base_dir}/download'
    separate_dir = f'{base_dir}/separated'

    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(separate_dir, exist_ok=True)

    downloaded = download_youtube_audio(f'https://youtube.com/watch?v={video_id}', download_dir)
    if not downloaded:
        cleanup_path(base_dir)
        raise HTTPException(status_code=400, detail='Download failed')

    separated = separate_4stems(downloaded.output_os_path, separate_dir)
    if not separated:
        cleanup_path(base_dir)
        raise HTTPException(status_code=500, detail='Separation failed')

    zip_file_name = f'{downloaded.title}.zip'  # replace spaces with underscores or no?
    zip_path = f'{base_dir}/{zip_file_name}'
    create_zip_from_folder(separate_dir, zip_path)

    background_tasks.add_task(cleanup_path, base_dir)
    return FileResponse(zip_path, media_type='application/zip', filename=f'{zip_file_name}')
