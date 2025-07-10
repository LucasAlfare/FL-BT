```
███████╗██╗                   ██████╗ ████████╗
██╔════╝██║                   ██╔══██╗╚══██╔══╝
█████╗  ██║         █████╗    ██████╔╝   ██║   
██╔══╝  ██║         ╚════╝    ██╔══██╗   ██║   
██║     ███████╗              ██████╔╝   ██║   
╚═╝     ╚══════╝              ╚═════╝    ╚═╝   
```

> _"FL-BT"_ stands for _"Francisco Lucas BackingTracker"_

This project is a wrapper for Spleeter tool. The task that uses Spleeter is to retrieve audio from one or more YouTube videos and separate then into stems. Each separation job is returned to the user. In other words, the tool receives YouTube videos IDs as _input_ and spits zip files, each containing the separated/isolated audio tracks/stems.

This project was firstly done in command-line in pure python script, however was nice the idea to expose it though an HTTP web-api and, using the Docker tool, it would become suitable to be used in more different environments.

Since this is a tool that performs heavy tasks in terms of memory allocation and processing, for now it is designed to be used at localhost only. Is possible to run on cloud VPSs, however the target machines must have at least 6GB ram and some CUP cores available to receive requests. More details about implementation below.

Thinking this in a personal custom local service, it's fine for musicians that want to get stems/tracks of a song without using online paid services. Also, in the future, we plan to implement more options to do with the generated stems, such as combining multiple of then in a single audio track, and so on.

## Tech stack

For this project we have chosen most things in Python, mostly due to the fact Spleeter library is written in it:

- Python (3.10) _language*_;
- UV package manager tool (not PiP!);
- pytubefix for YouTube audio downloading;
- Spleeter library for song tracks/stems separation;
- FastAPI as web-server for the API;
- Celery for background working with Redis as backend;
- React+Vite for simple generation of web page to consume the API;

> _*Note_: Here I used strictly specific this python version because Spleeter library is not being actively maintained, so its current version works only with this specific python version. Also, due to this, much other versioning was very sensitive, and we faced a lot of dependency hell, which was mostly solved by using UV based on that python version.

## Implementation flow

We tried the most simple approach:

- Receive a task request via web API:
  - the task comes with desired YouTube video ID in path parameter (`POST /api/submit/{ID}`);
  - this request responds with the actual `TASK_ID`;
- Enqueue the request in a background job using Celery;
- While the task is being performed, the client can check its status:
  - `GET /api/status/{TASK_ID}`;
- When task is done, server keep the resulting files for a while;
  - the result files are removed after the client downloads it;
  - in the future we plan to implement a new worker to clean up the results;
  - for now, result files are stored in project folder, in future we can move then to a CDN service, of course;
- Client can `GET /api/download/{TASK_ID}` to download the result;
- More processing requests can be done in any moment: the web-api is `asynchronous`, only the background worker is `synchronous` (one job per time).

## How to use

This project is designed to work with Docker. So, if you have it available in you machine, you need:

- Clone or download this repository;
- Navigate to its folder using terminal;
- Run this:
```shell
docker-compose up --build
```
For subsequent uses, you can run without the `--build` flag.

After the container is up and running, you can access the web-page at `http://localhost:8000/app`.

You can also use the API via terminal using curl or other HTTP engine, to the endpoints:

- `POST /api/submit/{youtube_video_id}`;
  - this will respond the real `task ID`;
  - example of command request: `curl -X POST http://localhost:8000/api/submit/vjVkXlxsO8Q`
  - example of response: `{"task_id":"9332b4ce-bb5b-4ecf-9457-e14581486223","status":"PENDING","error":null}`
- `GET /api/status/{task_id}`:
  - example of request: `curl.exe http://localhost:8000/api/status/9332b4ce-bb5b-4ecf-9457-e14581486223`
  - example of response: `{"task_id":"9332b4ce-bb5b-4ecf-9457-e14581486223","status":"SUCCESS","error":null}`
- `GET /api/download/{task_id}`. # TODO examples

When using the project via web-page (`/app`), it will handle those endpoints for you.

> Note 1: Spleeter library uses FFMPEG and some pretrained_models binaries to work, so it will consume more container space than usual.

> Note 2: Due to the large amount of dependencies, this docker container can take a while to become up to date.

> Note 3: is possible face low-memory problems depending on the host machine.

> Note 4: In my machine, Docker takes around 500 seconds to build up the containers.

## Project structure

From root project directory, we have:

- Dockerfile, dokcer-compose.yaml, pyproject.toml, uv.lock:
  - needed files to docker and to run the project;
- /server folder:
  - source of python code;
- /web_client:
  - here we keep the simple project of React+Vite, which generates a static web-page for us.

## Contributing

I am writing this project for real personal use, but it is a nice opportunity to keep evolving in programming. For this reason, I can be very bad in a lot of concepts related to this project, so any kind of contribution or feedback is welcome!