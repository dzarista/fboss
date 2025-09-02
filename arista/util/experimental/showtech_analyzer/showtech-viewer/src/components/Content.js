import { useState, useEffect, useRef, useCallback } from 'react';
import { detectAllErrors } from './ErrorDetection';
import { ErrorIndicator, ErrorSummaryModal } from './ErrorModal';
import { SectionContentRenderer, CollapsibleSection } from './SectionRenderer';
import SystemSummary from './SystemSummary';
import LoadingSpinner from './LoadingSpinner';


export default function Content({ log, onClose, visibleSections, onJumpToSection, fontSize, onFontSizeChange, slotIndex, isActive, onActivate, isLoadingFromApp }) {
  const [expandedSections, setExpandedSections] = useState(new Set());
  const [allExpanded, setAllExpanded] = useState(false);
  const [activeSection, setActiveSection] = useState(null);
  const [detectedErrors, setDetectedErrors] = useState([]);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [showSystemSummary, setShowSystemSummary] = useState(false);
  const [isToggling, setIsToggling] = useState(false); // Simple loading state
  const [isExpandCollapseToggling, setIsExpandCollapseToggling] = useState(false); // Loading state for expand/collapse all
  const [rawModeSections, setRawModeSections] = useState(new Set()); // Track which sections are in raw mode
  const sectionRefs = useRef({});

  // Scroll positions for main content views - per file using slotIndex
  const [systemSummaryScrollPosition, setSystemSummaryScrollPosition] = useState(() => {
    if (!window.scrollPositions) window.scrollPositions = {};
    return window.scrollPositions[`${slotIndex}_summary`] || 0;
  });
  const [sectionsScrollPosition, setSectionsScrollPosition] = useState(() => {
    if (!window.scrollPositions) window.scrollPositions = {};
    return window.scrollPositions[`${slotIndex}_sections`] || 0;
  });

  // Custom toggle function that preserves scroll positions
  const toggleSystemSummary = () => {
    // Show spinner immediately - this is the FIRST thing that happens
    setIsToggling(true);

    // Let React render the spinner first, then do all the heavy work
    setTimeout(() => {
      // Find scrolling containers specific to THIS file using the current component's DOM
      const currentContent = document.querySelector(`.content:nth-child(${slotIndex + 1})`);
      const systemSummaryEl = currentContent?.querySelector('.system-summary-container') ||
                             currentContent?.querySelector('.system-summary-view') ||
                             currentContent?.querySelector('.content-view.system-summary-view');

      const sectionsContainerEl = currentContent?.querySelector('.sections-container') ||
                                 currentContent?.querySelector('.sections-view') ||
                                 currentContent?.querySelector('.content-view.sections-view');

      if (showSystemSummary) {
        // Switching from system summary to sections
        // Save system summary scroll position for this file
        if (systemSummaryEl) {
          const scrollPos = systemSummaryEl.scrollTop;
          setSystemSummaryScrollPosition(scrollPos);
          if (!window.scrollPositions) window.scrollPositions = {};
          window.scrollPositions[`${slotIndex}_summary`] = scrollPos;
        }

        setShowSystemSummary(false);

        // Restore sections scroll position after a brief delay
        setTimeout(() => {
          const currentContent = document.querySelector(`.content:nth-child(${slotIndex + 1})`);
          const newSectionsEl = currentContent?.querySelector('.sections-container') ||
                               currentContent?.querySelector('.sections-view') ||
                               currentContent?.querySelector('.content-view.sections-view');
          if (newSectionsEl) {
            const savedScrollPos = window.scrollPositions?.[`${slotIndex}_sections`] || sectionsScrollPosition;
            newSectionsEl.scrollTop = savedScrollPos;
          }

          // Hide spinner - this is the LAST thing that happens
          setTimeout(() => setIsToggling(false), 10);
        }, 10);
      } else {
        // Switching from sections to system summary
        // Save sections scroll position for this file
        if (sectionsContainerEl) {
          const scrollPos = sectionsContainerEl.scrollTop;
          setSectionsScrollPosition(scrollPos);
          if (!window.scrollPositions) window.scrollPositions = {};
          window.scrollPositions[`${slotIndex}_sections`] = scrollPos;
        }

        setShowSystemSummary(true);

        // Restore system summary scroll position after a brief delay
        setTimeout(() => {
          const currentContent = document.querySelector(`.content:nth-child(${slotIndex + 1})`);
          const newSystemSummaryEl = currentContent?.querySelector('.system-summary-container') ||
                                    currentContent?.querySelector('.system-summary-view') ||
                                    currentContent?.querySelector('.content-view.system-summary-view');
          if (newSystemSummaryEl) {
            const savedScrollPos = window.scrollPositions?.[`${slotIndex}_summary`] || systemSummaryScrollPosition;
            newSystemSummaryEl.scrollTop = savedScrollPos;
          }

          // Hide spinner - this is the LAST thing that happens
          setTimeout(() => setIsToggling(false), 10);
        }, 10);
      }
    }, 10);
  };



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
  const toggleRawMode = (sectionIdx) => {
    const isCurrentlyRaw = rawModeSections.has(sectionIdx);
    const newRawSections = new Set(rawModeSections);

    if (isCurrentlyRaw) {
      // Switch back to structured mode
      newRawSections.delete(sectionIdx);
    } else {
      // Switch to raw mode
      newRawSections.add(sectionIdx);
    }

    setRawModeSections(newRawSections);
  };

  // Create a navigation handler that's bound to THIS specific component
  const handleNavigateToError = useCallback((error) => {
    const sectionIndex = error.sectionIndex;
    const rowIndex = error.rowIndex;
    const deviceIndex = error.deviceIndex;

    // Verify this section exists in our log
    if (!log?.sections?.[sectionIndex]) {
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
      return;
    }

    // Ensure the section is expanded
    if (!expandedSections.has(sectionIndex)) {
      const newExpanded = new Set(expandedSections);
      newExpanded.add(sectionIndex);
      setExpandedSections(newExpanded);
    }

    // For table row navigation, ensure section is in structured mode (not raw mode)
    if (rowIndex !== undefined && rawModeSections.has(sectionIndex)) {
      console.log(`Switching section ${sectionIndex} from raw to structured mode for row navigation`);
      toggleRawMode(sectionIndex);
    }

    // Activate the section
    activateSection(sectionIndex);

    console.log(`Section ${sectionIndex} state:`, {
      isExpanded: expandedSections.has(sectionIndex),
      isInRawMode: rawModeSections.has(sectionIndex),
      isVisible: !visibleSections || visibleSections.has(sectionIndex)
    });

    // Jump to the section first, then scroll within the section to the specific row
    // Use requestAnimationFrame to ensure DOM updates are applied
    requestAnimationFrame(() => {
      setTimeout(() => {
      // Find the section ref directly
      const sectionRef = sectionRefs.current[sectionIndex];
      if (sectionRef) {
        // First, navigate TO the section (scroll outer container to bring section into view)
        sectionRef.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });

        // After jumping to section, scroll WITHIN the section content to the specific row or device
        // Increased timeout to ensure section is fully activated and CSS is applied
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
              }, 500);
            } else {
              console.error(`Device element not found: section-${sectionIndex}-device-${deviceIndex}`);
            }
          } else if (rowIndex !== undefined) {
            // Handle table row navigation - scope search to this section only
            const targetRowId = `section-${sectionIndex}-row-${rowIndex}`;
            console.log(`Looking for row element with ID: ${targetRowId}`);

            // First, let's see what row elements exist in this section
            const allRows = sectionRef.querySelectorAll('[id*="row-"]');
            console.log(`Found ${allRows.length} row elements in section:`, Array.from(allRows).map(r => r.id));

            const rowElement = sectionRef.querySelector(`#${targetRowId}`);
            console.log(`Row element found:`, !!rowElement, rowElement?.id);

            if (rowElement) {
              // Get the section content wrapper for scrolling within the section
              const sectionContentWrapper = sectionRef.querySelector('.section-content-wrapper');
              console.log('Row navigation debug:', {
                rowIndex,
                sectionIndex,
                sectionRef: !!sectionRef,
                rowElement: !!rowElement,
                sectionContentWrapper: !!sectionContentWrapper,
                sectionIsActive: sectionRef.classList.contains('active'),
                wrapperOverflow: sectionContentWrapper ? getComputedStyle(sectionContentWrapper).overflowY : 'N/A'
              });

              if (sectionContentWrapper && getComputedStyle(sectionContentWrapper).overflowY === 'auto') {
                console.log('Scrolling within section content wrapper for row', rowIndex);

                // Calculate position within the section content
                const rowRect = rowElement.getBoundingClientRect();
                const wrapperRect = sectionContentWrapper.getBoundingClientRect();
                const relativeTop = rowRect.top - wrapperRect.top + sectionContentWrapper.scrollTop;
                const targetScrollTop = relativeTop - (sectionContentWrapper.clientHeight / 2) + (rowElement.offsetHeight / 2);

                console.log('Scroll calculation details:', {
                  rowRect: { top: rowRect.top, height: rowRect.height },
                  wrapperRect: { top: wrapperRect.top, height: wrapperRect.height },
                  currentScrollTop: sectionContentWrapper.scrollTop,
                  relativeTop,
                  targetScrollTop: Math.max(0, targetScrollTop),
                  wrapperClientHeight: sectionContentWrapper.clientHeight,
                  wrapperScrollHeight: sectionContentWrapper.scrollHeight
                });

                // Scroll within the section to center the row
                sectionContentWrapper.scrollTo({
                  top: Math.max(0, targetScrollTop),
                  behavior: 'smooth'
                });

                // No backup scrollIntoView to avoid affecting outer container
              } else {
                console.log('Section content wrapper not scrollable or not found, using constrained scrollIntoView');
                // Use scrollIntoView but constrain it to not affect outer container by using nearest
                rowElement.scrollIntoView({
                  behavior: 'smooth',
                  block: 'nearest',
                  inline: 'nearest'
                });
              }

              // Add a temporary highlight to the row
              rowElement.style.backgroundColor = '#fef3c7';
              rowElement.style.transition = 'background-color 0.3s ease';
              setTimeout(() => {
                rowElement.style.backgroundColor = '';
              }, 500);
            } else {
              console.error(`Row element not found: section-${sectionIndex}-row-${rowIndex}`);

              // Try alternative approaches to find the row
              console.log('Trying alternative row finding methods...');

              // Try finding by row index in any table within the section
              const tables = sectionRef.querySelectorAll('table');
              console.log(`Found ${tables.length} tables in section`);
              for (const table of tables) {
                const rows = table.querySelectorAll('tbody tr');
                console.log(`Table has ${rows.length} rows, looking for row ${rowIndex}`);
                if (rows[rowIndex]) {
                  console.log(`Found row ${rowIndex} in table, scrolling to it within section`);
                  // Use constrained scrollIntoView to avoid affecting outer container
                  rows[rowIndex].scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                    inline: 'nearest'
                  });
                  rows[rowIndex].style.backgroundColor = '#ffeb3b';
                  rows[rowIndex].style.transition = 'background-color 0.3s ease';
                  setTimeout(() => { rows[rowIndex].style.backgroundColor = ''; }, 500);
                  break;
                }
              }
            }
          }
        }, 150); // Increased timeout to allow section activation and CSS to be applied
      } else {
        console.error(`Section ref not found for index ${sectionIndex}`);
      }
      }, 10);
    });
  }, [log, expandedSections, visibleSections, onActivate]);



  const toggleAllSections = () => {
    // Show spinner immediately - this is the FIRST thing that happens
    setIsExpandCollapseToggling(true);

    // Let React render the spinner first, then perform the action
    setTimeout(() => {
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

      // Hide spinner - this is the LAST thing that happens
      setTimeout(() => setIsExpandCollapseToggling(false), 10);
    }, 10);
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
                  {log.metadata?.hostname || "Loading..."}
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
                  onClick={toggleSystemSummary}
                  title={showSystemSummary ? "Back to Sections" : "View System Summary"}
                  disabled={isToggling}
                >
                  {isToggling ? (
                    <div className="raw-button-spinner"></div>
                  ) : (
                    showSystemSummary ? "Back to Sections" : "System Summary"
                  )}
                </button>

                {!showSystemSummary && (
                  <button
                    className="control-button"
                    onClick={toggleAllSections}
                    title={allExpanded ? "Collapse All" : "Expand All"}
                    disabled={isExpandCollapseToggling}
                  >
                    {isExpandCollapseToggling ? (
                      <div className="raw-button-spinner"></div>
                    ) : (
                      allExpanded ? "Collapse All" : "Expand All"
                    )}
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
            <div className="sections-container" style={{ fontSize: `${fontSize}px`, position: 'relative' }}>


              {/* Loading View */}
              <div
                className="content-view loading-view"
                style={{ display: (isLoadingFromApp || !log.sections) ? 'block' : 'none' }}
              >
                <LoadingSpinner
                  message="Loading file..."
                  size="large"
                />
              </div>

              {/* System Summary View - Pre-rendered */}
              <div
                className="content-view system-summary-view"
                style={{ display: showSystemSummary && log.sections ? 'block' : 'none' }}
              >
                {log.sections && (
                  <SystemSummary
                    sections={log.sections}
                    systemMap={log.system_map || null}
                    slotIndex={slotIndex}
                  />
                )}


              </div>

              {/* Empty Sections View */}
              <div
                className="content-view empty-sections-view"
                style={{ display: (!isLoadingFromApp && log.sections?.length === 0) ? 'block' : 'none' }}
              >
                <p className="placeholder-text">No sections found in this log</p>
              </div>

              {/* Sections View - Pre-rendered */}
              <div
                className="content-view sections-view"
                style={{ display: (!showSystemSummary && log.sections && log.sections.length > 0) ? 'block' : 'none' }}
              >
                {log.sections && log.sections.map((sec, idx) => (
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
                    onToggleRaw={
                      // Only show raw toggle for sections with structured data (not plain raw)
                      sec.parsed_data?.type !== 'raw'
                        ? () => toggleRawMode(idx)
                        : null
                    }
                    isVisible={!visibleSections || visibleSections.has(idx)}
                  >
                    <SectionContentRenderer
                      section={sec}
                      sectionIndex={idx}
                      isRawMode={rawModeSections.has(idx)}
                      rawContent={sec.raw_content}
                    />
                  </CollapsibleSection>
                ))}


              </div>
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