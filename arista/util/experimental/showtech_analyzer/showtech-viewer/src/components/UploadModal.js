import React, { useRef, useState } from 'react';
import { uploadFiles } from '../utils/api';

export default function UploadModal({ onClose, onFilesProcessed }) {
  const fileInputRef = useRef(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);

  const handleChooseClick = () => fileInputRef.current?.click();

  const handleFileChange = (e) => {
    const newFiles = Array.from(e.target.files);
    if (newFiles.length) {
      setSelectedFiles((prev) => [...prev, ...newFiles]);
      setError('');
    }
    e.target.value = '';
  };

  const handleRemove = (idx) =>
    setSelectedFiles((prev) => prev.filter((_, i) => i !== idx));

  // Drag and drop handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set dragOver to false if we're leaving the drop zone entirely
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length) {
      setSelectedFiles((prev) => [...prev, ...droppedFiles]);
      setError('');
    }
  };

    const handleUpload = async () => {
    if (!selectedFiles.length) return;
    setIsUploading(true);
    setError('');

    try {
        const uploaded = await uploadFiles(selectedFiles); // ← helper uses API_ENDPOINT
        onFilesProcessed(uploaded);
        onClose();
    } catch (err) {
        console.error(err);
        setError(err.message);
    } finally {
        setIsUploading(false);
    }
    };


  return (
    <div className="upload-modal-backdrop">
      <div className="upload-modal">
        <h2>Upload Files</h2>
        <input
          type="file"
          multiple
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {/* Selected files list with drag and drop */}
        <div
          className={`upload-preview-box ${isDragOver ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {selectedFiles.length === 0 ? (
            <div className="drop-zone-content">
              <p className="placeholder-text">
                {isDragOver ? 'Drop files here' : 'No files selected'}
              </p>
              <p className="drop-zone-hint">
                Drag and drop files here or click Browse
              </p>
            </div>
          ) : (
            selectedFiles.map((file, idx) => (
              <div className="file-card" key={idx}>
                <span>{file.name}</span>
                <button
                  className="remove-icon"
                  onClick={() => handleRemove(idx)}
                  aria-label="Remove"
                >
                  &times;
                </button>
              </div>
            ))
          )}
        </div>

        {error && <p className="error-text">{error}</p>}

        {/* Footer buttons */}
        <div className="upload-footer">
        {/* Left-side cancel */}
        <button
            className="upload-button"
            onClick={onClose}
            disabled={isUploading}
        >
            Cancel
        </button>

        {/* Right-side Add + Upload */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button className="upload-button" onClick={handleChooseClick}>
            Browse
            </button>
            <button
            className="upload-button"
            onClick={handleUpload}
            disabled={isUploading || !selectedFiles.length}
            >
            {isUploading ? 'Uploading…' : 'Upload'}
            </button>
        </div>
        </div>
      </div>
    </div>
  );
}
