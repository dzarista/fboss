// URL management utilities for session handling
// Manages URL state for session IDs only

/**
 * Parse the current URL to extract session information
 * URL format: /session/{sessionId}
 */
export const parseUrlState = () => {
  const path = window.location.pathname;

  // Extract session ID from path
  const sessionMatch = path.match(/\/session\/([^\/]+)/);
  const sessionId = sessionMatch ? sessionMatch[1] : null;

  return {
    sessionId
  };
};

/**
 * Update the URL to reflect current session state
 */
export const updateUrl = (sessionId, replace = false) => {
  if (!sessionId) {
    // No session - go to root
    const newUrl = '/';
    if (replace) {
      window.history.replaceState({}, '', newUrl);
    } else {
      window.history.pushState({}, '', newUrl);
    }
    return;
  }

  // Build the URL - just session ID, no file IDs
  const newUrl = `/session/${sessionId}`;

  // Update the URL
  if (replace) {
    window.history.replaceState({}, '', newUrl);
  } else {
    window.history.pushState({}, '', newUrl);
  }
};

/**
 * Navigate to a session URL
 */
export const navigateToSession = (sessionId) => {
  updateUrl(sessionId, false);
};

/**
 * Replace current URL with session state (useful for initial load)
 */
export const replaceWithSessionUrl = (sessionId) => {
  updateUrl(sessionId, true);
};

/**
 * Navigate to home (no session)
 */
export const navigateToHome = () => {
  updateUrl(null, false);
};

/**
 * Get a shareable URL for the current session
 */
export const getShareableUrl = (sessionId) => {
  const baseUrl = window.location.origin;
  return `${baseUrl}/session/${sessionId}`;
};

/**
 * Check if the current URL represents a session
 */
export const isSessionUrl = () => {
  return window.location.pathname.startsWith('/session/');
};

/**
 * Extract session ID from current URL
 */
export const getCurrentSessionId = () => {
  const state = parseUrlState();
  return state.sessionId;
};

/**
 * Set up URL change listener for browser back/forward navigation
 */
export const setupUrlChangeListener = (callback) => {
  const handlePopState = () => {
    const urlState = parseUrlState();
    callback(urlState);
  };
  
  window.addEventListener('popstate', handlePopState);
  
  // Return cleanup function
  return () => {
    window.removeEventListener('popstate', handlePopState);
  };
};

/**
 * Generate a session URL for sharing
 */
export const generateSessionShareUrl = (sessionId, openedFiles = [], activeSections = []) => {
  // Extract file IDs from opened files
  const fileIds = openedFiles
    .filter(file => file && file.file_id)
    .map(file => file.file_id);
  
  return getShareableUrl(sessionId, fileIds, activeSections);
};
