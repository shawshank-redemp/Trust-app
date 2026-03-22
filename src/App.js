import React, { useState } from "react";

export default function App() {
  const [video, setVideo] = useState(null);
  const [preview, setPreview] = useState(null);
  const [score, setScore] = useState(null);
  const [reasons, setReasons] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideo(file);
      setPreview(URL.createObjectURL(file));
      setScore(null);
      setReasons([]);
    }
  };

  const analyzeVideo = async () => {
  if (!video) return;

  setLoading(true);

  const formData = new FormData();
  formData.append("video", video);

  try {
    const res = await fetch("http://127.0.0.1:5000/upload", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    setScore(data.score);
    setReasons(data.reasons);
  } catch (error) {
    console.error("Error:", error);
  }

  setLoading(false);
};

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f3f4f6", padding: "20px" }}>
      <div style={{ background: "white", padding: "20px", borderRadius: "10px", width: "400px" }}>
        
        <h1 style={{ textAlign: "center" }}>
          Trust-Based Video Analyzer
        </h1>

        <input
          type="file"
          accept="video/*"
          onChange={handleUpload}
          style={{ width: "100%", marginTop: "10px" }}
        />

        {preview && (
          <video
            src={preview}
            controls
            style={{ width: "100%", marginTop: "10px" }}
          />
        )}

        <button
          onClick={analyzeVideo}
          disabled={loading}
          style={{ width: "100%", marginTop: "10px", padding: "10px", background: "blue", color: "white", border: "none", borderRadius: "5px" }}
        >
          {loading ? "Analyzing..." : "Analyze Video"}
        </button>

        {score !== null && (
          <div style={{ marginTop: "15px" }}>
            <h2>Trust Score: {score}%</h2>

            <div style={{ width: "100%", background: "#ddd", height: "10px" }}>
              <div style={{ width: `${score}%`, background: "green", height: "10px" }}></div>
            </div>

            <div>
              <h3>Reasons:</h3>
              <ul>
                {reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}