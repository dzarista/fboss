import { useState, useEffect, useRef, useCallback } from 'react';
import { detectAllErrors } from './ErrorDetection';
import { ErrorIndicator, ErrorSummaryModal } from './ErrorModal';
import { SectionContentRenderer, CollapsibleSection } from './SectionRenderer';

export default function Content({ log, onClose, visibleSections, onJumpToSection, fontSize, onFontSizeChange, slotIndex, isActive, onActivate }) {
  const [expandedSections, setExpandedSections] = useState(new Set());
  const [allExpanded, setAllExpanded] = useState(true);
  const [fullscreenSection, setFullscreenSection] = useState(null);
  const [fullscreenScrollPosition, setFullscreenScrollPosition] = useState(0);
  const [activeSection, setActiveSection] = useState(null);
  const [detectedErrors, setDetectedErrors] = useState([]);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const sectionRefs = useRef({});
  const fullscreenContentRef = useRef(null);



  // Initialize all sections as expanded when log changes
  useEffect(() => {
    if (log?.sections) {
      const allSectionIds = new Set(log.sections.map((_, idx) => idx));
      setExpandedSections(allSectionIds);
      setAllExpanded(true);
      // Initialize refs
      sectionRefs.current = {};

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

    // Jump to the section first, then scroll to the specific row
    setTimeout(() => {
      // Find the section ref directly
      const sectionRef = sectionRefs.current[sectionIndex];
      if (sectionRef) {
        sectionRef.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });

        // After jumping to section, scroll to the specific row or device
        setTimeout(() => {
          if (deviceIndex !== undefined && deviceIndex !== null) {
            // Handle LSPCI device navigation - scope search to this section only
            const deviceElement = sectionRef.querySelector(`#section-${sectionIndex}-device-${deviceIndex}`);
            if (deviceElement) {
              deviceElement.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
              });

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
              rowElement.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
              });

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
        }, 200);
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

  const toggleFullscreen = (sectionIdx) => {
    if (fullscreenSection === sectionIdx) {
      // Exiting fullscreen - jump to section location like navigation button
      setFullscreenSection(null);
      // Use the jump function for THIS specific window (slotIndex)
      setTimeout(() => {
        if (window.jumpToSectionFunctions && window.jumpToSectionFunctions[slotIndex]) {
          window.jumpToSectionFunctions[slotIndex](sectionIdx);
        }
      }, 50);
    } else {
      // Entering fullscreen - save current scroll position
      const sectionElement = sectionRefs.current[sectionIdx];
      if (sectionElement) {
        const contentWrapper = sectionElement.querySelector('.section-content-wrapper');
        if (contentWrapper) {
          setFullscreenScrollPosition(contentWrapper.scrollTop);
        }
      }

      setFullscreenSection(sectionIdx);
      // Ensure the section is expanded when going fullscreen
      if (!expandedSections.has(sectionIdx)) {
        const newExpanded = new Set(expandedSections);
        newExpanded.add(sectionIdx);
        setExpandedSections(newExpanded);
      }

      // Restore scroll position in fullscreen after DOM update
      setTimeout(() => {
        if (fullscreenContentRef.current) {
          fullscreenContentRef.current.scrollTop = fullscreenScrollPosition;
        }
      }, 50);
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
                <ErrorIndicator
                  errorCount={detectedErrors.length}
                  onClick={() => setShowErrorModal(true)}
                />

                <button
                  className="control-button"
                  onClick={toggleAllSections}
                  title={allExpanded ? "Collapse All" : "Expand All"}
                >
                  {allExpanded ? "Collapse All" : "Expand All"}
                </button>

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
            <div className={`sections-container ${fullscreenSection !== null ? 'has-fullscreen' : ''}`} style={{ fontSize: `${fontSize}px` }}>
              {log.sections?.length === 0 ? (
                <p className="placeholder-text">No sections found in this log</p>
              ) : (
                fullscreenSection !== null ? (
                  // Show only fullscreen section
                  <CollapsibleSection
                    key={fullscreenSection}
                    ref={(el) => {
                      if (el) {
                        sectionRefs.current[fullscreenSection] = el;
                        fullscreenContentRef.current = el?.querySelector('.section-content-wrapper');
                      }
                    }}
                    title={log.sections[fullscreenSection]?.title || `Section ${fullscreenSection + 1}`}
                    isExpanded={true}
                    onToggle={() => {}}
                    isFullscreen={true}
                    onFullscreenToggle={() => toggleFullscreen(fullscreenSection)}
                    isActive={activeSection === fullscreenSection}
                    onActivate={() => activateSection(fullscreenSection)}
                  >
                    <SectionContentRenderer section={log.sections[fullscreenSection]} sectionIndex={fullscreenSection} />
                  </CollapsibleSection>
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
                        isFullscreen={false}
                        onFullscreenToggle={() => toggleFullscreen(idx)}
                        isActive={activeSection === idx}
                        onActivate={() => activateSection(idx)}
                      >
                        <SectionContentRenderer section={sec} sectionIndex={idx} />
                      </CollapsibleSection>
                    ))
                )
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
