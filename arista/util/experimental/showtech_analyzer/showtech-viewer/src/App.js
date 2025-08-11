import React, { useState, useEffect } from 'react';
import './App.css';
import { checkBackendStatus } from './utils/api';
import {
  getCachedFiles,
  addFilesToCache,
  removeFileFromCache,
  isStorageAvailable,
  getCacheInfo,
  saveFilterState,
  getFilterState,
  removeFilterState
} from './utils/fileCache';

import Sidebar from './components/Sidebar';
import Content from './components/Content';
import SectionFilter from './components/SectionFilter';
import UploadModal from './components/UploadModal';

function App() {
  const [isError, setIsError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Stores a list of all the logs uploaded
  // Before saving them, they must be processed by the backend
  // Still work in progress
  const [logs, setLogs] = useState([]);

  // Currently opened files (max 2)
  const [openedFiles, setOpenedFiles] = useState([null, null]); // [leftFile, rightFile]
  const [visibleSections, setVisibleSections] = useState([new Set(), new Set()]); // [leftSections, rightSections]
  const [fontSizes, setFontSizes] = useState([12, 12]); // [leftFontSize, rightFontSize]
  const [activeFilterTab, setActiveFilterTab] = useState(0); // Which file's filters to show
  const [activeWindow, setActiveWindow] = useState(0); // Which content window is active (0 or 1)
  const [isModalOpen, setIsModalOpen] = useState(false);

  // On startup: check backend connection and load cached files
  useEffect(() => {
    const initializeApp = async () => {
      // Check backend status
      try {
        await checkBackendStatus();
        setIsError(false);
      } catch {
        setIsError(true);
      } finally {
        setIsLoading(false);
      }

      // Load cached files if storage is available
      if (isStorageAvailable()) {
        const cachedFiles = getCachedFiles();
        if (cachedFiles.length > 0) {
          setLogs(cachedFiles);
          console.log(`Loaded ${cachedFiles.length} files from cache`);
        }
      } else {
        console.warn('localStorage not available - files will not be cached');
      }
    };

    initializeApp();
  }, []);

  const statusClass = isError ? 'error' : isLoading ? 'loading' : 'success';
  const statusTitle = isLoading ? 'Connecting' : isError ? 'Failure' : 'Success';

  // Get cache info for display
  const cacheInfo = isStorageAvailable() ? getCacheInfo() : null;

  // Appends new logs to the previous ones at the end of each upload
  const handleFilesProcessed = (newLogs) => {
    const updatedLogs = [...logs, ...newLogs];
    setLogs(updatedLogs);

    // Save to cache
    if (isStorageAvailable()) {
      const success = addFilesToCache(newLogs);
      if (success) {
        console.log(`Cached ${newLogs.length} new files`);
      } else {
        console.warn('Failed to cache files - storage may be full');
      }
    }
  };

  const handleOpenFile = (idx) => {
    const file = logs[idx];

    // Check if file is already open
    const leftFile = openedFiles[0];
    const rightFile = openedFiles[1];

    if (leftFile?.name === file.name || rightFile?.name === file.name) {
      console.log(`File "${file.name}" is already open`);
      return;
    }

    // Find the next available slot (left first, then right)
    let slotIndex = 0;
    if (leftFile === null) {
      slotIndex = 0; // Use left slot
    } else if (rightFile === null) {
      slotIndex = 1; // Use right slot
    } else {
      // Both slots occupied, replace the active window
      slotIndex = activeWindow;
    }

    // Update opened files
    const newOpenedFiles = [...openedFiles];
    newOpenedFiles[slotIndex] = file;
    setOpenedFiles(newOpenedFiles);

    // Load cached filter state or initialize all sections as visible
    if (file?.sections) {
      const cachedFilterState = getFilterState(file.name);
      const newVisibleSections = [...visibleSections];

      if (cachedFilterState && cachedFilterState.size > 0) {
        // Use cached filter state
        newVisibleSections[slotIndex] = cachedFilterState;
        console.log(`Loaded filter state for "${file.name}": ${cachedFilterState.size} sections visible`);
      } else {
        // Default: all sections visible
        const allSectionIds = new Set(file.sections.map((_, sectionIdx) => sectionIdx));
        newVisibleSections[slotIndex] = allSectionIds;

        // Save the default state to cache
        if (isStorageAvailable()) {
          saveFilterState(file.name, allSectionIds);
        }
      }

      setVisibleSections(newVisibleSections);
    }

    // Set active filter tab and active window to the newly opened file
    setActiveFilterTab(slotIndex);
    setActiveWindow(slotIndex);
  };

  const handleCloseFile = (slotIndex) => {
    const newOpenedFiles = [...openedFiles];
    const newVisibleSections = [...visibleSections];
    const newFontSizes = [...fontSizes];

    newOpenedFiles[slotIndex] = null;
    newVisibleSections[slotIndex] = new Set();
    newFontSizes[slotIndex] = 12; // Reset to default font size

    setOpenedFiles(newOpenedFiles);
    setVisibleSections(newVisibleSections);
    setFontSizes(newFontSizes);

    // If we closed the active filter tab, switch to the other one if it exists
    if (activeFilterTab === slotIndex) {
      const otherSlot = slotIndex === 0 ? 1 : 0;
      if (newOpenedFiles[otherSlot] !== null) {
        setActiveFilterTab(otherSlot);
      }
    }

    // If we closed the active window, switch to the other one if it exists
    if (activeWindow === slotIndex) {
      const otherSlot = slotIndex === 0 ? 1 : 0;
      if (newOpenedFiles[otherSlot] !== null) {
        setActiveWindow(otherSlot);
      }
    }
  };

  const handleToggleSection = (sectionIdx) => {
    const activeFile = openedFiles[activeFilterTab];
    if (!activeFile) return;

    setVisibleSections(prev => {
      const newVisibleSections = [...prev];
      const currentSet = new Set(newVisibleSections[activeFilterTab]);

      if (currentSet.has(sectionIdx)) {
        currentSet.delete(sectionIdx);
      } else {
        currentSet.add(sectionIdx);
      }

      newVisibleSections[activeFilterTab] = currentSet;

      // Save the updated filter state to cache
      if (isStorageAvailable()) {
        saveFilterState(activeFile.name, currentSet);
      }

      return newVisibleSections;
    });
  };

  const handleJumpToSection = (sectionIdx) => {
    // Call the jump function for the active tab
    if (window.jumpToSectionFunctions && window.jumpToSectionFunctions[activeFilterTab]) {
      window.jumpToSectionFunctions[activeFilterTab](sectionIdx);
    }
  };

  const handleBulkToggleSections = (showAll) => {
    const activeFile = openedFiles[activeFilterTab];
    if (!activeFile?.sections) return;

    const newSectionSet = showAll
      ? new Set(activeFile.sections.map((_, idx) => idx)) // Show all
      : new Set(); // Hide all

    setVisibleSections(prev => {
      const newVisibleSections = [...prev];
      newVisibleSections[activeFilterTab] = newSectionSet;
      return newVisibleSections;
    });

    // Save the updated filter state to cache
    if (isStorageAvailable()) {
      saveFilterState(activeFile.name, newSectionSet);
    }
  };

  const handleFontSizeChange = (slotIndex, delta) => {
    setFontSizes(prev => {
      const newFontSizes = [...prev];
      const newSize = Math.max(8, Math.min(24, prev[slotIndex] + delta));
      newFontSizes[slotIndex] = newSize;
      return newFontSizes;
    });
  };

  const handleWindowActivation = (slotIndex) => {
    setActiveWindow(slotIndex);
  };

  const handleRemoveFile = (idx) => {
    const fileToRemove = logs[idx];
    const updatedLogs = logs.filter((_, i) => i !== idx);
    setLogs(updatedLogs);

    // Remove from cache
    if (isStorageAvailable()) {
      const fileSuccess = removeFileFromCache(idx);
      const filterSuccess = removeFilterState(fileToRemove.name);

      if (fileSuccess) {
        console.log(`Removed file "${fileToRemove.name}" from cache`);
      }
      if (filterSuccess) {
        console.log(`Removed filter state for "${fileToRemove.name}"`);
      }
    }

    // If the removed file is currently opened, close it
    const newOpenedFiles = [...openedFiles];
    const newVisibleSections = [...visibleSections];
    let shouldUpdateActiveTab = false;

    for (let i = 0; i < 2; i++) {
      if (newOpenedFiles[i]?.name === fileToRemove.name) {
        newOpenedFiles[i] = null;
        newVisibleSections[i] = new Set();

        if (activeFilterTab === i) {
          shouldUpdateActiveTab = true;
        }
      }
    }

    setOpenedFiles(newOpenedFiles);
    setVisibleSections(newVisibleSections);

    // Update active filter tab if needed
    if (shouldUpdateActiveTab) {
      const otherSlot = activeFilterTab === 0 ? 1 : 0;
      if (newOpenedFiles[otherSlot] !== null) {
        setActiveFilterTab(otherSlot);
      }
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>Showtech Viewer</h1>
        <div className="header-indicators">
          {cacheInfo && (
            <div
              className="cache-indicator"
              title={`${cacheInfo.fileCount} files cached (${cacheInfo.sizeInKB} KB)`}
            >
              📁 {cacheInfo.fileCount}
            </div>
          )}
          <div className={`status-indicator ${statusClass}`} title={statusTitle}></div>
        </div>
      </header>

      <div className="body">
        <Sidebar
          logs={logs}
          onSelect={handleOpenFile}
          onUploadClick={() => setIsModalOpen(true)}
          onRemoveFile={handleRemoveFile}
        />

        <div className="content-area">
          {openedFiles[0] && (
            <Content
              log={openedFiles[0]}
              onClose={() => handleCloseFile(0)}
              visibleSections={visibleSections[0]}
              onJumpToSection={handleJumpToSection}
              fontSize={fontSizes[0]}
              onFontSizeChange={(delta) => handleFontSizeChange(0, delta)}
              slotIndex={0}
              isActive={activeWindow === 0}
              onActivate={() => handleWindowActivation(0)}
            />
          )}

          {openedFiles[1] && (
            <Content
              log={openedFiles[1]}
              onClose={() => handleCloseFile(1)}
              visibleSections={visibleSections[1]}
              onJumpToSection={handleJumpToSection}
              fontSize={fontSizes[1]}
              onFontSizeChange={(delta) => handleFontSizeChange(1, delta)}
              slotIndex={1}
              isActive={activeWindow === 1}
              onActivate={() => handleWindowActivation(1)}
            />
          )}

          {!openedFiles[0] && !openedFiles[1] && (
            <div className="no-files-message">
              <p className="placeholder-text">Double-click files to open them side by side</p>
            </div>
          )}
        </div>

        <SectionFilter
          openedFiles={openedFiles}
          activeTab={activeFilterTab}
          onTabChange={setActiveFilterTab}
          visibleSections={visibleSections[activeFilterTab]}
          onToggleSection={handleToggleSection}
          onJumpToSection={handleJumpToSection}
          onBulkToggle={handleBulkToggleSections}
        />
      </div>

      {/* render the upload modal if it's set to true */}
      {isModalOpen && (
        <UploadModal
          onClose={() => setIsModalOpen(false)}
          onFilesProcessed={handleFilesProcessed}
        />
      )}

    </div>
  );
}

export default App;
