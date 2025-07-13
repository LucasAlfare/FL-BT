# github_as_cdn_helper.py
import base64
import os
from typing import Optional

import httpx
from pydantic import BaseModel


class Committer(BaseModel):
    name: str
    email: str


class GithubUploadRequestDTO(BaseModel):
    message: str
    committer: Committer
    content: str


class GithubUploadResponseContent(BaseModel):
    name: str
    path: str
    download_url: str


class GithubUploadResponseDTO(BaseModel):
    content: GithubUploadResponseContent


class GithubHelper:
    BASE_URL = "https://api.github.com"
    USERNAME = os.environ["GITHUB_USERNAME"]
    REPOSITORY = os.environ["GITHUB_REPO"]
    TOKEN = os.environ["GITHUB_TOKEN"]
    COMMITTER_NAME = os.environ["GITHUB_COMMIT_NAME"]
    COMMITTER_EMAIL = os.environ["GITHUB_COMMIT_EMAIL"]

    @staticmethod
    async def upload_file_to_github(
            input_file_name: str,
            input_file_bytes: bytes,
            commit_message: str = "Upload file via my custom API wrapper 🛠",
    ) -> Optional[GithubUploadResponseDTO]:

        file_content_base64 = base64.b64encode(input_file_bytes).decode("utf-8")
        final_target_path = f"uploads/{input_file_name}/{input_file_name}"
        url = f"{GithubHelper.BASE_URL}/repos/{GithubHelper.USERNAME}/{GithubHelper.REPOSITORY}/contents/{final_target_path}"

        headers = {
            "Authorization": f"Bearer {GithubHelper.TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        payload = GithubUploadRequestDTO(
            message=commit_message,
            committer=Committer(name=GithubHelper.COMMITTER_NAME, email=GithubHelper.COMMITTER_EMAIL),
            content=file_content_base64
        ).dict()

        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers, json=payload)

        if response.status_code == 201:
            return GithubUploadResponseDTO(**response.json())
        return None

    @staticmethod
    async def file_exists_on_github(
            input_file_name: str,
    ) -> Optional[str]:
        file_path = f"uploads/{input_file_name}/{input_file_name}"
        url = f"{GithubHelper.BASE_URL}/repos/{GithubHelper.USERNAME}/{GithubHelper.REPOSITORY}/contents/{file_path}"

        headers = {
            "Authorization": f"Bearer {GithubHelper.TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            return response.json().get("download_url")
        return None
