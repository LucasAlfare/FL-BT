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

BASE_TEMP_DIR = os.environ.get("BASE_TEMP_DIR", "/app/temp")


def download_youtube_audio(url: str, output_path: str) -> str | None:
    try:
        os.makedirs(output_path, exist_ok=True)
        yt = YouTube(url)
        stream: Stream = yt.streams.get_audio_only()
        return stream.download(output_path)
    except Exception as e:
        print(f"[ERROR] Download failed for {url}: {e}")
        return None


def get_audio_duration(path: str) -> float:
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
        raise RuntimeError(f"Falha ao obter duração do áudio: {e}")


def separate_stems_chunked(input_path: str, output_path: str,
                           codec: Codec = Codec.MP3) -> bool:
    try:
        from spleeter.separator import Separator
        import tensorflow as tf

        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)

        total_duration = get_audio_duration(input_path)
        chunk_duration = min(45, max(10, int(total_duration / ceil(total_duration / 45))))
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
        return True

    except Exception as e:
        print(f"[ERROR] Chunked separation failed: {e}")
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
    process = psutil.Process()
    print(f"Memory before job {video_id}: {process.memory_info().rss / 1024 / 1024:.2f} MB")

    base_dir = os.path.join(BASE_TEMP_DIR, video_id)
    download_dir = os.path.join(base_dir, "download")
    separate_dir = os.path.join(base_dir, "separated")
    zip_path = os.path.join(base_dir, f"{video_id}.zip")

    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(separate_dir, exist_ok=True)

    url = f'https://youtube.com/watch?v={video_id}'
    downloaded_path = download_youtube_audio(url, download_dir)
    if not downloaded_path:
        raise RuntimeError("Download failed")

    success = separate_stems_chunked(downloaded_path, separate_dir)
    if not success:
        raise RuntimeError("Separation failed")

    create_zip_from_folder(separate_dir, zip_path)

    print(f"Memory after job {video_id}: {process.memory_info().rss / 1024 / 1024:.2f} MB")
    return zip_path
