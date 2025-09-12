import React, { useState, useEffect } from 'react';
import './App.css';
import { checkBackendStatus } from './utils/api';
import packageJson from '../package.json';
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
import { findDiff } from './utils/findDiff';


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
  const [loadingFiles, setLoadingFiles] = useState([false, false]); // Track which slots are loading
  const [isAlignMode, setIsAlignMode] = useState(false); // Track align mode state
  const [isDiffMode, setIsDiffMode] = useState(false); // Track diff mode state
  const [diffs, setDiffs] = useState({ file1Diffs: new Map(), file2Diffs: new Map() }); // Store all diffs
  const [alignMode, setAlignMode] = useState(false); // Whether files are aligned for synchronized scrolling

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

          // After loading cached files, check for URL fragments
          handleUrlFragments(cachedFiles);
        }
      } else {
        console.warn('localStorage not available - files will not be cached');
      }
    };

    initializeApp();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Listen for hash changes
  useEffect(() => {
    const handleHashChange = () => {
      handleUrlFragments();
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Handle URL fragment navigation
  const handleUrlFragments = (availableLogs = logs) => {
    const hash = window.location.hash;
    if (!hash || hash === '#') return;

    // Ensure we have logs to work with
    if (!availableLogs || availableLogs.length === 0) {
      console.warn('No logs available for URL fragment navigation');
      return;
    }

    // Parse fragments: #fileIndex/sectionIndex
    const fragments = hash.substring(1).split('/');
    const fileIndex = parseInt(fragments[0], 10);
    const sectionIndex = fragments[1] ? parseInt(fragments[1], 10) : null;

    // Validate file index
    if (isNaN(fileIndex) || fileIndex < 0 || fileIndex >= availableLogs.length) {
      console.warn(`Invalid file index in URL fragment: ${fileIndex}`);
      return;
    }

    const targetFile = availableLogs[fileIndex];
    if (!targetFile) {
      console.warn(`File not found at index: ${fileIndex}`);
      return;
    }

    // Check if file is already open
    const leftFile = openedFiles[0];
    const rightFile = openedFiles[1];
    let targetSlotIndex = null;

    if (leftFile?.name === targetFile.name) {
      targetSlotIndex = 0;
    } else if (rightFile?.name === targetFile.name) {
      targetSlotIndex = 1;
    }

    if (targetSlotIndex !== null) {
      // File is already open, activate its window and navigate to section
      setActiveWindow(targetSlotIndex);
      setActiveFilterTab(targetSlotIndex);

      if (sectionIndex !== null && !isNaN(sectionIndex)) {
        // Validate section index
        const openFile = openedFiles[targetSlotIndex];
        if (openFile?.sections && sectionIndex >= 0 && sectionIndex < openFile.sections.length) {
          // Navigate to section after a brief delay to ensure window is active
          setTimeout(() => {
            handleJumpToSection(sectionIndex);
          }, 50);
        } else {
          console.warn(`Invalid section index in URL fragment: ${sectionIndex} (file has ${openFile?.sections?.length || 0} sections)`);
        }
      }
    } else {
      // File is not open, open it and then navigate to section
      handleOpenFile(fileIndex).then(() => {
        if (sectionIndex !== null && !isNaN(sectionIndex)) {
          // Validate section index after file is loaded
          setTimeout(() => {
            const loadedFile = logs[fileIndex];
            if (loadedFile?.sections && sectionIndex >= 0 && sectionIndex < loadedFile.sections.length) {
              handleJumpToSection(sectionIndex);
            } else {
              console.warn(`Invalid section index in URL fragment: ${sectionIndex} (file has ${loadedFile?.sections?.length || 0} sections)`);
            }
          }, 200); // Brief wait for file to load
        }
      });
    }
  };

  // Update URL fragment based on current state
  const updateUrlFragment = (fileIndex = null, sectionIndex = null) => {
    if (fileIndex === null) {
      // Clear fragment
      if (window.location.hash) {
        window.history.replaceState(null, '', window.location.pathname + window.location.search);
      }
      return;
    }

    let fragment = `#${fileIndex}`;
    if (sectionIndex !== null && sectionIndex >= 0) {
      fragment += `/${sectionIndex}`;
    }

    if (window.location.hash !== fragment) {
      window.history.replaceState(null, '', window.location.pathname + window.location.search + fragment);
    }
  };

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

    if (leftFile?.name === file.name) {
      console.log(`File "${file.name}" is already open in left window`);
      // Activate the left window and update URL
      setActiveWindow(0);
      setActiveFilterTab(0);
      updateUrlFragment(idx);
      return;
    } else if (rightFile?.name === file.name) {
      console.log(`File "${file.name}" is already open in right window`);
      // Activate the right window and update URL
      setActiveWindow(1);
      setActiveFilterTab(1);
      updateUrlFragment(idx);
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

      // Load cached filter state or initialize all sections as visible
      if (actualFile?.sections) {
        const cachedFilterState = getFilterState(actualFile.name);
        const newVisibleSections = [...visibleSections];

        if (cachedFilterState && cachedFilterState.size > 0) {
          // Use cached filter state
          newVisibleSections[slotIndex] = cachedFilterState;
          console.log(`Loaded filter state for "${actualFile.name}": ${cachedFilterState.size} sections visible`);
        } else {
          // Default: all sections visible
          const allSectionIds = new Set(actualFile.sections.map((_, sectionIdx) => sectionIdx));
          newVisibleSections[slotIndex] = allSectionIds;

          // Save the default state to cache
          if (isStorageAvailable()) {
            saveFilterState(actualFile.name, allSectionIds);
          }
        }

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

    // Update URL fragment to reflect the opened file
    updateUrlFragment(idx);
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
        const activeFile = newOpenedFiles[otherSlot];
        const fileIndex = logs.findIndex(log => log.name === activeFile.name);
        if (fileIndex !== -1) {
          updateUrlFragment(fileIndex);
        }
      } else {
        // No files open, clear URL fragment
        updateUrlFragment(null);
      }
    } else if (newOpenedFiles[0] === null && newOpenedFiles[1] === null) {
      // All files closed, clear URL fragment
      updateUrlFragment(null);
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

            // Save the updated filter state to cache for both files
            if (isStorageAvailable()) {
              saveFilterState(openedFiles[slotIndex].name, currentSet);
            }
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

        // Save the updated filter state to cache
        if (isStorageAvailable()) {
          saveFilterState(activeFile.name, currentSet);
        }
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

    // Update URL fragment to include section index
    const activeFile = openedFiles[activeFilterTab];
    if (activeFile) {
      const fileIndex = logs.findIndex(log => log.name === activeFile.name);
      if (fileIndex !== -1) {
        updateUrlFragment(fileIndex, sectionIdx);
      }
    }
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

            // Save the updated filter state to cache for both files
            if (isStorageAvailable()) {
              saveFilterState(openedFiles[slotIndex].name, newSectionSet);
            }
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

      // Save the updated filter state to cache
      if (isStorageAvailable()) {
        saveFilterState(activeFile.name, newSectionSet);
      }
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
    const activeFile = openedFiles[slotIndex];
    if (activeFile) {
      const fileIndex = logs.findIndex(log => log.name === activeFile.name);
      if (fileIndex !== -1) {
        updateUrlFragment(fileIndex);
      }
    }
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
    const activeFile = openedFiles[slotIndex];
    if (activeFile) {
      const fileIndex = logs.findIndex(log => log.name === activeFile.name);
      if (fileIndex !== -1) {
        updateUrlFragment(fileIndex);
      }
    }
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
      <div className="body">
        <Sidebar
          logs={logs}
          onSelect={handleOpenFile}
          onUploadClick={() => setIsModalOpen(true)}
          onRemoveFile={handleRemoveFile}
          statusClass={statusClass}
          statusTitle={statusTitle}
          version={`v${packageJson.version}-${process.env.NODE_ENV === 'production' ? 'prod' : 'dev'}`}
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
          onFilesProcessed={handleFilesProcessed}
        />
      )}

    </div>
  );
}

export default App;
