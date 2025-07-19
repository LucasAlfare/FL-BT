```
███████╗██╗                   ██████╗ ████████╗
██╔════╝██║                   ██╔══██╗╚══██╔══╝
█████╗  ██║         █████╗    ██████╔╝   ██║   
██╔══╝  ██║         ╚════╝    ██╔══██╗   ██║   
██║     ███████╗              ██████╔╝   ██║   
╚═╝     ╚══════╝              ╚═════╝    ╚═╝   
```

> _"FL-BT"_ stands for _"Francisco Lucas BackingTracker"_


<p align="center">
  <img src="img/img.png" width="300px"  alt="image of main UI with task in 'PENDING' state"/>
  <img src="img/img_1.png" width="300px"  alt="image of main UI with task in 'SUCCESS' state"/>
</p>

<p align="center">
  <sub><i>Initial UI design exploration assisted by AI tools</i></sub>
</p>

This project wraps Spleeter to extract audio stems (vocals, instruments, etc.) from one or more YouTube videos.

> ⚠ Warning: This project is not compatible with ARM64 due to TensorFlow limitations.

---

## Overview

Originally built as a CLI tool, it is now a web app with an HTTP API, fully Dockerized for cross-environment use.

- Use case: Musicians who want to extract stems locally, without paid services.

- Output: A ZIP file (downloadable URL) containing the extracted stems.

- Planned features: Stem merging and better CDN caching.



---

## Quick Start

1. Requirements

Docker

A GitHub repository for caching results.

A GitHub Personal Access Token (PAT) with repository permissions.


2. .env Setup

Create a .env file with:

```envfile
GITHUB_USERNAME=username
GITHUB_REPO=repository_name
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GITHUB_COMMIT_NAME=commit_identifier
GITHUB_COMMIT_EMAIL=email@example.com
MAX_AUDIO_CHUNK_DURATION=45
```

Notes:

- GitHub is used as a makeshift CDN for caching processed stems.

- No other CDN providers are supported yet.

- Internet connection is required (GitHub + YouTube downloads).


3. Run

```bash
docker-compose up --build
```

Once running, open: http://localhost:8000/app


---

## API

### Endpoints

1. `POST /api/submit/{video_id}` – Submit a job (returns task_id).


2. `GET /api/status/{task_id}` – Check job status.


3. `GET /api/download/{task_id}` – Download the ZIP (when ready).


#### Examples

##### Submit
`curl -X POST http://localhost:8000/api/submit/vjVkXlxsO8Q`

###### Check status
`curl http://localhost:8000/api/status/{task_id}`

###### Download
`curl -O http://localhost:8000/api/download/{task_id}`


---

## Tech Stack

- Backend: Python 3.10, FastAPI, Celery + Redis, Spleeter, pytubefix

- Frontend: React + Vite

- Others: UV (dependency manager), Docker, FFMPEG



---

## Architecture

- Background worker: synchronous (1 job at a time)

- API: asynchronous

- Workflow:

1. Job submitted → queued in Celery


2. Spleeter extracts stems (chunked processing to save memory)


3. Results uploaded to GitHub (cache)


4. Client downloads ZIP

---

## Known Issues & Limitations

- Chunking: Long audio is split into 45s chunks to avoid TensorFlow OOM issues.

- This may cause minor audio transitions between chunks.

- Future improvements aim to reduce or eliminate these artifacts.

- Build: First Docker build is slow (~500s).

- Memory: Large videos or big chunk durations may cause crashes.

- CDN: Only GitHub is supported for caching (S3/Cloudflare planned).

---

Project Structure

```
/
├── Dockerfile, docker-compose.yaml, pyproject.toml, uv.lock, .env
├── /server        # Python backend
└── /web_client    # React frontend 
```

---

## License

See LICENSE.

---

## Contributing

This is primarily a personal project, but contributions and suggestions are welcome!
