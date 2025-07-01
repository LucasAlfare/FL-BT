#  lib.py file

import os
from pytubefix import YouTube, Stream
from spleeter.audio import Codec
from spleeter.separator import Separator
import zipfile
import shutil

separator = Separator(params_descriptor='spleeter:4stems', multiprocess=True)


class DownloadedSongInfo:
    def __init__(self, title: str, original_url: str, output_os_path: str) -> None:
        self.title = title
        self.original_url = original_url
        self.output_os_path = output_os_path

    def __str__(self) -> str:
        return f'DownloadedSongInfo(title="{self.title}", original_url="{self.original_url}", output_os_path="{self.output_os_path}")'


class SeparationInfo:
    """
    Represents information about the separation process.

    Attributes:
        input_path (str): The input file path.
        output_path (str): The output directory path.
        codec (Codec): The audio codec used for the output files.
    """

    def __init__(self, input_path: str, output_path: str, codec: Codec) -> None:
        """
        Initializes the SeparationInfo object.

        Args:
            input_path (str): The input file path.
            output_path (str): The output directory path.
            codec (Codec): The audio codec used for the output files.
        """
        self.input_path = input_path
        self.output_path = output_path
        self.codec = codec

    def __str__(self) -> str:
        """
        Returns a string representation of the SeparationInfo object.

        Returns:
            str: A string describing the SeparationInfo object.
        """
        return f'SeparationInfo(input_path="{self.input_path}", output_path="{self.output_path}", codec={self.codec})'


def download_youtube_audio(url: str, output_path: str) -> DownloadedSongInfo | None:
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        yt = YouTube(url)
        # audio_stream: Stream = yt.streams.filter(only_audio=True).desc().first()
        audio_stream: Stream = yt.streams.get_audio_only()  # takes the best quality?
        output_file = audio_stream.download(output_path)

        return DownloadedSongInfo(title=yt.title, original_url=url, output_os_path=output_file)
    except Exception as e:
        print(f'Error trying to download the URL {url}.')
        print(f'The error:\n{e}')
        return None


def separate_4stems(input_path: str, output_path: str, codec: Codec = Codec.MP3) -> SeparationInfo | None:
    try:
        if not os.path.exists(input_path):
            print(f'Input path {input_path} does not exist.')
            return None

        if not os.path.exists(output_path):
            os.makedirs(output_path)

        separator.separate_to_file(input_path, output_path, codec=codec, synchronous=False)

        return SeparationInfo(input_path=input_path, output_path=output_path, codec=codec)
    except Exception as e:
        print(f'Error trying to separate stems for the input {input_path}. The error:\n{e}')
        return None


def create_zip_from_folder(folder_path: str, zip_path: str) -> None:
    """
    Creates a ZIP file using the specified content.
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)


def cleanup_path(path: str) -> None:
    """
    Used for clean up. Nothing is kept after the separation.
    """
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.isfile(path):
        os.remove(path)
