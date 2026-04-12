import os
import json
import uuid
import threading
import subprocess
import sys
import re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)

# Downloads folder - saves to user's Downloads or fallback to local ./downloads
HOME_DOWNLOADS = Path.home() / "Downloads" / "VideoDownloader"
LOCAL_DOWNLOADS = Path(__file__).parent / "downloads"
DOWNLOAD_DIR = HOME_DOWNLOADS if HOME_DOWNLOADS.parent.exists() else LOCAL_DOWNLOADS
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Track active downloads
downloads = {}


def get_yt_dlp_path():
    """Find yt-dlp executable."""
    for cmd in ["yt-dlp", "yt_dlp"]:
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True)
            return cmd
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    # Try running as Python module
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
        # Match percentage
        pct_match = re.search(r"(\d+\.?\d*)%", line)
        if pct_match:
            progress["percent"] = float(pct_match.group(1))
        # Match speed
        speed_match = re.search(r"at\s+([\d.]+\w+/s)", line)
        if speed_match:
            progress["speed"] = speed_match.group(1)
        # Match ETA
        eta_match = re.search(r"ETA\s+([\d:]+)", line)
        if eta_match:
            progress["eta"] = eta_match.group(1)
        # Match size
        size_match = re.search(r"of\s+~?([\d.]+\w+)", line)
        if size_match:
            progress["size"] = size_match.group(1)
    return progress


def download_video(download_id, url, quality, format_type):
    """Run yt-dlp download in background thread."""
    yt_dlp = get_yt_dlp_path()
    if not yt_dlp:
        downloads[download_id]["status"] = "error"
        downloads[download_id]["error"] = (
            "yt-dlp not found. Run: pip install yt-dlp"
        )
        return

    cmd = yt_dlp if isinstance(yt_dlp, list) else [yt_dlp]

    # Build command
    args = cmd + [
        "--no-playlist",
        "--newline",
        "--progress",
        "-o",
        str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
    ]

    # Quality settings
    if quality == "best":
        args += ["-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"]
    elif quality == "1080":
        args += [
            "-f",
            "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        ]
    elif quality == "720":
        args += [
            "-f",
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
        ]
    elif quality == "480":
        args += [
            "-f",
            "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best",
        ]
    elif quality == "audio":
        args += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]

    # Format type
    if format_type == "mp4" and quality != "audio":
        args += ["--merge-output-format", "mp4"]

    args.append(url)

    downloads[download_id]["status"] = "downloading"
    downloads[download_id]["command"] = " ".join(args)

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

            # Parse progress
            progress = parse_progress(line)
            if progress:
                downloads[download_id].update(progress)

            # Capture title
            if "[download] Destination:" in line:
                filename = line.split("Destination:")[-1].strip()
                downloads[download_id]["filename"] = os.path.basename(filename)

            # Already downloaded
            if "has already been downloaded" in line:
                match = re.search(r"\[download\]\s+(.+)\s+has already", line)
                if match:
                    downloads[download_id]["filename"] = os.path.basename(
                        match.group(1)
                    )
                downloads[download_id]["percent"] = 100

            # Merging
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
            # Try to find the file if filename wasn't captured
            if not downloads[download_id].get("filename"):
                recent = max(
                    DOWNLOAD_DIR.iterdir(), key=lambda p: p.stat().st_mtime
                )
                downloads[download_id]["filename"] = recent.name
        else:
            downloads[download_id]["status"] = "error"
            downloads[download_id]["error"] = "Download failed. Check the URL."

    except Exception as e:
        downloads[download_id]["status"] = "error"
        downloads[download_id]["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html", download_dir=str(DOWNLOAD_DIR))


@app.route("/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    quality = data.get("quality", "best")
    format_type = data.get("format", "mp4")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

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
    return jsonify(info)


@app.route("/history")
def history():
    files = []
    if DOWNLOAD_DIR.exists():
        for f in sorted(
            DOWNLOAD_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        ):
            if f.is_file() and not f.name.startswith("."):
                stat = f.stat()
                size_mb = stat.st_size / (1024 * 1024)
                files.append(
                    {
                        "name": f.name,
                        "size": f"{size_mb:.1f} MB",
                        "size_bytes": stat.st_size,
                    }
                )
    return jsonify(files)


@app.route("/file/<filename>")
def serve_file(filename):
    return send_from_directory(str(DOWNLOAD_DIR), filename, as_attachment=True)


@app.route("/open-folder")
def open_folder():
    folder = str(DOWNLOAD_DIR)
    try:
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print(f"\n  Video Downloader is running!")
    print(f"  Open: http://localhost:5000")
    print(f"  Downloads saved to: {DOWNLOAD_DIR}\n")
    app.run(debug=False, port=5000)
