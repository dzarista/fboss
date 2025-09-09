import { useState, useEffect } from 'react';

export default function SectionFilter({
  openedFiles,
  activeTab,
  onTabChange,
  visibleSections,
  onToggleSection,
  onJumpToSection,
  onBulkToggle,
  isAlignMode,
  canAlign,
  onToggleAlign,
  isDiffMode,
  onToggleDiff,
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [isBulkToggling, setIsBulkToggling] = useState(false);
  const [showAlignPopup, setShowAlignPopup] = useState(false);

  // Auto-hide align popup after 4 seconds
  useEffect(() => {
    if (showAlignPopup) {
      const timer = setTimeout(() => {
        setShowAlignPopup(false);
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [showAlignPopup]);

  // Get the currently active file and its sections
  const activeFile = openedFiles[activeTab];
  const sections = activeFile?.sections;

  const handleBulkToggleWithSpinner = (showAll) => {
    // Show spinner immediately - this is the FIRST thing that happens
    setIsBulkToggling(true);

    // Let React render the spinner first, then perform the action
    setTimeout(() => {
      onBulkToggle(showAll);

      // Hide spinner - this is the LAST thing that happens
      setTimeout(() => setIsBulkToggling(false), 10);
    }, 10);
  };

  const handleAlignToggle = () => {
    if (!isAlignMode) {
      // Show popup when entering align mode
      setShowAlignPopup(true);
    }
    onToggleAlign();
  };

  if (!openedFiles[0] && !openedFiles[1]) {
    return null; // No files open
  }

  return (
    <div className={`section-filter${collapsed ? ' collapsed' : ''}`}>
      {/* collapse handle */}
      <div
        className="section-filter-collapse-handle"
        onClick={() => setCollapsed(c => !c)}
        title={collapsed ? 'Expand section filter' : 'Collapse section filter'}
      />

      {/* all of this hides when collapsed */}
      {!collapsed && (
        <>
          <div className="section-filter-title-row">
            <h2 className="section-filter-title">Sections</h2>
          </div>

          {/* File Tabs */}
          <div className="section-filter-tabs">
            {openedFiles.map((file, index) => (
              file && (
                <button
                  key={index}
                  className={`section-filter-tab ${activeTab === index && !isAlignMode ? 'active' : ''} ${isAlignMode ? 'align-mode' : ''}`}
                  onClick={() => !isAlignMode && onTabChange(index)}
                  title={file.name}
                  disabled={isAlignMode}
                >
                  {file.name}
                </button>
              )
            ))}
          </div>

          {/* Controls for active file */}
          {sections && sections.length > 0 && (
            <div className="section-filter-controls">
              <button
                className="filter-control-button"
                onClick={() => {
                  const allVisible = visibleSections?.size === sections.length;
                  handleBulkToggleWithSpinner(!allVisible);
                }}
                title={visibleSections?.size === sections.length ? "Hide All" : "Show All"}
                disabled={isBulkToggling}
              >
                {isBulkToggling ? (
                  <div className="raw-button-spinner"></div>
                ) : (
                  visibleSections?.size === sections.length ? "Hide All" : "Show All"
                )}
              </button>

              <div className="filter-control-buttons-right">
                {/* Align button - only show when two files are open and can be aligned */}
                {canAlign && (
                  <button
                    className={`filter-control-button align-button ${isAlignMode ? 'active' : ''}`}
                    onClick={handleAlignToggle}
                    title={isAlignMode ? "Exit Align Mode" : "Enter Align Mode - Synchronize scrolling and navigation"}
                  >
                    {isAlignMode ? "Exit Align" : "Align"}
                  </button>
                )}

                {/* Diff Tables & I2C button - only show when two files are open and can be aligned */}
                {canAlign && (
                  <button
                    className={`filter-control-button diff-button ${isDiffMode ? 'active' : ''}`}
                    onClick={onToggleDiff}
                    title={isDiffMode ? "Exit Diff Mode" : "Diff Tables & I2C - Highlight differences in tables and i2c dumps"}
                  >
                    {isDiffMode ? "Exit Diff" : "Diff Tables & I2C"}
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Section List */}
          {sections && sections.length > 0 ? (
            <div className="section-filter-list">
              {sections.map((section, idx) => (
                <div
                  key={idx}
                  className={'section-filter-item'}
                >
                  <div className="section-filter-checkbox-container">
                    <input
                      type="checkbox"
                      id={`section-${activeTab}-${idx}`}
                      checked={visibleSections?.has(idx) || false}
                      onChange={() => onToggleSection(idx)}
                      className="section-filter-checkbox"
                    />
                    <span
                      className="section-filter-label"
                      onClick={() => onJumpToSection(idx)}
                      title={`Jump to: ${section.title || `Section ${idx + 1}`}`}
                    >
                      {section.title || `Section ${idx + 1}`}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-sections-message">
              <p className="placeholder-text">
                {activeFile ? 'No sections found in this file' : 'Select a file tab above'}
              </p>
            </div>
          )}
        </>
      )}

      {/* Align Mode Explanation Popup */}
      {showAlignPopup && (
        <div className="align-popup">
          <div className="align-popup-content">
            <h4>Align Mode Activated</h4>
            <p>
              Both windows are now synchronized. Use the <strong>table of contents</strong> on the right to navigate -
              clicking any section will jump to that section in both files simultaneously.
            </p>
            <p>
              <em>Don't scroll manually - use the section links for synchronized navigation!</em>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
