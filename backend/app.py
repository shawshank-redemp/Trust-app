from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import cv2
import hashlib
import subprocess
import tempfile

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "videos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

video_hashes = []
audio_hashes = []

def get_video_hash(video_path):
    cap = cv2.VideoCapture(video_path)
    hashes = []
    count = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        if count % 30 == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            small = cv2.resize(gray, (32, 32))
            hashes.append(hashlib.md5(small.tobytes()).hexdigest())

        count += 1
        if len(hashes) >= 5:
            break

    cap.release()
    return "".join(hashes)

def get_audio_hash(video_path):
    try:
        temp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

        command = [
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            temp_audio.name,
            "-y"
        ]

        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with open(temp_audio.name, "rb") as f:
            audio_bytes = f.read()

        return hashlib.md5(audio_bytes).hexdigest()
    except:
        return None
@app.route("/upload", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    file = request.files["video"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    v_hash = get_video_hash(filepath)
    a_hash = get_audio_hash(filepath)

    # ✅ First upload should always be original
    if len(video_hashes) == 0 and len(audio_hashes) == 0:
        video_hashes.append(v_hash)
        audio_hashes.append(a_hash)

        return jsonify({
            "score": 90,
            "reasons": ["Original content"]
        })

    score = 90
    reasons = []

    video_match = 0
    audio_match = 0

    for h in video_hashes:
        if h == v_hash:
            video_match += 1

    for h in audio_hashes:
        if h == a_hash:
            audio_match += 1

    if audio_match >= 1:
        if video_match >= 1:
            score = 30
            reasons.append("Same audio + same visuals (mass-produced)")
        else:
            score = 85
            reasons.append("Same audio but different content (real performance)")
    elif video_match >= 1:
        score = 50
        reasons.append("Similar video detected")
    else:
        score = 90
        reasons.append("Original content")

    video_hashes.append(v_hash)
    audio_hashes.append(a_hash)

    return jsonify({
        "score": score,
        "reasons": reasons
    })

if __name__ == "__main__":
    app.run(debug=True)