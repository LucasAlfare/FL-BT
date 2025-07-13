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

> **Note**: *Stems* are isolated instrument/vocal tracks. Since waveforms (e.g., WAV/MP3) aren't digitally tagged by instrument, separation is computationally intensive and inherently lossy.

## Overview

Each job takes YouTube video IDs as input and returns a ZIP with extracted stems.

Originally a CLI tool, now exposed via HTTP API. Dockerized for cross-environment use.

> **Warning**: High CPU and RAM usage. Designed for localhost use.
> Remote/VPS deployments are possible but **not recommended** for now due to:
>
> * Lack of authentication or rate limiting;
> * No resource quota or multi-tenant handling;
> * Single-threaded worker limits concurrency;
> * Missing CDN/file persistence strategy.

Ideal for musicians extracting stems locally, without relying on paid services. Future enhancements may include stem merging.

## Tech Stack

* [Python 3.10](https://www.python.org/)
* [UV](https://github.com/astral-sh/uv) (package manager)
* [`pytubefix`](https://github.com/JuanBindez/pytubefix) – YouTube downloader
* [`spleeter`](https://github.com/deezer/spleeter) – stem separation
* FastAPI – HTTP server
* Celery + Redis – task queue
* React + Vite – web UI

> **Note**: Python 3.10 is required due to Spleeter compatibility. UV resolves most dependency conflicts.

## Architecture

1. `POST /api/submit/{video_id}`
   → Enqueues task, returns `task_id`
2. Celery runs stem extraction
3. Client polls:
   `GET /api/status/{task_id}`
4. On success, download ZIP:
   `GET /api/download/{task_id}`

* Results are temporary; files auto-delete after download
* CDN support and cleanup workers planned
* Background worker is **synchronous** (1 job at a time), API is **asynchronous**

## Usage

Requires Docker.

```bash
docker-compose up --build
```

Then access: [http://localhost:8000/app](http://localhost:8000/app)

### API Examples

```bash
# Submit job
curl -X POST http://localhost:8000/api/submit/vjVkXlxsO8Q

# Check status
curl http://localhost:8000/api/status/{task_id}

# Download result (once ready)
curl -O http://localhost:8000/api/download/{task_id}
```

> The `/app` UI handles all API interactions.

## Notes

* Spleeter depends on FFMPEG and pretrained models → large container
* First build is slow (\~500s)
* High memory usage can crash tasks
* Long videos may fail due to TensorFlow memory issues

## Project Layout

```
/
├── Dockerfile, docker-compose.yaml, pyproject.toml, uv.lock
├── /server        # Python backend
└── /web_client    # React UI
```

## Known Issues

* TensorFlow memory leaks can crash tasks
* Celery queue should remain small (≤2 jobs)
* Restart container on failure

In this current project state, I implemented a strategy to save some memory. Instead of calling spleeter to separate a full song, now we separate the song in "chunks", which uses less memory, once spleeter will load less data to tensorflow/keras each time. After creating lot of separated chunks, I used *FFMPEG* to glue then and make a new track. This saves memory but can lead to weird sound abruptely, due to new chunk conversion is a absolutely new tensorflow model prediction and so on. By the way, based on my personal observation, the results are fine, making possible to request separation of a lot of songs in the celery queue again.

Other thing to improve is use some kind of CDN cache. Youtube videos doesn't changes their IDs, so we can store each new separation result in a CDN remote cache and, if the application receive the request for an existing ID, then just return the CDN cache content. If it was not possible to find in CDN, finally we perform the separation pipeline. This can save HUGE memory for existing items in cache. Should be my next improvement at this project.

## License

See [LICENSE](./LICENSE) for details.

## Contributing

This is a personal-use project, but contributions or suggestions are welcome!
