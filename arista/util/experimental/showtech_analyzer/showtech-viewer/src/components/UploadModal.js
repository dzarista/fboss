import React, { useRef, useState } from 'react';
import { uploadFiles, uploadFilesWithProgress, unrollZips } from '../utils/api';

export default function UploadModal({ onClose, onFilesProcessed }) {
  const fileInputRef = useRef(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState('');
  const [progressPercent, setProgressPercent] = useState(0);
  const [currentFile, setCurrentFile] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);
  const [error, setError] = useState('');
  const [isWarning, setIsWarning] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleChooseClick = () => fileInputRef.current?.click();

  // Check if a file is likely a showtech file or ZIP
  const isValidFile = (file) => {
    const name = file.name.toLowerCase();
    const isZip = name.endsWith('.zip');
    const isText = name.endsWith('.txt') || name.endsWith('.log') || !name.includes('.');
    const hasShowtechKeywords = name.includes('showtech') || name.includes('show-tech') ||
                                name.includes('support') || name.includes('debug');

    // Accept ZIP files or text files that might be showtech files
    return isZip || isText || hasShowtechKeywords;
  };



  const addFilesWithoutDuplicates = (newFiles) => {
    setSelectedFiles((prev) => {
      const existingNames = new Set(prev.map(file => file.name));

      // Filter for valid files first, then remove duplicates
      const validFiles = newFiles.filter(file => isValidFile(file));
      const uniqueFiles = validFiles.filter(file => !existingNames.has(file.name));

      const duplicateCount = validFiles.length - uniqueFiles.length;
      const invalidCount = newFiles.length - validFiles.length;

      // Show feedback for filtered files
      let messages = [];
      if (invalidCount > 0) {
        messages.push(`${invalidCount} non-showtech file${invalidCount !== 1 ? 's' : ''} were skipped`);
      }
      if (duplicateCount > 0) {
        messages.push(`${duplicateCount} duplicate file${duplicateCount !== 1 ? 's' : ''} were skipped`);
      }

      if (messages.length > 0) {
        setError(messages.join(', '));
        setIsWarning(true);
        // Clear the message after 4 seconds
        setTimeout(() => {
          setError('');
          setIsWarning(false);
        }, 4000);
      }

      return [...prev, ...uniqueFiles];
    });
  };

  const handleFileChange = (e) => {
    const newFiles = Array.from(e.target.files);
    if (newFiles.length) {
      addFilesWithoutDuplicates(newFiles);
      // Only clear error if it's not a warning (duplicate message)
      if (!isWarning) {
        setError('');
      }
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
      addFilesWithoutDuplicates(droppedFiles);
      // Only clear error if it's not a warning (duplicate message)
      if (!isWarning) {
        setError('');
      }
    }
  };

    const handleUpload = async () => {
    if (!selectedFiles.length) return;
    setIsUploading(true);
    setError('');
    setIsWarning(false);
    setProgressPercent(0);
    setCurrentFile(0);
    setTotalFiles(selectedFiles.length);

    try {
        const hasZipFiles = selectedFiles.some(file => file.name.toLowerCase().endsWith('.zip'));

        // Step 1: If there are zip files, unroll them first
        let filesToProcess = [...selectedFiles];

        if (hasZipFiles) {
          setUploadProgress('Extracting zip files...');

          const unrollResult = await unrollZips(selectedFiles);

          // Remove zip files from the list
          filesToProcess = filesToProcess.filter(file =>
            !unrollResult.files_to_remove.includes(file.name)
          );

          // Add individual files from zips
          const extractedFiles = unrollResult.files_to_add.map(fileInfo => {
            // Create a File-like object from the extracted content
            const blob = new Blob([fileInfo.content], { type: 'text/plain' });
            const file = new File([blob], fileInfo.name, { type: 'text/plain' });
            file.extracted_from = fileInfo.extracted_from;
            return file;
          });

          filesToProcess.push(...extractedFiles);

          // Update the selected files list to show extracted files
          setSelectedFiles(filesToProcess);
          setTotalFiles(filesToProcess.length);
        }

        // Step 2: Process all individual files
        if (filesToProcess.length > 1) {
          const uploaded = await uploadFilesWithProgress(filesToProcess, (progress) => {
            setCurrentFile(progress.currentFile);
            setTotalFiles(progress.totalFiles);
            setProgressPercent(progress.percent);

            if (progress.fileName === 'Complete') {
              setUploadProgress('Upload complete!');
            } else if (progress.fileName === 'No valid files found') {
              setUploadProgress('No valid showtech files found');
            } else {
              setUploadProgress(`Processing ${progress.fileName}... (${progress.currentFile} of ${progress.totalFiles} files)`);
            }
          });

          // Brief completion message before closing
          setTimeout(() => {
            if (uploaded && uploaded.length > 0) {
              onFilesProcessed(uploaded);
            }
            onClose();
          }, 800);

        } else {
          // Single file - use simpler progress
          setUploadProgress('Processing file...');
          const uploaded = await uploadFiles(filesToProcess);

          // Check if any files were actually processed
          if (uploaded && uploaded.length > 0) {
            setUploadProgress('Upload complete!');
            setTimeout(() => {
              onFilesProcessed(uploaded);
              onClose();
            }, 500);
          } else {
            // No valid showtech files found - just close quietly
            setUploadProgress('No valid showtech files found');
            setTimeout(() => {
              onClose();
            }, 1000);
          }
        }

    } catch (err) {
        console.error(err);
        setError(err.message);
        setIsWarning(false); // Real errors are not warnings
        setUploadProgress('');
        setProgressPercent(0);
        setCurrentFile(0);
        setTotalFiles(0);
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
          accept=".txt,.log,.zip"
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
                Drag and drop showtech files or ZIP archives here, or click Browse
              </p>
            </div>
          ) : (
            selectedFiles.map((file, idx) => {
              const isZip = file.name.toLowerCase().endsWith('.zip');
              return (
                <div className="file-card" key={idx}>
                  <div className="file-info">
                    <span className="file-name">{file.name}</span>
                    {isZip && <span className="file-type-badge">ZIP</span>}
                  </div>
                  <button
                    className="remove-icon"
                    onClick={() => handleRemove(idx)}
                    aria-label="Remove"
                    disabled={isUploading}
                  >
                    &times;
                  </button>
                </div>
              );
            })
          )}
        </div>

        {error && <p className={isWarning ? "warning-text" : "error-text"}>{error}</p>}
        {isUploading && uploadProgress && (
          <div className="upload-progress">
            <div className="upload-spinner"></div>
            <div className="progress-content">
              <p className="progress-text">{uploadProgress}</p>
              {totalFiles > 1 && (
                <div className="progress-bar-container">
                  <div className="progress-bar">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${progressPercent}%` }}
                    ></div>
                  </div>
                  <span className="progress-percentage">{progressPercent}%</span>
                </div>
              )}
            </div>
          </div>
        )}

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
            <button
              className="upload-button"
              onClick={handleChooseClick}
              disabled={isUploading}
            >
              Browse
            </button>
            <button
              className="upload-button"
              onClick={handleUpload}
              disabled={isUploading || !selectedFiles.length}
            >
              {isUploading ? 'Processing…' : 'Upload'}
            </button>
        </div>
        </div>
      </div>
    </div>
  );
}