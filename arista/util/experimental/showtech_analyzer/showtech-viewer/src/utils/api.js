// src/utils/api.js
// This file contains the logic for communicating with the backend.

// Determine API endpoint based on environment
// In production (served by nginx), use relative path
// In development, use direct backend URL
const API_ENDPOINT = process.env.NODE_ENV === 'production'
  ? '/api'  // Relative path for nginx proxy
  : 'http://localhost:5001/api';  // Direct backend for development

export const checkBackendStatus = async () => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5001);

  try {
    const res = await fetch(`${API_ENDPOINT}/status`, { signal: controller.signal });
    clearTimeout(timeout);
    if (!res.ok) throw new Error('Network response was not ok');
    return await res.json();
  } catch (err) {
    console.error(err.name === 'AbortError' ? 'Fetch timed out' : 'API fetch error:', err);
    throw err;
  }
};


// Calls the function that processes the file and returns it to the front end
export const uploadFiles = async (filesArray) => {
  const formData = new FormData();
  filesArray.forEach((file) => formData.append('file', file));

  const res = await fetch(`${API_ENDPOINT}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    let errorMessage = 'Upload failed';
    try {
      const errorData = await res.json();
      if (errorData.error === 'No files could be processed' && errorData.details) {
        // Extract the actual error messages from the details
        const errorMessages = errorData.details.map(detail => {
          // Extract the message after the filename
          const match = detail.match(/File '.*?': (.+)/);
          return match ? match[1] : detail;
        });
        errorMessage = errorMessages.join('\n');
      } else {
        errorMessage = errorData.error || 'Upload failed';
      }
    } catch (parseError) {
      // If JSON parsing fails, use status text
      errorMessage = `Upload failed: ${res.statusText}`;
    }
    throw new Error(errorMessage);
  }
  return res.json();
};

// Upload files with progress tracking - processes files individually
export const uploadFilesWithProgress = async (filesArray, onProgress) => {
  const allResults = [];
  const totalFiles = filesArray.length;

  for (let i = 0; i < filesArray.length; i++) {
    const file = filesArray[i];
    const currentFileNum = i + 1;

    // Update progress
    if (onProgress) {
      onProgress({
        currentFile: currentFileNum,
        totalFiles: totalFiles,
        fileName: file.name,
        percent: Math.round((i / totalFiles) * 100)
      });
    }

    // Upload single file
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_ENDPOINT}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      let errorMessage = `Upload failed for ${file.name}`;
      try {
        const errorData = await res.json();
        if (errorData.error === 'No files could be processed' && errorData.details) {
          // Extract the actual error messages from the details
          const errorMessages = errorData.details.map(detail => {
            // Extract the message after the filename
            const match = detail.match(/File '.*?': (.+)/);
            return match ? match[1] : detail;
          });
          errorMessage = `${file.name}: ${errorMessages.join(', ')}`;
        } else {
          errorMessage = `${file.name}: ${errorData.error || 'Upload failed'}`;
        }
      } catch (parseError) {
        // If JSON parsing fails, use status text
        errorMessage = `Upload failed for ${file.name}: ${res.statusText}`;
      }
      throw new Error(errorMessage);
    }

    const result = await res.json();
    allResults.push(...result);
  }

  // Final progress update
  if (onProgress) {
    onProgress({
      currentFile: totalFiles,
      totalFiles: totalFiles,
      fileName: 'Complete',
      percent: 100
    });
  }

  return allResults;
};