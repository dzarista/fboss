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


const LINE_FALLBACK_PX = 18; // used if computed line-height is not available

// Create a navigation handler that's bound to THIS specific component
const handleNavigateToError = useCallback((error) => {
  const sectionIndex = error.sectionIndex;
  const rowIndex = Number.isInteger(error.rowIndex) ? error.rowIndex : undefined;
  const deviceIndex = Number.isInteger(error.deviceIndex) ? error.deviceIndex : undefined;
  const line = Number.isInteger(error.line) ? error.line : undefined;
  const wantsRaw = (error.view === 'raw') || (error.type && String(error.type).toLowerCase() === 'regex match') || (line !== undefined);

  // Verify this section exists in our log
  if (!log?.sections?.[sectionIndex]) return;

  if (onActivate) onActivate();

  // Ensure the section is visible in the filter
  if (visibleSections && !visibleSections.has(sectionIndex)) {
    // It's filtered out; parent must adjust the filter. We bail here by design.
    return;
  }

  // Ensure the section is expanded
  if (!expandedSections.has(sectionIndex)) {
    const next = new Set(expandedSections);
    next.add(sectionIndex);
    setExpandedSections(next);
  }

  // If we need to navigate by row, ensure STRUCTURED mode.
  if (rowIndex !== undefined && rawModeSections.has(sectionIndex)) {
    toggleRawMode(sectionIndex);
  }

  // If we need to navigate by raw line/match, ensure RAW mode.
  if ((wantsRaw && !rawModeSections.has(sectionIndex))) {
    toggleRawMode(sectionIndex);
  }

  // Activate the section
  activateSection(sectionIndex);

  // Jump to the section first, then scroll within it
  requestAnimationFrame(() => {
    setTimeout(() => {
      const sectionRef = sectionRefs.current[sectionIndex];
      if (!sectionRef) {
        console.error(`Section ref not found for index ${sectionIndex}`);
        return;
      }

      sectionRef.scrollIntoView({ behavior: 'smooth', block: 'start' });

      // After the section is visible, scroll WITHIN the section
      setTimeout(() => {
        const sectionContentWrapper = sectionRef.querySelector('.section-content-wrapper');

        // ---- LSPCI device navigation ----
        if (deviceIndex !== undefined && deviceIndex !== null) {
          const deviceElement = sectionRef.querySelector(`#section-${sectionIndex}-device-${deviceIndex}`);
          if (!deviceElement) {
            console.error(`Device element not found: section-${sectionIndex}-device-${deviceIndex}`);
            return;
          }

          if (sectionContentWrapper) {
            const deviceRect = deviceElement.getBoundingClientRect();
            const wrapperRect = sectionContentWrapper.getBoundingClientRect();
            const relativeTop = deviceRect.top - wrapperRect.top + sectionContentWrapper.scrollTop;
            const targetScrollTop = relativeTop - (sectionContentWrapper.clientHeight / 2) + (deviceElement.offsetHeight / 2);
            sectionContentWrapper.scrollTo({ top: Math.max(0, targetScrollTop), behavior: 'smooth' });
          } else {
            deviceElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
          }

          // Flash highlight
          deviceElement.style.backgroundColor = '#fee2e2';
          deviceElement.style.borderColor = '#ef4444';
          deviceElement.style.transition = 'background-color 0.3s ease, border-color 0.3s ease';
          setTimeout(() => { deviceElement.style.backgroundColor = ''; deviceElement.style.borderColor = ''; }, 500);
          return;
        }

        // ---- Structured table row navigation ----
        if (rowIndex !== undefined) {
          const rowElement = sectionRef.querySelector(`#section-${sectionIndex}-row-${rowIndex}`);
          if (rowElement) {
            if (sectionContentWrapper && getComputedStyle(sectionContentWrapper).overflowY === 'auto') {
              const rowRect = rowElement.getBoundingClientRect();
              const wrapperRect = sectionContentWrapper.getBoundingClientRect();
              const relativeTop = rowRect.top - wrapperRect.top + sectionContentWrapper.scrollTop;
              const targetScrollTop = relativeTop - (sectionContentWrapper.clientHeight / 2) + (rowElement.offsetHeight / 2);
              sectionContentWrapper.scrollTo({ top: Math.max(0, targetScrollTop), behavior: 'smooth' });
            } else {
              rowElement.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
            }
            rowElement.style.backgroundColor = '#fef3c7';
            rowElement.style.transition = 'background-color 0.3s ease';
            setTimeout(() => { rowElement.style.backgroundColor = ''; }, 500);
            return;
          }
          // Fallback: try nth row of first tbody in this section
          const altTable = sectionRef.querySelector('table tbody');
          if (altTable?.children?.[rowIndex]) {
            const altRow = altTable.children[rowIndex];
            altRow.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
            altRow.style.backgroundColor = '#ffeb3b';
            setTimeout(() => { altRow.style.backgroundColor = ''; }, 500);
          } else {
            console.error(`Row element not found: section-${sectionIndex}-row-${rowIndex}`);
          }
          return;
        }

        // ---- Raw line/match navigation ----
        if (wantsRaw && line !== undefined) {
          console.log('Navigating to line:', line, 'in section:', sectionIndex);

          // Ensure we're in raw view: we already toggled earlier if needed
          const rawContainer = sectionRef.querySelector('.section-content-view.raw-view .section-text-content');
          console.log('Raw container found:', !!rawContainer);

          if (!rawContainer) {
            console.error('Raw container element not found for raw navigation');
            // Try alternative selectors
            const altContainer = sectionRef.querySelector('.section-text-content');
            console.log('Alternative container found:', !!altContainer);
            if (!altContainer) return;
          }

          const container = rawContainer || sectionRef.querySelector('.section-text-content');

          // Look for the specific line element using data-line attribute
          const lineElement = container.querySelector(`[data-line="${line}"]`);
          console.log('Line element found:', !!lineElement, 'for line:', line);

          if (lineElement) {
            console.log('Scrolling to line element');
            // Direct navigation to the specific line element
            lineElement.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Highlight the line temporarily
            lineElement.style.backgroundColor = '#fef3c7';
            lineElement.style.transition = 'background-color 0.3s ease';
            setTimeout(() => { lineElement.style.backgroundColor = ''; }, 1000);

            // Also flash any regex highlights on this line
            const marks = lineElement.querySelectorAll('mark.regex-highlight');
            marks.forEach(mark => {
              mark.style.boxShadow = '0 0 0 2px rgba(239,68,68,0.9)';
              setTimeout(() => { mark.style.boxShadow = ''; }, 1000);
            });
          } else {
            console.log('Line element not found, trying fallback method');
            // Debug: log all available line elements
            const allLines = container.querySelectorAll('[data-line]');
            console.log('Available line elements:', Array.from(allLines).map(el => el.getAttribute('data-line')));

            // Fallback: try the old method for backward compatibility
            const wrapper = sectionContentWrapper; // scroll container
            const computed = getComputedStyle(container);
            let lineHeight = parseFloat(computed.lineHeight);
            if (!Number.isFinite(lineHeight)) {
              // Approx fallback: assume 18px or derive from height/lines if possible
              const totalLines = (container.textContent || '').split('\n').length || 1;
              lineHeight = Math.max(LINE_FALLBACK_PX, container.getBoundingClientRect().height / totalLines);
            }

            const targetTop = Math.max(0, (line * lineHeight) - ( (wrapper?.clientHeight || 0) / 2 ));
            if (wrapper) {
              wrapper.scrollTo({ top: targetTop, behavior: 'smooth' });
            } else {
              // Fallback if wrapper missing
              container.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
          }

          // Optional: flash the first <mark> in this section (regex highlight)
          const firstMark = sectionRef.querySelector('.section-content-view.raw-view .section-text-content mark.regex-highlight');
          if (firstMark) {
            firstMark.style.boxShadow = '0 0 0 2px rgba(239,68,68,0.9)';
            setTimeout(() => { firstMark.style.boxShadow = ''; }, 600);
          }
          return;
        }

      }, 150); // wait for expansion/toggle styles
    }, 10); // let scrollIntoView for the section start
  });
}, [
  log,
  expandedSections,
  visibleSections,
  rawModeSections,
  onActivate,
  toggleRawMode,
  activateSection,
  sectionRefs,
  setExpandedSections
]);




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