from flask import Flask, request, jsonify, send_file
import os
import yt_dlp
import tempfile

app = Flask(__name__)

def download_youtube_mp3(url: str) -> str:
    """Pobiera audio z YouTube i konwertuje do MP3, zwraca ścieżkę pliku."""
    temp_dir = tempfile.mkdtemp()
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        mp3_file = os.path.splitext(filename)[0] + ".mp3"
        return mp3_file

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"success": False, "error": "Brak linku"}), 400

    try:
        mp3_file = download_youtube_mp3(url)
        return send_file(mp3_file, as_attachment=True)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=8000)