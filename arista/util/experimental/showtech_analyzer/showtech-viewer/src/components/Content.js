import { useState, useEffect, useRef, useCallback } from 'react';
import { detectAllErrors } from './ErrorDetection';
import { ErrorIndicator, ErrorSummaryModal } from './ErrorModal';
import { SectionContentRenderer, CollapsibleSection } from './SectionRenderer';
import SystemSummary from './SystemSummary';
import LoadingSpinner from './LoadingSpinner';
import { getSectionRaw } from '../utils/api';

export default function Content({ log, onClose, visibleSections, onJumpToSection, fontSize, onFontSizeChange, slotIndex, isActive, onActivate, isLoadingFromApp }) {
  const [expandedSections, setExpandedSections] = useState(new Set());
  const [allExpanded, setAllExpanded] = useState(false);
  const [activeSection, setActiveSection] = useState(null);
  const [detectedErrors, setDetectedErrors] = useState([]);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [showSystemSummary, setShowSystemSummary] = useState(false);
  const [rawModeSections, setRawModeSections] = useState(new Set()); // Track which sections are in raw mode
  const [rawDataCache, setRawDataCache] = useState({}); // Cache raw data to avoid repeated API calls
  const [loadingRawSections, setLoadingRawSections] = useState(new Set()); // Track which sections are loading raw data
  const sectionRefs = useRef({});



  // Initialize all sections as expanded when log changes
  useEffect(() => {
    if (log?.sections) {
      const allSectionIds = new Set(log.sections.map((_, idx) => idx));
      setExpandedSections(allSectionIds); // Start with all sections expanded
      setAllExpanded(true);
      // Initialize refs
      sectionRefs.current = {};

      // Reset raw mode state when log changes
      setRawModeSections(new Set());
      setRawDataCache({});
      setLoadingRawSections(new Set());

      // Detect errors in the log
      const errors = detectAllErrors(log);
      setDetectedErrors(errors);
    }
  }, [log]);

  // Handle jumping to section
  useEffect(() => {
    if (onJumpToSection && typeof onJumpToSection === 'function') {
      // Register this content's jump function with a unique key
      if (!window.jumpToSectionFunctions) {
        window.jumpToSectionFunctions = {};
      }

      window.jumpToSectionFunctions[slotIndex] = (sectionIdx) => {
        const sectionRef = sectionRefs.current[sectionIdx];
        if (sectionRef) {
          sectionRef.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      };


    }

    // Cleanup when component unmounts
    return () => {
      if (window.jumpToSectionFunctions && slotIndex !== undefined) {
        delete window.jumpToSectionFunctions[slotIndex];
      }
    };
  }, [onJumpToSection, slotIndex]);

  const toggleSection = (sectionIdx) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionIdx)) {
      newExpanded.delete(sectionIdx);
    } else {
      newExpanded.add(sectionIdx);
    }
    setExpandedSections(newExpanded);
    setAllExpanded(newExpanded.size === log?.sections?.length);
  };

  const activateSection = (sectionIdx) => {
    setActiveSection(sectionIdx);
  };

  // Handle raw mode toggle for a section
  const toggleRawMode = async (sectionIdx) => {
    const isCurrentlyRaw = rawModeSections.has(sectionIdx);

    if (isCurrentlyRaw) {
      // Switch back to structured mode
      const newRawSections = new Set(rawModeSections);
      newRawSections.delete(sectionIdx);
      setRawModeSections(newRawSections);
    } else {
      // Switch to raw mode - fetch raw data if not cached
      const cacheKey = `${log.file_id}_${sectionIdx}`;

      if (!log.file_id) {
        console.error('No file_id found in log object:', log);
        return;
      }

      if (!rawDataCache[cacheKey]) {
        // Add to loading state
        const newLoadingSections = new Set(loadingRawSections);
        newLoadingSections.add(sectionIdx);
        setLoadingRawSections(newLoadingSections);

        try {
          const rawData = await getSectionRaw(log.file_id, sectionIdx);

          // Cache the raw data
          setRawDataCache(prev => ({
            ...prev,
            [cacheKey]: rawData.raw_content
          }));

          // Add to raw mode sections
          const newRawSections = new Set(rawModeSections);
          newRawSections.add(sectionIdx);
          setRawModeSections(newRawSections);

        } catch (error) {
          console.error('Failed to fetch raw data:', error);
          // Could show an error message to user here
        } finally {
          // Remove from loading state
          const newLoadingSections = new Set(loadingRawSections);
          newLoadingSections.delete(sectionIdx);
          setLoadingRawSections(newLoadingSections);
        }
      } else {
        // Data is cached, just toggle mode
        const newRawSections = new Set(rawModeSections);
        newRawSections.add(sectionIdx);
        setRawModeSections(newRawSections);
      }
    }
  };

  // Create a navigation handler that's bound to THIS specific component
  const handleNavigateToError = useCallback((error) => {
    console.log(`Navigation called on Content ${slotIndex}:`, {
      errorType: error.type,
      sectionIndex: error.sectionIndex,
      sectionTitle: error.sectionTitle,
      logName: log?.name
    });

    const sectionIndex = error.sectionIndex;
    const rowIndex = error.rowIndex;
    const deviceIndex = error.deviceIndex;

    // Verify this section exists in our log
    if (!log?.sections?.[sectionIndex]) {
      console.warn(`Section ${sectionIndex} not found in log ${log?.name}`);
      return;
    }





    // First, activate this window to ensure it gets focus
    if (onActivate) {
      onActivate();
    }

    // Ensure the section is visible in the filter
    if (visibleSections && !visibleSections.has(sectionIndex)) {
      // This error is in a filtered-out section, we need to make it visible
      // We can't directly modify visibleSections here as it comes from parent
      console.warn(`Error is in filtered section ${sectionIndex}. Section may not be visible.`);
    }

    // Ensure the section is expanded
    if (!expandedSections.has(sectionIndex)) {
      const newExpanded = new Set(expandedSections);
      newExpanded.add(sectionIndex);
      setExpandedSections(newExpanded);
    }

    // Activate the section
    activateSection(sectionIndex);

    // Jump to the section first, then scroll within the section to the specific row
    setTimeout(() => {
      // Find the section ref directly
      const sectionRef = sectionRefs.current[sectionIndex];
      if (sectionRef) {
        // First, position the section at the top of the viewport
        sectionRef.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });

        // After jumping to section, scroll within the section content to the specific row or device
        setTimeout(() => {
          if (deviceIndex !== undefined && deviceIndex !== null) {
            // Handle LSPCI device navigation - scope search to this section only
            const deviceElement = sectionRef.querySelector(`#section-${sectionIndex}-device-${deviceIndex}`);
            if (deviceElement) {
              // Get the section content wrapper for scrolling within the section
              const sectionContentWrapper = sectionRef.querySelector('.section-content-wrapper');
              if (sectionContentWrapper) {
                console.log('Scrolling within section content wrapper for device', deviceIndex);
                // Calculate position within the section content
                const deviceRect = deviceElement.getBoundingClientRect();
                const wrapperRect = sectionContentWrapper.getBoundingClientRect();
                const relativeTop = deviceRect.top - wrapperRect.top + sectionContentWrapper.scrollTop;

                // Scroll within the section to center the device
                const targetScrollTop = relativeTop - (sectionContentWrapper.clientHeight / 2) + (deviceElement.offsetHeight / 2);
                sectionContentWrapper.scrollTo({
                  top: Math.max(0, targetScrollTop),
                  behavior: 'smooth'
                });
              } else {
                console.log('Section content wrapper not found, using fallback scrollIntoView for device');
                // Fallback to regular scrollIntoView if section wrapper not found
                deviceElement.scrollIntoView({
                  behavior: 'smooth',
                  block: 'center'
                });
              }

              // Add a temporary highlight to the device (red for speed mismatch)
              deviceElement.style.backgroundColor = '#fee2e2';
              deviceElement.style.borderColor = '#ef4444';
              deviceElement.style.transition = 'background-color 0.3s ease, border-color 0.3s ease';
              setTimeout(() => {
                deviceElement.style.backgroundColor = '';
                deviceElement.style.borderColor = '';
              }, 3000);
            } else {
              console.error(`Device element not found: section-${sectionIndex}-device-${deviceIndex}`);
            }
          } else if (rowIndex !== undefined) {
            // Handle table row navigation - scope search to this section only
            const rowElement = sectionRef.querySelector(`#section-${sectionIndex}-row-${rowIndex}`);
            if (rowElement) {
              // Get the section content wrapper for scrolling within the section
              const sectionContentWrapper = sectionRef.querySelector('.section-content-wrapper');
              if (sectionContentWrapper) {
                console.log('Scrolling within section content wrapper for row', rowIndex);
                // Calculate position within the section content
                const rowRect = rowElement.getBoundingClientRect();
                const wrapperRect = sectionContentWrapper.getBoundingClientRect();
                const relativeTop = rowRect.top - wrapperRect.top + sectionContentWrapper.scrollTop;

                // Scroll within the section to center the row
                const targetScrollTop = relativeTop - (sectionContentWrapper.clientHeight / 2) + (rowElement.offsetHeight / 2);
                sectionContentWrapper.scrollTo({
                  top: Math.max(0, targetScrollTop),
                  behavior: 'smooth'
                });
              } else {
                console.log('Section content wrapper not found, using fallback scrollIntoView for row');
                // Fallback to regular scrollIntoView if section wrapper not found
                rowElement.scrollIntoView({
                  behavior: 'smooth',
                  block: 'center'
                });
              }

              // Add a temporary highlight to the row
              rowElement.style.backgroundColor = '#fef3c7';
              rowElement.style.transition = 'background-color 0.3s ease';
              setTimeout(() => {
                rowElement.style.backgroundColor = '';
              }, 2000);
            } else {
              console.error(`Row element not found: section-${sectionIndex}-row-${rowIndex}`);
            }
          }
        }, 300); // Increased timeout to allow section positioning to complete
      } else {
        console.error(`Section ref not found for index ${sectionIndex}`);
      }
    }, 100);
  }, [log, expandedSections, visibleSections, onActivate]);



  const toggleAllSections = () => {
    if (allExpanded) {
      // Collapse all
      setExpandedSections(new Set());
      setAllExpanded(false);
    } else {
      // Expand all
      const allSectionIds = new Set(log.sections.map((_, idx) => idx));
      setExpandedSections(allSectionIds);
      setAllExpanded(true);
    }
  };





  return (
    <div className={`content ${isActive ? 'active' : ''}`} style={{ fontSize: `${fontSize}px` }} onClick={onActivate}>
      <div className="log-display-section">
        {!log ? (
          <p className="placeholder-text">Double-click a file to open it</p>
        ) : (
          <>
            <div className="content-topbar">
              <div className="file-name-container">
                <span className="file-name-text">
                  {log.name || 'Unknown File'}
                  <button
                    className="close-file-button"
                    onClick={onClose}
                    title="Close file"
                    aria-label="Close file"
                  >
                    &times;
                  </button>
                </span>
              </div>
              <div className="topbar-controls">
                {!showSystemSummary && (
                  <ErrorIndicator
                    errorCount={detectedErrors.length}
                    onClick={() => setShowErrorModal(true)}
                  />
                )}

                <button
                  className="control-button system-summary-button"
                  onClick={() => setShowSystemSummary(!showSystemSummary)}
                  title={showSystemSummary ? "Back to Sections" : "View System Summary"}
                >
                  {showSystemSummary ? "Back to Sections" : "System Summary"}
                </button>

                {!showSystemSummary && (
                  <button
                    className="control-button"
                    onClick={toggleAllSections}
                    title={allExpanded ? "Collapse All" : "Expand All"}
                  >
                    {allExpanded ? "Collapse All" : "Expand All"}
                  </button>
                )}

                <div className="font-size-controls">
                  <span className="font-size-label">Font Size</span>
                  <button
                    className="control-button font-button"
                    onClick={() => onFontSizeChange(-1)}
                    title="Decrease Font Size"
                    disabled={fontSize <= 8}
                  >
                    -
                  </button>
                  <button
                    className="control-button font-button"
                    onClick={() => onFontSizeChange(1)}
                    title="Increase Font Size"
                    disabled={fontSize >= 24}
                  >
                    +
                  </button>
                </div>
              </div>
            </div>
            <div className="sections-container" style={{ fontSize: `${fontSize}px` }}>
              {(isLoadingFromApp || !log.sections) ? (
                // Show loading spinner while file is loading
                <LoadingSpinner
                  message="Loading file..."
                  size="large"
                />
              ) : showSystemSummary ? (
                // Show System Summary
                <SystemSummary
                  sections={log.sections || []}
                  systemMap={log.system_map || null}
                />
              ) : log.sections?.length === 0 ? (
                <p className="placeholder-text">No sections found in this log</p>
              ) : (
                // Show all sections normally
                log.sections
                  .map((sec, idx) => ({ sec, idx }))
                  .filter(({ idx }) => !visibleSections || visibleSections.has(idx))
                  .map(({ sec, idx }) => (
                    <CollapsibleSection
                      key={idx}
                      ref={(el) => {
                        if (el) {
                          sectionRefs.current[idx] = el;
                        }
                      }}
                      title={sec.title || `Section ${idx + 1}`}
                      isExpanded={expandedSections.has(idx)}
                      onToggle={() => toggleSection(idx)}
                      isActive={activeSection === idx}
                      onActivate={() => activateSection(idx)}
                      isRawMode={rawModeSections.has(idx)}
                      isLoadingRaw={loadingRawSections.has(idx)}
                      onToggleRaw={
                        // Only show raw toggle for sections with structured data (not plain raw)
                        sec.parsed_data?.type !== 'raw'
                          ? () => toggleRawMode(idx)
                          : null
                      }
                    >
                      <SectionContentRenderer
                        section={sec}
                        sectionIndex={idx}
                        isRawMode={rawModeSections.has(idx)}
                        rawContent={rawDataCache[`${log.file_id}_${idx}`]}
                        isLoadingRaw={loadingRawSections.has(idx)}
                      />
                    </CollapsibleSection>
                  ))
              )}
            </div>
          </>
        )}
      </div>

      {/* Error Summary Modal - Only show if this component has errors */}
      {showErrorModal && detectedErrors.length > 0 && (
        <ErrorSummaryModal
          key={`error-modal-${slotIndex}`}
          errors={detectedErrors}
          isOpen={showErrorModal}
          onClose={() => setShowErrorModal(false)}
          onNavigateToSection={handleNavigateToError}
        />
      )}
    </div>
  );
}