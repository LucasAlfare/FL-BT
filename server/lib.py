# lib.py
import os
import shutil
import zipfile
from pytubefix import YouTube, Stream
from spleeter.audio import Codec
from spleeter.separator import Separator
import tensorflow as tf

BASE_TEMP_DIR = os.path.abspath("temp")
separator = Separator(params_descriptor='spleeter:4stems', multiprocess=False)

tf.config.threading.set_intra_op_parallelism_threads(1)
tf.config.threading.set_inter_op_parallelism_threads(1)


def download_youtube_audio(url: str, output_path: str) -> str | None:
    try:
        os.makedirs(output_path, exist_ok=True)
        yt = YouTube(url)
        stream: Stream = yt.streams.get_audio_only()
        return stream.download(output_path)
    except Exception as e:
        print(f"[ERROR] Download failed for {url}: {e}")
        return None


def separate_4stems(input_path: str, output_path: str, codec: Codec = Codec.MP3) -> bool:
    try:
        if not os.path.exists(input_path):
            return False
        os.makedirs(output_path, exist_ok=True)
        # we will perform only 1 separation per time per worker
        separator.separate_to_file(input_path, output_path, codec=codec, synchronous=True)
        return True
    except Exception as e:
        print(f"[ERROR] Separation failed: {e}")
        return False


def create_zip_from_folder(folder_path: str, zip_path: str) -> None:
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)


def cleanup_path(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    elif os.path.isfile(path):
        os.remove(path)


def single_pipeline(video_id: str) -> str:
    base_dir = f'{BASE_TEMP_DIR}/{video_id}'
    download_dir = f'{base_dir}/download'
    separate_dir = f'{base_dir}/separated'
    zip_path = f'{base_dir}/{video_id}.zip'

    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(separate_dir, exist_ok=True)

    url = f'https://youtube.com/watch?v={video_id}'
    downloaded_path = download_youtube_audio(url, download_dir)
    if not downloaded_path:
        raise RuntimeError("Download failed")

    success = separate_4stems(downloaded_path, separate_dir)
    if not success:
        raise RuntimeError("Separation failed")

    create_zip_from_folder(separate_dir, zip_path)

    return zip_path
