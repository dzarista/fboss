// Session API utilities
// Handles all session-related API calls

// API endpoint configuration
const API_ENDPOINT = process.env.NODE_ENV === 'production'
  ? '/api'  // Relative path for production (served by Flask)
  : 'http://localhost/api';  // Absolute URL for development (React dev server -> Flask backend)

// List all sessions
export const listSessions = async (limit = 50, offset = 0) => {
  const response = await fetch(`${API_ENDPOINT}/sessions?limit=${limit}&offset=${offset}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch sessions');
  }
  return response.json();
};

// Create a new session
export const createSession = async (sessionData) => {
  const response = await fetch(`${API_ENDPOINT}/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(sessionData),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to create session');
  }
  return response.json();
};

// Get a session with all its files
export const getSession = async (sessionId) => {
  const response = await fetch(`${API_ENDPOINT}/sessions/${sessionId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch session');
  }
  return response.json();
};

// Update session metadata
export const updateSession = async (sessionId, updates) => {
  const response = await fetch(`${API_ENDPOINT}/sessions/${sessionId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to update session');
  }
  return response.json();
};

// Delete a session
export const deleteSession = async (sessionId) => {
  const response = await fetch(`${API_ENDPOINT}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to delete session');
  }
  return response.json();
};

// Add files to a session
export const addFilesToSession = async (sessionId, files) => {
  const formData = new FormData();
  files.forEach((file) => formData.append('file', file));

  const response = await fetch(`${API_ENDPOINT}/sessions/${sessionId}/files`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to add files to session');
  }
  return response.json();
};

// Delete a file from a session
export const deleteFileFromSession = async (sessionId, fileId) => {
  const response = await fetch(`${API_ENDPOINT}/sessions/${sessionId}/files/${fileId}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to delete file');
  }
  return response.json();
};

// Search sessions
export const searchSessions = async (query, limit = 20) => {
  const response = await fetch(`${API_ENDPOINT}/sessions/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to search sessions');
  }
  return response.json();
};

// Upload files and create a new session
export const uploadFilesAndCreateSession = async (files, sessionName, sessionDescription = '') => {
  try {
    // First create the session
    const session = await createSession({
      name: sessionName,
      description: sessionDescription
    });

    // Then add files to the session
    const result = await addFilesToSession(session.session_id, files);
    
    return {
      session,
      files: result.files
    };
  } catch (error) {
    throw new Error(`Failed to upload files and create session: ${error.message}`);
  }
};

// Get session metadata only (without files)
export const getSessionMetadata = async (sessionId) => {
  const response = await fetch(`${API_ENDPOINT}/sessions/${sessionId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch session metadata');
  }
  const data = await response.json();
  return data.metadata; // Return just the metadata part
};
