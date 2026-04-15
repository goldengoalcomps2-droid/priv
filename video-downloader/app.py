import os
import uuid
import threading
import subprocess
import sys
import re
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response

app = Flask(__name__)


@app.after_request
def add_pwa_headers(response):
    """Add headers required for PWA features."""
    if request.path == "/static/sw.js":
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
    return response

# Downloads folder - always use local ./downloads on server
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Track active downloads
downloads = {}

# Auto-cleanup: delete files older than 10 minutes
CLEANUP_AFTER_SECONDS = 600


def cleanup_old_files():
    """Remove downloaded files older than CLEANUP_AFTER_SECONDS."""
    while True:
        time.sleep(60)
        try:
            now = time.time()
            if DOWNLOAD_DIR.exists():
                for f in DOWNLOAD_DIR.iterdir():
                    if f.is_file() and not f.name.startswith("."):
                        age = now - f.stat().st_mtime
                        if age > CLEANUP_AFTER_SECONDS:
                            f.unlink(missing_ok=True)
            # Clean old download records too
            stale = [
                k for k, v in downloads.items()
                if v.get("_created", 0) < now - CLEANUP_AFTER_SECONDS
            ]
            for k in stale:
                downloads.pop(k, None)
        except Exception:
            pass


# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()


def get_yt_dlp_path():
    """Find yt-dlp executable."""
    for cmd in ["yt-dlp", "yt_dlp"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return cmd
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    try:
        subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            capture_output=True,
            check=True,
        )
        return [sys.executable, "-m", "yt_dlp"]
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def parse_progress(line):
    """Parse yt-dlp output for progress info."""
    progress = {}
    if "[download]" in line:
        pct_match = re.search(r"(\d+\.?\d*)%", line)
        if pct_match:
            progress["percent"] = float(pct_match.group(1))
        speed_match = re.search(r"at\s+([\d.]+\w+/s)", line)
        if speed_match:
            progress["speed"] = speed_match.group(1)
        eta_match = re.search(r"ETA\s+([\d:]+)", line)
        if eta_match:
            progress["eta"] = eta_match.group(1)
        size_match = re.search(r"of\s+~?([\d.]+\w+)", line)
        if size_match:
            progress["size"] = size_match.group(1)
    return progress


def download_video(download_id, url, quality, format_type):
    """Run yt-dlp download in background thread."""
    yt_dlp = get_yt_dlp_path()
    if not yt_dlp:
        downloads[download_id]["status"] = "error"
        downloads[download_id]["error"] = "yt-dlp not installed on server."
        return

    cmd = yt_dlp if isinstance(yt_dlp, list) else [yt_dlp]

    # Use unique prefix to avoid filename collisions between users
    prefix = download_id + "_"
    args = cmd + [
        "--no-playlist",
        "--newline",
        "--progress",
        "--max-filesize", "500m",
        "-o",
        str(DOWNLOAD_DIR / (prefix + "%(title)s.%(ext)s")),
    ]

    if quality == "best":
        args += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]
    elif quality == "1080":
        args += ["-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best"]
    elif quality == "720":
        args += ["-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"]
    elif quality == "480":
        args += ["-f", "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best"]
    elif quality == "audio":
        args += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]

    if format_type == "mp4" and quality != "audio":
        args += ["--merge-output-format", "mp4"]

    args.append(url)

    downloads[download_id]["status"] = "downloading"

    try:
        process = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        downloads[download_id]["pid"] = process.pid

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            downloads[download_id]["log"].append(line)

            progress = parse_progress(line)
            if progress:
                downloads[download_id].update(progress)

            if "[download] Destination:" in line:
                filename = line.split("Destination:")[-1].strip()
                downloads[download_id]["filename"] = os.path.basename(filename)

            if "has already been downloaded" in line:
                match = re.search(r"\[download\]\s+(.+)\s+has already", line)
                if match:
                    downloads[download_id]["filename"] = os.path.basename(
                        match.group(1)
                    )
                downloads[download_id]["percent"] = 100

            if "[Merger]" in line or "[ExtractAudio]" in line:
                merge_match = re.search(r'Merging formats into "(.+)"', line)
                if merge_match:
                    downloads[download_id]["filename"] = os.path.basename(
                        merge_match.group(1)
                    )

        process.wait()

        if process.returncode == 0:
            downloads[download_id]["status"] = "complete"
            downloads[download_id]["percent"] = 100
            if not downloads[download_id].get("filename"):
                # Find most recent file with our prefix
                matching = [
                    f for f in DOWNLOAD_DIR.iterdir()
                    if f.is_file() and f.name.startswith(prefix)
                ]
                if matching:
                    recent = max(matching, key=lambda p: p.stat().st_mtime)
                    downloads[download_id]["filename"] = recent.name
        else:
            downloads[download_id]["status"] = "error"
            downloads[download_id]["error"] = "Download failed. Check the URL is valid."

    except Exception as e:
        downloads[download_id]["status"] = "error"
        downloads[download_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    quality = data.get("quality", "best")
    format_type = data.get("format", "mp4")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "Invalid URL. Must start with http:// or https://"}), 400

    download_id = str(uuid.uuid4())[:8]
    downloads[download_id] = {
        "id": download_id,
        "url": url,
        "status": "starting",
        "percent": 0,
        "speed": "",
        "eta": "",
        "size": "",
        "filename": "",
        "error": "",
        "log": [],
        "_created": time.time(),
    }

    thread = threading.Thread(
        target=download_video, args=(download_id, url, quality, format_type)
    )
    thread.daemon = True
    thread.start()

    return jsonify({"id": download_id})


@app.route("/status/<download_id>")
def get_status(download_id):
    if download_id not in downloads:
        return jsonify({"error": "Not found"}), 404
    info = downloads[download_id].copy()
    info.pop("log", None)
    info.pop("command", None)
    info.pop("pid", None)
    info.pop("_created", None)
    return jsonify(info)


@app.route("/file/<filename>")
def serve_file(filename):
    return send_from_directory(str(DOWNLOAD_DIR), filename, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  Video Downloader is running!")
    print(f"  Open: http://localhost:{port}\n")
    app.run(debug=False, host="0.0.0.0", port=port)
