import { useRef, useState } from "react";
import SectionHeader from "./SectionHeader.jsx";
import Icon from "./Icon.jsx";

export default function UploadPanel({ onUpload, loading, error }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [fileName, setFileName] = useState(null);

  function handleFiles(files) {
    const file = files?.[0];
    if (file) {
      setFileName(file.name);
      onUpload(file);
    }
  }

  return (
    <section className="card upload-panel">
      <SectionHeader step={1} title="Upload raw student data" subtitle="Accepts .csv or .xlsx — cleaning runs automatically on upload." />
      <div
        className={`dropzone ${dragOver ? "dropzone-active" : ""} ${loading ? "dropzone-loading" : ""}`}
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
        <div className={`dropzone-icon ${loading ? "spin" : ""}`}>
          <Icon name="upload" size={26} />
        </div>
        {loading ? (
          <p className="dropzone-title">Cleaning your data…</p>
        ) : (
          <>
            <p className="dropzone-title">Click or drag a file here to upload</p>
            {fileName && <p className="dropzone-filename">Last file: {fileName}</p>}
          </>
        )}
      </div>
      {error && (
        <p className="error">
          <Icon name="alert" size={14} /> {error}
        </p>
      )}
    </section>
  );
}
