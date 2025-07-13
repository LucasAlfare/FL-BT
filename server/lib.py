# lib.py
import os
import shutil
import tempfile
import subprocess
import zipfile
from math import ceil

import psutil
from pytubefix import YouTube, Stream
from spleeter.audio import Codec

from server.logging_config import logger
from server.github_as_cdn_helper import GithubHelper

BASE_TEMP_DIR = os.environ.get("BASE_TEMP_DIR", "/app/temp")


def download_youtube_audio(url: str, output_path: str) -> str | None:
    """
    Downloads audio from a YouTube URL using pytubefix.

    Args:
        url (str): YouTube video URL.
        output_path (str): Path to store downloaded file.

    Returns:
        str | None: Path to the downloaded file or None if failed.
    """
    try:
        os.makedirs(output_path, exist_ok=True)
        yt = YouTube(url)
        stream: Stream = yt.streams.get_audio_only()
        logger.info(f"Downloading audio from URL: {url}...")
        return stream.download(output_path)
    except Exception as e:
        logger.error(f"Download failed for {url}: {e}.")
        return None


def get_audio_duration(path: str) -> float:
    """
    Gets the duration of an audio file using ffprobe.

    Args:
        path (str): Path to the audio file.

    Returns:
        float: Duration in seconds.

    Raises:
        RuntimeError: If ffprobe fails.
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        raise RuntimeError(f"Failed to get audio duration: {e}.")


def separate_stems_chunked(input_path: str, output_path: str,
                           codec: Codec = Codec.MP3) -> bool:
    """
    Separates audio into 4 stems (vocals, drums, bass, other) using Spleeter in chunks.

    Args:
        input_path (str): Path to the input audio.
        output_path (str): Destination directory.
        codec (Codec): Output audio codec.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        from spleeter.separator import Separator
        import tensorflow as tf

        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)

        logger.info("Starting audio separation process...")

        total_duration = get_audio_duration(input_path)

        max_audio_chunk_duration = os.environ["MAX_AUDIO_CHUNK_DURATION"]
        if not max_audio_chunk_duration:
            max_audio_chunk_duration = 45
        else:
            max_audio_chunk_duration = int(max_audio_chunk_duration)

        chunk_duration = min(
            max_audio_chunk_duration,
            max(10, int(total_duration / ceil(total_duration / max_audio_chunk_duration)))
        )
        logger.debug(f"Total duration: {total_duration:.2f}s, chunk size: {chunk_duration}s.")

        os.makedirs(output_path, exist_ok=True)
        tmp_base = tempfile.mkdtemp()

        separator = Separator('spleeter:4stems', multiprocess=False)
        chunk_count = int(total_duration // chunk_duration) + 1
        stems = ['vocals', 'drums', 'bass', 'other']
        chunk_outputs = {stem: [] for stem in stems}

        for i in range(chunk_count):
            offset = i * chunk_duration
            tmp_out = os.path.join(tmp_base, f'chunk_{i}')
            os.makedirs(tmp_out, exist_ok=True)
            logger.info(f"Processing chunk {i + 1}/{chunk_count} at offset {offset}s...")

            separator.separate_to_file(
                audio_descriptor=input_path,
                destination=tmp_out,
                offset=offset,
                duration=chunk_duration,
                codec=codec,
                synchronous=True
            )

            for stem in stems:
                stem_path = os.path.join(
                    tmp_out,
                    os.path.basename(input_path).split('.')[0],
                    f"{stem}.{codec.value}"
                )
                if os.path.exists(stem_path):
                    chunk_outputs[stem].append(stem_path)

        logger.info("Concatenating stem outputs...")
        for stem in stems:
            concat_list = os.path.join(tmp_base, f"{stem}_concat.txt")
            with open(concat_list, "w") as f:
                for path in chunk_outputs[stem]:
                    f.write(f"file '{path}'\n")

            final_path = os.path.join(output_path, f"{stem}.{codec.value}")
            subprocess.run([
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", concat_list, "-c", "copy", final_path
            ], check=True)

        shutil.rmtree(tmp_base, ignore_errors=True)
        del separator
        logger.info("Audio separation completed successfully.")
        return True

    except Exception as e:
        logger.error(f"Chunked separation failed: {e}.")
        return False


def create_zip_from_folder(folder_path: str, zip_path: str) -> None:
    """
    Creates a ZIP file from a given folder.

    Args:
        folder_path (str): Source folder path.
        zip_path (str): Destination ZIP file path.
    """
    logger.info(f"Creating zip file at: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)


def cleanup_path(path: str) -> None:
    """
    Deletes a file or folder from the filesystem.

    Args:
        path (str): Path to delete.
    """
    logger.info(f"Cleaning up path: {path}...")
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    elif os.path.isfile(path):
        os.remove(path)


async def single_pipeline(video_id: str) -> str:
    """
    Full processing pipeline: download, separate stems, zip or return existing CDN URL.

    Args:
        video_id (str): YouTube video ID.

    Returns:
        str: URL to resulting ZIP file (from CDN).

    Raises:
        RuntimeError: On any stage failure.
    """
    # First verifies if CDN already contains the file
    existing_url = await GithubHelper.file_exists_on_github(
        input_file_name=f"{video_id}.zip"
    )
    if existing_url:
        logger.info(f"File {video_id} is cached in the CDN!")
        return existing_url

    process = psutil.Process()
    logger.info(f"File {video_id} is NOT cached in the CDN.")
    logger.info(f"Starting pipeline for video {video_id}...")
    logger.debug(f"Memory before job: {process.memory_info().rss / 1024 / 1024:.2f} MB.")

    base_dir = os.path.join(BASE_TEMP_DIR, video_id)
    download_dir = os.path.join(base_dir, "download")
    separate_dir = os.path.join(base_dir, "separated")
    zip_path = os.path.join(base_dir, f"{video_id}.zip")

    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(separate_dir, exist_ok=True)

    url = f'https://youtube.com/watch?v={video_id}'
    downloaded_path = download_youtube_audio(url, download_dir)
    if not downloaded_path:
        raise RuntimeError("Download failed.")

    success = separate_stems_chunked(downloaded_path, separate_dir)
    if not success:
        raise RuntimeError("Separation failed.")

    create_zip_from_folder(separate_dir, zip_path)

    logger.debug(f"Memory after job: {process.memory_info().rss / 1024 / 1024:.2f} MB.")
    logger.info(f"Pipeline completed for video {video_id}. Uploading to CDN...")

    with open(zip_path, "rb") as f:
        upload_result = await GithubHelper.upload_file_to_github(
            input_file_name=f"{video_id}.zip",
            input_file_bytes=f.read()
        )

    if not upload_result:
        raise RuntimeError("CDN upload failed.")
    else:
        logger.info(f"Uploading to CDN completed for video {video_id}.")

    logger.info("Starting cleaning up temp files routine...")
    cleanup_path(download_dir)
    cleanup_path(separate_dir)
    cleanup_path(zip_path)
    logger.info("Cleaning up temp files routine completed.")

    return upload_result.content.download_url
