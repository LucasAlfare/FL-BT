import os
import shutil
import zipfile
from pytubefix import YouTube, Stream
from spleeter.audio import Codec
import psutil

BASE_TEMP_DIR = os.path.abspath("temp")
"""
Defines the base directory for temporary files.
Using an absolute path ensures consistent file handling regardless of
where the script is executed.
"""


def download_youtube_audio(url: str, output_path: str) -> str | None:
    """
    Downloads the audio-only stream from a YouTube video URL.

    - Creates output directory if missing.
    - Uses pytubefix to fetch YouTube streams, prioritizing audio-only.
    - Returns the local file path of the downloaded audio or None on failure.
    """
    try:
        os.makedirs(output_path, exist_ok=True)
        yt = YouTube(url)
        stream: Stream = yt.streams.get_audio_only()  # Get only audio stream for minimal data
        return stream.download(output_path)
    except Exception as e:
        print(f"[ERROR] Download failed for {url}: {e}")
        return None


def separate_4stems(input_path: str, output_path: str, codec: Codec = Codec.MP3) -> bool:
    """
    Performs 4-stem audio separation on the input audio file.

    - Loads spleeter's Separator with 4 stems configuration (vocals, drums, bass, other).
    - Limits TensorFlow thread parallelism to reduce resource contention.
    - Separates audio and writes output to given directory in specified codec.
    - Deletes separator instance to free resources explicitly.
    - Returns True on success, False on any failure.
    """
    try:
        from spleeter.separator import Separator
        import tensorflow as tf

        # Restrict TensorFlow parallelism to avoid excessive CPU usage
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)

        separator = Separator(params_descriptor='spleeter:4stems', multiprocess=False)

        separator.separate_to_file(input_path, output_path, codec=codec, synchronous=True)

        del separator  # Explicit cleanup

        return True

    except Exception as e:
        print(f"[ERROR] Separation failed: {e}")
        return False


def create_zip_from_folder(folder_path: str, zip_path: str) -> None:
    """
    Compresses the entire folder into a ZIP archive.

    - Walks folder recursively to include all files.
    - Writes files preserving relative paths for consistent extraction.
    - Uses ZIP_DEFLATED compression for balance of speed and size.
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)


def cleanup_path(path: str) -> None:
    """
    Removes a file or directory at the given path.

    - Recursively deletes directories with all contents.
    - Deletes single files.
    - Ignores errors to avoid failure if file/dir is missing.
    """
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    elif os.path.isfile(path):
        os.remove(path)


def single_pipeline(video_id: str) -> str:
    """
    Executes the full processing pipeline for one YouTube video ID.

    Steps:
    1. Logs memory usage before starting for monitoring.
    2. Sets up a temp folder structure for download, separation, and zip.
    3. Downloads audio from YouTube.
    4. Runs 4-stem separation on downloaded audio.
    5. Creates a ZIP archive of separated stems.
    6. Logs memory usage after processing.
    7. Returns the path to the resulting ZIP archive.

    Raises RuntimeError if download or separation fails.
    """
    process = psutil.Process()
    print(f"Memory before job {video_id}: {process.memory_info().rss / 1024 / 1024:.2f} MB")

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

    print(f"Memory after job {video_id}: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    return zip_path
