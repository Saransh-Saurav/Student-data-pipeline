import { useRef, useState } from "react";

export default function UploadPanel({ onUpload, loading, error }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);

  function handleFiles(files) {
    const file = files?.[0];
    if (file) onUpload(file);
  }

  return (
    <section className="card upload-panel">
      <h2>1. Upload raw student data</h2>
      <p className="muted">Accepts .csv or .xlsx. Cleaning runs automatically on upload.</p>
      <div
        className={`dropzone ${dragOver ? "dropzone-active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          hidden
          onChange={(e) => handleFiles(e.target.files)}
        />
        <p>{loading ? "Cleaning your data…" : "Click or drag a file here to upload"}</p>
      </div>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
