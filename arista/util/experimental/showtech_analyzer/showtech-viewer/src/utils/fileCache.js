// File cache utility using localStorage
const CACHE_KEY = 'showtech_uploaded_files';
const FILTER_CACHE_KEY = 'showtech_filter_states';
const CACHE_VERSION = '1.1';
const VERSION_KEY = 'showtech_cache_version';

// Check if we need to clear old cache due to version changes
const checkCacheVersion = () => {
  const storedVersion = localStorage.getItem(VERSION_KEY);
  if (storedVersion !== CACHE_VERSION) {
    localStorage.removeItem(CACHE_KEY);
    localStorage.removeItem(FILTER_CACHE_KEY);
    localStorage.setItem(VERSION_KEY, CACHE_VERSION);
  }
};

// Get all cached files
export const getCachedFiles = () => {
  try {
    checkCacheVersion();
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return [];
    
    const files = JSON.parse(cached);
    return Array.isArray(files) ? files : [];
  } catch (error) {
    console.error('Error reading cached files:', error);
    // Clear corrupted cache
    localStorage.removeItem(CACHE_KEY);
    return [];
  }
};

// Save files to cache
export const setCachedFiles = (files) => {
  try {
    checkCacheVersion();
    localStorage.setItem(CACHE_KEY, JSON.stringify(files));
    return true;
  } catch (error) {
    console.error('Error saving files to cache:', error);
    // Handle quota exceeded or other storage errors
    if (error.name === 'QuotaExceededError') {
      console.warn('localStorage quota exceeded. Consider clearing old files.');
    }
    return false;
  }
};

// Add a single file to cache
export const addFileToCache = (file) => {
  const cachedFiles = getCachedFiles();
  
  // Check if file already exists (by name)
  const existingIndex = cachedFiles.findIndex(f => f.name === file.name);
  
  if (existingIndex >= 0) {
    // Replace existing file
    cachedFiles[existingIndex] = file;
  } else {
    // Add new file
    cachedFiles.push(file);
  }
  
  return setCachedFiles(cachedFiles);
};

// Add multiple files to cache
export const addFilesToCache = (newFiles) => {
  const cachedFiles = getCachedFiles();
  
  newFiles.forEach(file => {
    const existingIndex = cachedFiles.findIndex(f => f.name === file.name);
    if (existingIndex >= 0) {
      cachedFiles[existingIndex] = file;
    } else {
      cachedFiles.push(file);
    }
  });
  
  return setCachedFiles(cachedFiles);
};

// Remove a file from cache by index
export const removeFileFromCache = (index) => {
  const cachedFiles = getCachedFiles();
  if (index >= 0 && index < cachedFiles.length) {
    cachedFiles.splice(index, 1);
    return setCachedFiles(cachedFiles);
  }
  return false;
};

// Remove a file from cache by name
export const removeFileFromCacheByName = (fileName) => {
  const cachedFiles = getCachedFiles();
  const index = cachedFiles.findIndex(f => f.name === fileName);
  if (index >= 0) {
    cachedFiles.splice(index, 1);
    return setCachedFiles(cachedFiles);
  }
  return false;
};

// Clear all cached files
export const clearFileCache = () => {
  try {
    localStorage.removeItem(CACHE_KEY);
    return true;
  } catch (error) {
    console.error('Error clearing file cache:', error);
    return false;
  }
};

// Get cache size info
export const getCacheInfo = () => {
  const cachedFiles = getCachedFiles();
  const cacheString = localStorage.getItem(CACHE_KEY) || '';
  
  return {
    fileCount: cachedFiles.length,
    sizeInBytes: new Blob([cacheString]).size,
    sizeInKB: Math.round(new Blob([cacheString]).size / 1024),
    sizeInMB: Math.round(new Blob([cacheString]).size / (1024 * 1024) * 100) / 100
  };
};

// Check if localStorage is available
export const isStorageAvailable = () => {
  try {
    const test = '__storage_test__';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch (error) {
    return false;
  }
};

// -------- Filter State Management --------

// Get all cached filter states
export const getCachedFilterStates = () => {
  try {
    checkCacheVersion();
    const cached = localStorage.getItem(FILTER_CACHE_KEY);
    if (!cached) return {};

    const filterStates = JSON.parse(cached);
    return typeof filterStates === 'object' ? filterStates : {};
  } catch (error) {
    console.error('Error reading cached filter states:', error);
    localStorage.removeItem(FILTER_CACHE_KEY);
    return {};
  }
};

// Save filter state for a specific file
export const saveFilterState = (fileName, visibleSections) => {
  try {
    checkCacheVersion();
    const filterStates = getCachedFilterStates();

    // Convert Set to Array for JSON serialization
    filterStates[fileName] = Array.from(visibleSections);

    localStorage.setItem(FILTER_CACHE_KEY, JSON.stringify(filterStates));
    return true;
  } catch (error) {
    console.error('Error saving filter state:', error);
    return false;
  }
};

// Get filter state for a specific file
export const getFilterState = (fileName) => {
  try {
    const filterStates = getCachedFilterStates();
    const state = filterStates[fileName];

    // Convert Array back to Set
    return state ? new Set(state) : null;
  } catch (error) {
    console.error('Error getting filter state:', error);
    return null;
  }
};

// Remove filter state for a specific file
export const removeFilterState = (fileName) => {
  try {
    const filterStates = getCachedFilterStates();
    delete filterStates[fileName];

    localStorage.setItem(FILTER_CACHE_KEY, JSON.stringify(filterStates));
    return true;
  } catch (error) {
    console.error('Error removing filter state:', error);
    return false;
  }
};

// Clear all filter states
export const clearFilterStates = () => {
  try {
    localStorage.removeItem(FILTER_CACHE_KEY);
    return true;
  } catch (error) {
    console.error('Error clearing filter states:', error);
    return false;
  }
};
