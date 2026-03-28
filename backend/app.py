from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import os
import uuid
import subprocess
import tempfile
import librosa
import mediapipe as mp
from scipy.spatial.distance import cosine

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "videos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

video_db = []

mp_pose = mp.solutions.pose
pose_detector = mp_pose.Pose()

# ================= AUDIO =================
def extract_audio_wav(video_path):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

    cmd = [
        r"C:\Users\LENOVO\AppData\Roaming\Python\Python312\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe",
        "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "22050", "-ac", "1",
        tmp.name, "-y"
    ]

    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    if result.returncode != 0:
        return None

    return tmp.name


def get_audio_features(video_path):
    wav_path = extract_audio_wav(video_path)
    if wav_path is None:
        return None

    y, sr = librosa.load(wav_path, sr=22050, duration=3)
    os.unlink(wav_path)

    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    return np.mean(mfcc, axis=1)


# ================= POSE =================
def get_pose_features(video_path):
    cap = cv2.VideoCapture(video_path)
    poses = []

    while cap.isOpened() and len(poses) < 50:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose_detector.process(rgb)

        if result.pose_landmarks:
            coords = []
            for lm in result.pose_landmarks.landmark[:15]:
                coords.extend([lm.x, lm.y])
            poses.append(coords)

    cap.release()

    if len(poses) < 5:
        return None

    return np.array(poses)


def get_motion_summary(poses):
    if poses is None:
        return None

    return np.mean(poses, axis=0)


# ================= SIMILARITY =================
def cosine_similarity(a, b):
    if a is None or b is None:
        return 0
    return (1 - cosine(a, b)) * 100


# ================= ROUTE =================
@app.route("/upload", methods=["POST"])
def upload_video():
    file = request.files["video"]

    filename = str(uuid.uuid4()) + ".mp4"
    path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(path)

    audio = get_audio_features(path)
    poses = get_pose_features(path)
    motion = get_motion_summary(poses)

    if len(video_db) == 0:
        video_db.append({"audio": audio, "motion": motion})
        return jsonify({
            "trust_score": 100,
            "result": "First video stored",
            "reasons": ["Baseline video"]
        })

    best_audio = 0
    best_motion = 0

    for v in video_db:
        best_audio = max(best_audio, cosine_similarity(audio, v["audio"]))
        best_motion = max(best_motion, cosine_similarity(motion, v["motion"]))

    video_db.append({"audio": audio, "motion": motion})

    if best_audio > 80 and best_motion > 70:
        return jsonify({
            "trust_score": 30,
            "result": "Similar emotional pattern detected",
            "reasons": ["Same audio + same motion"]
        })

    return jsonify({
        "trust_score": 90,
        "result": "Original content",
        "reasons": ["No similarity detected"]
    })


if __name__ == "__main__":
    app.run(debug=True)