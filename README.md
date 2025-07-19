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

This project wraps [Spleeter](https://github.com/deezer/spleeter) to extract audio stems from one or more YouTube videos.

> ⚠️ Warning: This projetct is not tested/compatible with ARM64 architectures due to tensorflow compatibility.

---

## Overview

This was born as a CLI tool, now I expanded to an app, exposed via HTTP API. Dockerized for cross-environment use.

Ideal for musicians extracting stems locally, without relying on paid services. Future enhancements may include stem merging.

Each job takes YouTube video IDs as input and returns a ZIP (URL to it) with extracted stems.

---

## How to use

This project uses Docker with `.env` variables to work.

### .env Configuration and GitHub as CDN

A `.env` file is required for configuration, as all CDN-related functionality currently depends exclusively on GitHub repositories acting as a CDN. No other CDN providers are supported at this moment.

You **must** have:

- A **GitHub repository** to store cached stem extraction results.
- A **GitHub Personal Access Token (PAT)** with appropriate repository permissions.

The `.env` file must contain these variables:

```dotenv
GITHUB_USERNAME=username
GITHUB_REPO=repository_name
GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
GITHUB_COMMIT_NAME=any_simple_name_for_ideentification
GITHUB_COMMIT_EMAIL=any_email_for_registry@abc.com
MAX_AUDIO_CHUNK_DURATION=20#in seconds
```

Relevant descriptions:
- `GITHUB_USERNAME`: The name of the owner of the GitHub repository (probably you).
- `GITHUB_REPO`: GitHub repository name where cached files will be stored and retrieved.
- `GITHUB_TOKEN`: Personal Access Token for accessing the GitHub API to upload/download cached files.
- `MAX_AUDIO_CHUNK_DURATION`: Defines the audio chunk duration which spleeter will take during each separation. Defaults to 45. 

This is **mandatory** because the project uses GitHub as a makeshift CDN to cache processed results. Without this setup, the project will not cache outputs, leading to repeated processing and high resource usage.

No alternative CDN providers are supported today. You cannot substitute GitHub with S3, Cloudflare, or others **yet**.

> **Note:** not less important but as this needs to connect to GitHub repository AND to download YouTube audio from videos, you can not to run this offline. In the future I may re-implement offline usage, but for now, stay connected.

### Running and using

With docker available in your machine, run:

```bash
docker-compose up --build
````

Wait the build, then access: [http://localhost:8000/app](http://localhost:8000/app) to interact with the web client page.

---

## Tech Stack

* [Python 3.10](https://www.python.org/)
* [UV](https://github.com/astral-sh/uv) (package manager)
* [`pytubefix`](https://github.com/JuanBindez/pytubefix) – YouTube downloader
* [`spleeter`](https://github.com/deezer/spleeter) – stem separation
* FastAPI – HTTP server
* Celery + Redis – task queue
* React + Vite – web UI

> **Note**: Python 3.10 is required due to Spleeter compatibility. UV also resolves most dependency conflicts.

---

## Architecture

1. `POST /api/submit/{video_id}`
   → Enqueues task, returns `task_id`
2. Celery runs stem extraction
3. Client polls:
   `GET /api/status/{task_id}`
4. On success, download ZIP:
   `GET /api/download/{task_id}`

> **Note:** Background worker is **synchronous** (1 job at a time), API is **asynchronous**

---

### API Examples

If you don't want to interact with the web-page from `/app`, you can handle endpoints manually:

```bash
# Submit job
curl -X POST http://localhost:8000/api/submit/vjVkXlxsO8Q

# Check status
curl http://localhost:8000/api/status/{task_id}

# Download result (once ready)
curl -O http://localhost:8000/api/download/{task_id}
```

> **Note:** The UI served in the endpoint `/app` handles all those API interactions.

---

## Other notes

* Spleeter depends on FFMPEG and pretrained models → large container
* First build is slow (\~500s)
* High memory usage can crash tasks is chunk size is set to higher duration values (e.g.: 1+ min)
* Long videos may fail due to TensorFlow memory issues

---

## Project Layout

```
/
├── Dockerfile, docker-compose.yaml, pyproject.toml, uv.lock, .env
├── /server        # Python backend
└── /web_client    # React UI
```

---

## Known Issues

In this current project state, I implemented a strategy to save some memory. Instead of calling spleeter to separate a full song, now we separate the song in "chunks", which uses less memory, once spleeter will load less data to tensorflow/keras each time. After creating a lot of separated chunks, I used *FFMPEG* to glue them together and make a new track. This saves memory but can lead to micro weird abrupt sound transitions, due to new chunk conversion being a new TensorFlow model prediction. The results are acceptable for queueing multiple songs in Celery. Finally, I have set the chunks to 45 seconds, and the abrupt sound transitions would not happen too much. 

Is possible to check alternatives to avoid cuts between chunks, based on the time precision when offsetting the audio. However this can be a natural problem, once the timing precision is not guaranteed in terms of floating points numbers. 

Another planned improvement is proper CDN caching. Since YouTube video IDs don't change, storing separation results in a CDN cache avoids re-processing. Currently, only GitHub repositories act as this cache.

With the project growing, I can use real money to pay for real CDN services, leaving off the McGyverism of using github repositories as CDN. 

---

## License

See [LICENSE](./LICENSE) for details.

---

## Contributing

This is a personal-use project, but contributions or suggestions are welcome!