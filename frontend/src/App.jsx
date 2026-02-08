import { useMemo, useState } from "react";

const MAX_MB = 10;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];

const emptyResult = {
  request_id: "",
  top_predictions: [],
  model_version: "",
  latency_ms: 0,
  warnings: []
};

export default function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [result, setResult] = useState(emptyResult);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const isReady = Boolean(file) && status !== "loading";

  const onFileSelected = (selectedFile) => {
    setError("");
    setResult(emptyResult);

    if (!ACCEPTED_TYPES.includes(selectedFile.type)) {
      setError("Unsupported file type. Upload JPG, PNG, or WebP.");
      return;
    }

    const maxBytes = MAX_MB * 1024 * 1024;
    if (selectedFile.size > maxBytes) {
      setError("File is too large. Max size is 10MB.");
      return;
    }

    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
  };

  const handleDrop = (event) => {
    event.preventDefault();
    if (event.dataTransfer.files && event.dataTransfer.files[0]) {
      onFileSelected(event.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleIdentify = async () => {
    if (!file) return;
    setStatus("loading");
    setError("");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/identify", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload.detail || "Unable to identify the character.");
      }

      const data = await response.json();
      setResult(data);
      setStatus("success");
    } catch (err) {
      setError(err.message || "Backend timeout. Please try again.");
      setStatus("error");
    }
  };

  const predictions = useMemo(() => result.top_predictions || [], [result]);

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="badge">Character Identifier</p>
          <h1>Identify characters from any image.</h1>
          <p className="subtitle">
            Upload a screenshot, poster, or photo. We analyze visual signals like outfit,
            facial features, and context to estimate the most likely character.
          </p>
        </div>
      </header>

      <main>
        <section
          className={`upload-card ${status === "loading" ? "loading" : ""}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        >
          <div className="upload-info">
            <h2>Upload an image</h2>
            <p>Drag & drop a JPG, PNG, or WebP. Max {MAX_MB}MB.</p>
          </div>
          <label className="upload-action">
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) => {
                if (event.target.files && event.target.files[0]) {
                  onFileSelected(event.target.files[0]);
                }
              }}
            />
            <span>Choose file</span>
          </label>
          {previewUrl && (
            <div className="preview">
              <img src={previewUrl} alt="Upload preview" />
            </div>
          )}
          {error && <p className="error">{error}</p>}
          <button className="primary" disabled={!isReady} onClick={handleIdentify}>
            {status === "loading" ? "Analyzing..." : "Identify"}
          </button>
          {status === "loading" && (
            <div className="progress">
              <div className="spinner" />
              <span>Running inference and matching against the character gallery.</span>
            </div>
          )}
        </section>

        <section className="results">
          <div className="results-header">
            <h2>Results</h2>
            <span className="meta">Model: {result.model_version || "v1"}</span>
          </div>
          {predictions.length === 0 ? (
            <p className="muted">Upload an image to see predictions.</p>
          ) : (
            <div className="result-grid">
              {predictions.map((prediction) => (
                <div key={prediction.label} className="result-card">
                  <div className="result-title">
                    <h3>{prediction.label}</h3>
                    <span>{Math.round(prediction.confidence * 100)}%</span>
                  </div>
                  <p>{prediction.notes || "Signals detected in the image."}</p>
                  <div className="result-footer">
                    <span className="tag">{prediction.source}</span>
                    <span className="tag">Latency {result.latency_ms}ms</span>
                  </div>
                </div>
              ))}
            </div>
          )}
          {result.warnings?.includes("low_confidence") && (
            <div className="warning">
              Low confidence. Possible alternatives include {predictions
                .slice(1, 3)
                .map((prediction) => prediction.label)
                .join(", ") || "other matches"}.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
