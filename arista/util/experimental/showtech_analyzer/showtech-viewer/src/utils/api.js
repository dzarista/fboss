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

// Count total files that will be processed (including files within zip archives)
export const countFiles = async (filesArray) => {
  const formData = new FormData();
  filesArray.forEach((file) => formData.append('file', file));

  const res = await fetch(`${API_ENDPOINT}/count-files`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Failed to count files: ${res.statusText}`);
  }

  return res.json();
};

// Unroll zip files and get individual file information
export const unrollZips = async (filesArray) => {
  const formData = new FormData();
  filesArray.forEach((file) => formData.append('file', file));

  const res = await fetch(`${API_ENDPOINT}/unroll-zips`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Failed to unroll zips: ${res.statusText}`);
  }

  return res.json();
};

// Upload files with progress tracking - accounts for individual files in zip archives
export const uploadFilesWithProgress = async (filesArray, onProgress) => {
  // First, count total files to be processed
  const countResult = await countFiles(filesArray);
  const totalFilesToProcess = countResult.total_count;

  if (totalFilesToProcess === 0) {
    if (onProgress) {
      onProgress({
        currentFile: 0,
        totalFiles: 0,
        fileName: 'No valid files found',
        percent: 100
      });
    }
    return [];
  }

  const allResults = [];
  let processedFiles = 0;

  for (let i = 0; i < filesArray.length; i++) {
    const file = filesArray[i];

    // Update progress at start of file processing
    if (onProgress) {
      onProgress({
        currentFile: processedFiles,
        totalFiles: totalFilesToProcess,
        fileName: file.name,
        percent: Math.round((processedFiles / totalFilesToProcess) * 100)
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
        errorMessage = `${file.name}: ${errorData.error || 'Upload failed'}`;
      } catch (parseError) {
        errorMessage = `Upload failed for ${file.name}: ${res.statusText}`;
      }
      throw new Error(errorMessage);
    }

    const result = await res.json();
    allResults.push(...result);

    // Update processed files count based on how many files were actually processed
    processedFiles += result.length;

    // Update progress after processing
    if (onProgress) {
      onProgress({
        currentFile: processedFiles,
        totalFiles: totalFilesToProcess,
        fileName: file.name,
        percent: Math.round((processedFiles / totalFilesToProcess) * 100)
      });
    }
  }

  // Final progress update
  if (onProgress) {
    onProgress({
      currentFile: totalFilesToProcess,
      totalFiles: totalFilesToProcess,
      fileName: 'Complete',
      percent: 100
    });
  }

  return allResults;
};