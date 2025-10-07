import React, { useState, useEffect } from 'react';
import './App.css';
import { checkBackendStatus } from './utils/api';
import packageJson from '../package.json';
import { findDiff } from './utils/findDiff';
import {
  parseUrlState,
  updateUrl,
  setupUrlChangeListener,
  navigateToSession
} from './utils/urlManager';
import { getSession, deleteFileFromSession, updateSession } from './utils/sessionApi';

import Sidebar from './components/Sidebar';
import Content from './components/Content';
import SectionFilter from './components/SectionFilter';
import UploadModal from './components/UploadModal';
import SessionManager from './components/SessionManager';

function App() {
  const [isError, setIsError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Session management
  const [currentSession, setCurrentSession] = useState(null);
  const [sessionFiles, setSessionFiles] = useState([]);
  const [showSessionManager, setShowSessionManager] = useState(false);
  const [loadingSession, setLoadingSession] = useState(false);

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
  const [loadingFiles, setLoadingFiles] = useState([false, false]); // Track which slots are loading
  const [isAlignMode, setIsAlignMode] = useState(false); // Track align mode state
  const [isDiffMode, setIsDiffMode] = useState(false); // Track diff mode state
  const [diffs, setDiffs] = useState({ file1Diffs: new Map(), file2Diffs: new Map() }); // Store all diffs
  const [alignMode, setAlignMode] = useState(false); // Whether files are aligned for synchronized scrolling

  // On startup: check backend connection and handle URL-based session loading
  useEffect(() => {
    const initializeApp = async () => {
      // Quick backend status check with minimal loading time
      try {
        await checkBackendStatus();
        setIsError(false);
        setIsLoading(false);
      } catch {
        setIsError(true);
        setIsLoading(false);
      }

      // Parse URL to see if we should load a session (don't show loading for this)
      const urlState = parseUrlState();
      if (urlState.sessionId) {
        try {
          await loadSessionFromUrl(urlState);
        } catch (error) {
          console.error('Failed to load session from URL:', error);
          // If session loading fails, show session manager
          setShowSessionManager(true);
        }
      } else {
        // No session in URL - start with no active session, allow file uploads
        // Session manager will be shown when user clicks the Sessions button
      }
    };

    initializeApp();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Set up URL change listener for browser navigation
  useEffect(() => {
    const cleanup = setupUrlChangeListener(async (urlState) => {
      if (urlState.sessionId) {
        // Check if we already have this session loaded
        if (currentSession && currentSession.session_id === urlState.sessionId) {
          return;
        }

        try {
          await loadSessionFromUrl(urlState);
        } catch (error) {
          console.error('Failed to load session from URL change:', error);
        }
      } else {
        // No session - clear current session and show manager
        setCurrentSession(null);
        setSessionFiles([]);
        setOpenedFiles([null, null]);
        setLoadingSession(false);
        setShowSessionManager(true);
      }
    });

    return cleanup;
  }, []);

  // Load session from URL state
  const loadSessionFromUrl = async (urlState) => {
    try {
      setLoadingSession(true);
      const sessionData = await getSession(urlState.sessionId);
      setCurrentSession(sessionData.metadata);
      setSessionFiles(sessionData.files || []);
      setLogs(sessionData.files || []); // For compatibility with existing code
    } catch (error) {
      throw new Error(`Failed to load session: ${error.message}`);
    } finally {
      setLoadingSession(false);
    }
  };

  // Handle session loading from SessionManager
  const handleSessionLoad = async (sessionData) => {
    setCurrentSession(sessionData.metadata);
    setSessionFiles(sessionData.files || []);
    setLogs(sessionData.files || []); // For compatibility
    setOpenedFiles([null, null]); // Clear opened files

    // Update URL to reflect loaded session
    navigateToSession(sessionData.metadata.session_id);
  };

  // Handle session rename from Sidebar
  const handleSessionRename = async (session, newName) => {
    if (newName && newName.trim() !== session.name) {
      try {
        await updateSession(session.session_id, { name: newName.trim() });
        // Update the local state
        setCurrentSession({ ...session, name: newName.trim() });
      } catch (error) {
        console.error('Failed to rename session:', error);
        alert('Failed to rename session. Please try again.');
      }
    }
  };

  // Handle session rename from SessionManager
  const handleSessionManagerRename = (sessionId, newName) => {
    if (currentSession && currentSession.session_id === sessionId) {
      setCurrentSession({ ...currentSession, name: newName });
    }
  };

  // Handle file uploads to current session
  const handleFilesUploaded = async (uploadedFiles, newSession = null) => {

    if (newSession) {
      // New session was created by UploadModal - set it as current and display files
      setCurrentSession(newSession);
      setSessionFiles(uploadedFiles || []);
      setLogs(uploadedFiles || []);
    } else if (currentSession) {
      // Files were already uploaded by UploadModal to the current session
      // Show loading state while refreshing session files
      setLoadingSession(true);

      try {
        const updatedSession = await getSession(currentSession.session_id);

        setSessionFiles(updatedSession.files || []);
        setLogs(updatedSession.files || []);
      } catch (error) {
        console.error('Failed to reload session after upload:', error);
        // Fall back to local handling if session reload fails
        setLogs(prevLogs => [...prevLogs, ...uploadedFiles]);
      } finally {
        // Clear loading state
        setLoadingSession(false);
      }
    } else {
      // No current session and no new session provided - fall back to local handling
      setLogs(prevLogs => [...prevLogs, ...uploadedFiles]);
    }
  };



  // Update URL fragment based on current state
  // Update URL to reflect current session and file state
  const updateSessionUrl = () => {
    if (!currentSession) return;

    // Update URL with current session state
    updateUrl(currentSession.session_id, true);
  };

  const statusClass = isError ? 'error' : 'success';
  const statusTitle = isError ? 'Failure' : 'Success';





  const handleOpenFile = async (idx) => {
    // Validate index and file existence
    if (idx < 0 || idx >= logs.length) {
      console.warn(`Invalid file index: ${idx}`);
      return;
    }

    const file = logs[idx];
    if (!file) {
      console.warn(`File not found at index: ${idx}`);
      return;
    }

    // Check if file is already open
    const leftFile = openedFiles[0];
    const rightFile = openedFiles[1];

    if (leftFile?.file_id === file.file_id) {
      // Activate the left window and update URL
      setActiveWindow(0);
      setActiveFilterTab(0);
      updateSessionUrl();
      return;
    } else if (rightFile?.file_id === file.file_id) {
      // Activate the right window and update URL
      setActiveWindow(1);
      setActiveFilterTab(1);
      updateSessionUrl();
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

    // IMMEDIATELY set loading state and open window with placeholder
    const newLoadingFiles = [...loadingFiles];
    newLoadingFiles[slotIndex] = true;
    setLoadingFiles(newLoadingFiles);

    // Create a placeholder file object to show loading state
    const placeholderFile = {
      name: file.name,
      file_id: file.file_id,
      sections: null, // This will trigger loading state
      isLoading: true
    };

    // Update opened files with placeholder
    const newOpenedFiles = [...openedFiles];
    newOpenedFiles[slotIndex] = placeholderFile;
    setOpenedFiles(newOpenedFiles);

    // Simulate progressive loading - in a real scenario, this would be actual data loading
    try {
      // Small delay to ensure UI updates
      await new Promise(resolve => setTimeout(resolve, 100));

      // Now load the actual file data
      const actualFile = { ...file };

      // Initialize all sections as visible
      if (actualFile?.sections) {
        const newVisibleSections = [...visibleSections];
        // Default: all sections visible
        const allSectionIds = new Set(actualFile.sections.map((_, sectionIdx) => sectionIdx));
        newVisibleSections[slotIndex] = allSectionIds;
        setVisibleSections(newVisibleSections);
      }

      // Small delay to ensure UI is ready for the file data
      await new Promise(resolve => setTimeout(resolve, 50));

      // Update with actual file data
      const finalOpenedFiles = [...openedFiles];
      finalOpenedFiles[slotIndex] = actualFile;
      setOpenedFiles(finalOpenedFiles);

      // Clear loading state
      const finalLoadingFiles = [...loadingFiles];
      finalLoadingFiles[slotIndex] = false;
      setLoadingFiles(finalLoadingFiles);

    } catch (error) {
      console.error('Error loading file:', error);
      // Clear loading state on error
      const errorLoadingFiles = [...loadingFiles];
      errorLoadingFiles[slotIndex] = false;
      setLoadingFiles(errorLoadingFiles);
    }

    // Set active filter tab and active window to the newly opened file
    setActiveFilterTab(slotIndex);
    setActiveWindow(slotIndex);

    // Update URL to reflect the opened file
    updateSessionUrl();
  };

  const handleCloseFile = (slotIndex) => {
    const newOpenedFiles = [...openedFiles];
    const newVisibleSections = [...visibleSections];
    const newFontSizes = [...fontSizes];
    const newLoadingFiles = [...loadingFiles];

    newOpenedFiles[slotIndex] = null;
    newVisibleSections[slotIndex] = new Set();
    newFontSizes[slotIndex] = 12; // Reset to default font size
    newLoadingFiles[slotIndex] = false; // Reset loading state

    setOpenedFiles(newOpenedFiles);
    setVisibleSections(newVisibleSections);
    setFontSizes(newFontSizes);
    setLoadingFiles(newLoadingFiles);

    // Exit diff mode when a file is closed
    if (isDiffMode) {
      setIsDiffMode(false);
      setDiffs({ file1Diffs: new Map(), file2Diffs: new Map() });
    }

    // Exit align mode when a file is closed
    if (isAlignMode) {
      setIsAlignMode(false);
    }

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
        setActiveFilterTab(otherSlot);

        // Update URL to reflect the now-active file
        updateSessionUrl();
      } else {
        // No files open, update URL
        updateSessionUrl();
      }
    } else if (newOpenedFiles[0] === null && newOpenedFiles[1] === null) {
      // All files closed, update URL
      updateSessionUrl();
    }
  };

  const handleToggleSection = (sectionIdx) => {
    const activeFile = openedFiles[activeFilterTab];
    if (!activeFile) return;

    setVisibleSections(prev => {
      const newVisibleSections = [...prev];

      if (isAlignMode && canAlign()) {
        // In align mode, toggle section in both files
        [0, 1].forEach(slotIndex => {
          if (openedFiles[slotIndex]) {
            const currentSet = new Set(newVisibleSections[slotIndex]);

            if (currentSet.has(sectionIdx)) {
              currentSet.delete(sectionIdx);
            } else {
              currentSet.add(sectionIdx);
            }

            newVisibleSections[slotIndex] = currentSet;
          }
        });
      } else {
        // Normal mode: only toggle for active file
        const currentSet = new Set(newVisibleSections[activeFilterTab]);

        if (currentSet.has(sectionIdx)) {
          currentSet.delete(sectionIdx);
        } else {
          currentSet.add(sectionIdx);
        }

        newVisibleSections[activeFilterTab] = currentSet;
      }

      return newVisibleSections;
    });
  };

  const handleJumpToSection = (sectionIdx) => {
    if (isAlignMode && canAlign()) {
      // In align mode, jump to section in both windows
      if (window.jumpToSectionFunctions) {
        if (window.jumpToSectionFunctions[0]) {
          window.jumpToSectionFunctions[0](sectionIdx);
        }
        if (window.jumpToSectionFunctions[1]) {
          window.jumpToSectionFunctions[1](sectionIdx);
        }
      }
      // In align mode, activate section in both windows
      if (window.activateSectionFunctions) {
        if (window.activateSectionFunctions[0]) {
          window.activateSectionFunctions[0](sectionIdx);
        }
        if (window.activateSectionFunctions[1]) {
          window.activateSectionFunctions[1](sectionIdx);
        }
      }
    } else {
      // Normal mode: call the jump function for the active tab
      if (window.jumpToSectionFunctions && window.jumpToSectionFunctions[activeFilterTab]) {
        window.jumpToSectionFunctions[activeFilterTab](sectionIdx);
      }
      // Normal mode: activate section in the active tab
      if (window.activateSectionFunctions && window.activateSectionFunctions[activeFilterTab]) {
        window.activateSectionFunctions[activeFilterTab](sectionIdx);
      }
    }

    // Update URL to reflect current state
    updateSessionUrl();
  };

  const handleBulkToggleSections = (showAll) => {
    const activeFile = openedFiles[activeFilterTab];
    if (!activeFile?.sections) return;

    if (isAlignMode && canAlign()) {
      // In align mode, bulk toggle sections in both files
      setVisibleSections(prev => {
        const newVisibleSections = [...prev];

        [0, 1].forEach(slotIndex => {
          if (openedFiles[slotIndex]?.sections) {
            const newSectionSet = showAll
              ? new Set(openedFiles[slotIndex].sections.map((_, idx) => idx)) // Show all
              : new Set(); // Hide all

            newVisibleSections[slotIndex] = newSectionSet;
          }
        });

        return newVisibleSections;
      });
    } else {
      // Normal mode: only toggle for active file
      const newSectionSet = showAll
        ? new Set(activeFile.sections.map((_, idx) => idx)) // Show all
        : new Set(); // Hide all

      setVisibleSections(prev => {
        const newVisibleSections = [...prev];
        newVisibleSections[activeFilterTab] = newSectionSet;
        return newVisibleSections;
      });


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
    // In align mode, don't change active window
    if (isAlignMode) return;

    setActiveWindow(slotIndex);
    // Update the section filter to point to the active window's file
    setActiveFilterTab(slotIndex);

    // Update URL to reflect the active file
    updateSessionUrl();
  };

  // Check if align mode should be available
  const canAlign = () => {
    if (!openedFiles[0] || !openedFiles[1]) return false;

    const file1 = openedFiles[0];
    const file2 = openedFiles[1];

    const version1 = file1.metadata?.showtech_version;
    const version2 = file2.metadata?.showtech_version;
    const product1 = file1.metadata?.product_name;
    const product2 = file2.metadata?.product_name;

    return version1 && version2 && product1 && product2 &&
           version1 === version2 && product1 === product2;
  };

  // Toggle align mode
  const handleToggleAlign = () => {
    if (!isAlignMode) {
      // Entering align mode - get the active section first, then set align mode and jump
      let activeSectionIndex = null;
      if (window.getActiveSectionFunctions && window.getActiveSectionFunctions[activeWindow]) {
        activeSectionIndex = window.getActiveSectionFunctions[activeWindow]();
      }

      // Set align mode
      setIsAlignMode(true);

      // Directly jump to the section in both windows without waiting for handleJumpToSection
      if (activeSectionIndex !== null && canAlign()) {
        // Jump to section in both windows directly
        if (window.jumpToSectionFunctions) {
          if (window.jumpToSectionFunctions[0]) {
            window.jumpToSectionFunctions[0](activeSectionIndex);
          }
          if (window.jumpToSectionFunctions[1]) {
            window.jumpToSectionFunctions[1](activeSectionIndex);
          }
        }
        // Activate section in both windows
        if (window.activateSectionFunctions) {
          if (window.activateSectionFunctions[0]) {
            window.activateSectionFunctions[0](activeSectionIndex);
          }
          if (window.activateSectionFunctions[1]) {
            window.activateSectionFunctions[1](activeSectionIndex);
          }
        }
      } else {
        // Fallback to scrolling to top if no active section
        if (window.scrollToTopFunctions) {
          if (window.scrollToTopFunctions[0]) {
            window.scrollToTopFunctions[0]();
          }
          if (window.scrollToTopFunctions[1]) {
            window.scrollToTopFunctions[1]();
          }
        }
      }
    } else {
      // Exiting align mode
      setIsAlignMode(false);
    }
  };

  // Exit diff mode and align mode when files change or page reloads
  useEffect(() => {
    if (isDiffMode && (!openedFiles[0] || !openedFiles[1] || !canAlign())) {
      setIsDiffMode(false);
      setDiffs({ file1Diffs: new Map(), file2Diffs: new Map() });
    }

    if (isAlignMode && (!openedFiles[0] || !openedFiles[1] || !canAlign())) {
      setIsAlignMode(false);
    }
  }, [openedFiles, isDiffMode, isAlignMode, canAlign]);

  // Toggle diff mode
  const handleToggleDiff = () => {
    if (isDiffMode) {
      // Exit diff mode
      setIsDiffMode(false);
      setDiffs({ file1Diffs: new Map(), file2Diffs: new Map() });
    } else {
      // Enter diff mode - compute all diffs (i2c, tables, etc.)
      const { file1Diffs, file2Diffs } = findDiff(openedFiles[0], openedFiles[1]);
      setDiffs({ file1Diffs, file2Diffs });
      setIsDiffMode(true);
    }
  };

  const handleFilterTabChange = (slotIndex) => {
    // When user clicks on a section filter tab, activate both the filter and the window
    setActiveFilterTab(slotIndex);
    setActiveWindow(slotIndex);

    // Update URL to reflect the active file
    updateSessionUrl();
  };

  const handleRemoveFile = async (idx) => {
    const fileToRemove = logs[idx];

    // Prevent duplicate calls by checking if file is already being removed
    if (!fileToRemove || fileToRemove.isRemoving) {
      return;
    }

    // Mark file as being removed to prevent duplicate calls
    const updatedLogs = logs.map((log, i) =>
      i === idx ? { ...log, isRemoving: true } : log
    );
    setLogs(updatedLogs);

    // Remove from session if we have one
    if (currentSession && fileToRemove.file_id) {
      try {
        await deleteFileFromSession(currentSession.session_id, fileToRemove.file_id);

        // Reload session to get updated file list
        const updatedSession = await getSession(currentSession.session_id);
        setSessionFiles(updatedSession.files || []);
        setLogs(updatedSession.files || []);
      } catch (error) {
        console.error('Failed to remove file from session:', error);
        // Fall back to local removal if session update fails
        const finalLogs = logs.filter((_, i) => i !== idx);
        setLogs(finalLogs);
      }
    } else {
      // No session or no file_id - just remove locally
      const finalLogs = logs.filter((_, i) => i !== idx);
      setLogs(finalLogs);
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
      <div className="body">
        <Sidebar
          logs={logs}
          onSelect={handleOpenFile}
          onUploadClick={() => setIsModalOpen(true)}
          onRemoveFile={handleRemoveFile}
          statusClass={statusClass}
          statusTitle={statusTitle}
          version={`v${packageJson.version}-${process.env.NODE_ENV === 'production' ? 'prod' : 'dev'}`}
          currentSession={currentSession}
          onSessionManagerClick={() => setShowSessionManager(true)}
          onSessionRename={handleSessionRename}
          loadingSession={loadingSession}
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
              isActive={isAlignMode ? false : activeWindow === 0}
              onActivate={() => handleWindowActivation(0)}
              isLoadingFromApp={loadingFiles[0]}
              isAlignMode={isAlignMode}
              isDiffMode={isDiffMode}
              diffs={diffs.file1Diffs}
              onExitAlignMode={() => setIsAlignMode(false)}
              onExitDiffMode={() => {
                setIsDiffMode(false);
                setDiffs({ file1Diffs: new Map(), file2Diffs: new Map() });
              }}
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
              isActive={isAlignMode ? false : activeWindow === 1}
              onActivate={() => handleWindowActivation(1)}
              isLoadingFromApp={loadingFiles[1]}
              isAlignMode={isAlignMode}
              isDiffMode={isDiffMode}
              diffs={diffs.file2Diffs}
              onExitAlignMode={() => setIsAlignMode(false)}
              onExitDiffMode={() => {
                setIsDiffMode(false);
                setDiffs({ file1Diffs: new Map(), file2Diffs: new Map() });
              }}
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
          onTabChange={handleFilterTabChange}
          visibleSections={visibleSections[activeFilterTab]}
          onToggleSection={handleToggleSection}
          onJumpToSection={handleJumpToSection}
          onBulkToggle={handleBulkToggleSections}
          isAlignMode={isAlignMode}
          canAlign={canAlign()}
          onToggleAlign={handleToggleAlign}
          isDiffMode={isDiffMode}
          onToggleDiff={handleToggleDiff}
        />
      </div>

      {/* render the upload modal if it's set to true */}
      {isModalOpen && (
        <UploadModal
          onClose={() => setIsModalOpen(false)}
          onFilesProcessed={handleFilesUploaded}
          currentSession={currentSession}
        />
      )}

      {/* render the session manager if it's set to true */}
      {showSessionManager && (
        <SessionManager
          onSessionLoad={handleSessionLoad}
          onClose={() => setShowSessionManager(false)}
          currentSessionId={currentSession?.session_id}
          onSessionRename={handleSessionManagerRename}
        />
      )}

    </div>
  );
}

export default App;
