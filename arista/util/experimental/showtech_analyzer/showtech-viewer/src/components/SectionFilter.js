import { useState } from 'react';

export default function SectionFilter({
  openedFiles,
  activeTab,
  onTabChange,
  visibleSections,
  onToggleSection,
  onJumpToSection,
  onBulkToggle,
}) {
  const [collapsed, setCollapsed] = useState(false);

  // Get the currently active file and its sections
  const activeFile = openedFiles[activeTab];
  const sections = activeFile?.sections;

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
                  className={`section-filter-tab ${activeTab === index ? 'active' : ''}`}
                  onClick={() => onTabChange(index)}
                  title={file.name}
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
                  onBulkToggle(!allVisible);
                }}
                title={visibleSections?.size === sections.length ? "Hide All" : "Show All"}
              >
                {visibleSections?.size === sections.length ? "Hide All" : "Show All"}
              </button>
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
    </div>
  );
}
