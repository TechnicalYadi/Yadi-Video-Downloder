from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import threading
from datetime import timedelta

app = Flask(__name__)

progress_data = {
    "progress": "0%",
    "speed": "0 KB/s",
    "eta": "0s",
    "status": "idle",
    "title": "",
    "filesize": "",
    "duration": ""
}

DOWNLOAD_FOLDER = os.path.join(os.getcwd(), "downloads")
COOKIE_PATH = r"C:\Users\champ\Downloads\video_downloader\hotstar_cookies.txt"  # ✅ your path

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


# ---- Progress Hook ----
def progress_hook(d):
    if d['status'] == 'downloading':
        progress_data['progress'] = d.get('_percent_str', '').strip()
        progress_data['speed'] = d.get('_speed_str', '0 KB/s').strip()

        eta_str = d.get('_eta_str', '0')
        try:
            seconds = int(eta_str.replace('s', ''))
            progress_data['eta'] = str(timedelta(seconds=seconds))
        except:
            progress_data['eta'] = eta_str

        progress_data['status'] = 'downloading'
    elif d['status'] == 'finished':
        progress_data['status'] = 'done'


# ---- Get video info ----
def get_video_info(url):
    ydl_opts = {'quiet': True}
    if "hotstar.com" in url:
        ydl_opts['cookiefile'] = COOKIE_PATH

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []
        for f in info.get('formats', []):
            if f.get('height'):
                size = f.get('filesize') or f.get('filesize_approx')
                size_str = f"{round(size / (1024*1024), 2)} MB" if size else "?"
                formats.append({
                    "id": f['format_id'],
                    "res": f"{f.get('height')}p",
                    "size": size_str,
                    "ext": f.get('ext', '')
                })
        return {
            "title": info.get('title', 'Unknown'),
            "duration": round(info.get('duration', 0) / 60, 2),
            "formats": formats
        }


# ---- Download thread ----
def start_download(url, format_id):
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'merge_output_format': 'mp4',  # ✅ combine audio + video
        'format': f'{format_id}+bestaudio/best',
        'noplaylist': True
    }

    if "hotstar.com" in url:
        ydl_opts['cookiefile'] = COOKIE_PATH

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            filesize = info.get('filesize_approx', 0)
            duration = info.get('duration', 0)
            progress_data.update({
                "status": "done",
                "title": title,
                "filesize": f"{round(filesize / (1024*1024), 2)} MB" if filesize else "Unknown",
                "duration": f"{round(duration / 60, 2)} min" if duration else "Unknown"
            })
    except Exception as e:
        progress_data['status'] = f"error: {str(e)}"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/info', methods=['POST'])
def info():
    url = request.form['url']
    try:
        info = get_video_info(url)
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    format_id = request.form['format_id']
    thread = threading.Thread(target=start_download, args=(url, format_id))
    thread.start()
    return jsonify({"message": "Download started"})


@app.route('/progress')
def progress():
    return jsonify(progress_data)


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
