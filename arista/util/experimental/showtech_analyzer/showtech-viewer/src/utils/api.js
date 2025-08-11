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
    const msg = await res.text();
    throw new Error(`Upload failed: ${msg || res.statusText}`);
  }
  return res.json();
};