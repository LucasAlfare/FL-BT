```
███████╗██╗                   ██████╗ ████████╗
██╔════╝██║                   ██╔══██╗╚══██╔══╝
█████╗  ██║         █████╗    ██████╔╝   ██║   
██╔══╝  ██║         ╚════╝    ██╔══██╗   ██║   
██║     ███████╗              ██████╔╝   ██║   
╚═╝     ╚══════╝              ╚═════╝    ╚═╝   
```

This project is a totally free simple wrapper that lets you **separate audio tracks from YouTube videos** using [Spleeter](https://github.com/deezer/spleeter). It works as a **local API server** with a basic desktop client. The goal is to make it easy—even for non-programmers—to split a song into separate audio components (vocals, drums, bass, others).

---

## 🔧 How It Works

1. **You provide a YouTube video URL.**
2. The backend downloads the video and processes the audio using Spleeter (4-stem model).
3. The result is a `.zip` file with the following separate tracks:
   - vocals
   - drums
   - bass
   - other (all remaining sounds)

---

## 🧩 API Overview

After starting the server:

- `GET /api/request/{video_id}`  
  Queues the YouTube video for processing.

- `GET /api/status/{video_id}`  
  Returns the processing status: `pending`, `processing`, `success`, or `error`.

- `GET /api/download/{video_id}`  
  When status is `success`, downloads a `.zip` with the extracted stems.

> Replace `{video_id}` with the actual YouTube video ID (e.g., `dQw4w9WgXcQ`).

---

## 🚀 How to Run

Is possible to run the python FastAPI by itself after installing the [`requirements.txt`](server/requirements.txt). But for this, you need to get `FFMPEG` manually for your operating system, because Spleeter uses it. To skip this, read Docker instructions below. 

### Requirements
- Windows
- [Docker](https://www.docker.com/)

If you want to use with the Docker and with the simple client you'll need to build the client to it become accessible from the starter script:
- [Java JDK 17+](https://adoptium.net/)
- [Gradle](https://gradle.org/) (or use the wrapper)

### 1. Build and Start Everything
Run `start.bat` (Windows only). It:
- Builds and starts the API in Docker
- Launches the desktop client

### 2. Build the Desktop Client (Only Once)

Navigate to the `desktop_client` folder and run:  
```bash
./gradlew packageReleaseUberJarForCurrentOS
```

It creates the JAR at:  
```text
desktop_client/app/build/compose/jars/FLBTClient-windows-x64-1.0.0-release.jar
```

This JAR will be used by the `start.bat` script.

---

## 📠 Using the project

If using the simple client, just paste YouTube video IDs, one per line, at the top text area, then click the button to request processing for all IDs. If using only API, look API reference.

---

## ⚠️ Limitations

- **No error handling** for failed downloads, network issues, or parallel requests.
- **Not optimized** for low-performance machines (especially low-end VPS).
- **Still experimental**—not production-ready.
- **Local usage**—for now, designed to be used locally, at home.

---

## 🐍 Python Compatibility

- Requires **Python 3.10**, due to current Spleeter version requirements.

---

## 📦 Technologies Used

- Python + FastAPI (backend)
- Spleeter (audio separation)
- Docker
- Kotlin Desktop Compose (client)

---

## 💡 Future Ideas

- Improve deploy/distribution process;
- Make more possible to run externally (VPS, etc).