import { useState, useEffect } from 'react';

const getErrorTypeDisplay = (errorType) => {
  switch (errorType) {
    case 'pcie_speed_mismatch':
      return 'PCIe Device Speed Mismatch';
    case 'missing_device':
      return 'Missing Device';
    case 'critical_sensor':
      return 'Critical Sensor';
    case 'port_down':
      return 'Port Down';
    default:
      return errorType.replace('_', ' ');
  }
};

// Error Indicator Component
export const ErrorIndicator = ({ errorCount, onClick }) => {
  if (errorCount === 0) return null;

  return (
    <button
      className="error-indicator"
      onClick={onClick}
      title={`${errorCount} critical item${errorCount !== 1 ? 's' : ''} detected - Click to view details`}
      aria-label={`${errorCount} critical items detected`}
    >
      <div className="error-triangle">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="none"
        >
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" fill="white" stroke="#ef4444" strokeWidth="1"/>
          <line x1="12" y1="7" x2="12" y2="14" stroke="#ef4444" strokeWidth="2"/>
          <circle cx="12" cy="17" r="1" fill="#ef4444"/>
        </svg>
      </div>
      <span className="error-count">{errorCount}</span>
    </button>
  );
};

// Error Summary Modal Component
export const ErrorSummaryModal = ({ errors, isOpen, onClose, onNavigateToSection }) => {
  // Initialize all sections as collapsed by default
  const [collapsedSections, setCollapsedSections] = useState(new Set());

  // Update collapsed sections when errors change
  useEffect(() => {
    if (errors && errors.length > 0) {
      const groupedErrors = errors.reduce((acc, error) => {
        const sectionTitle = error.sectionTitle;
        if (!acc[sectionTitle]) acc[sectionTitle] = [];
        acc[sectionTitle].push(error);
        return acc;
      }, {});
      setCollapsedSections(new Set(Object.keys(groupedErrors)));
    }
  }, [errors]);

  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleErrorClick = (error) => {
    onNavigateToSection(error);
    onClose();
  };

  const toggleSectionCollapse = (sectionTitle) => {
    const newCollapsed = new Set(collapsedSections);
    if (newCollapsed.has(sectionTitle)) {
      newCollapsed.delete(sectionTitle);
    } else {
      newCollapsed.add(sectionTitle);
    }
    setCollapsedSections(newCollapsed);
  };

  const groupedErrors = errors.reduce((acc, error) => {
    const key = error.sectionTitle;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(error);
    return acc;
  }, {});

  return (
    <div className="error-modal-backdrop" onClick={handleBackdropClick}>
      <div className="error-modal">
        <div className="error-modal-header">
          <h2>Critical Items</h2>
          <button
            className="error-modal-close"
            onClick={onClose}
            aria-label="Close error summary"
          >
            &times;
          </button>
        </div>
        <div className="error-modal-content">
          <div className="error-summary-stats">
            <p>{errors.length} critical item{errors.length !== 1 ? 's' : ''} found across {Object.keys(groupedErrors).length} section{Object.keys(groupedErrors).length !== 1 ? 's' : ''}</p>
          </div>
          <div className="error-list">
            {Object.entries(groupedErrors).map(([sectionTitle, sectionErrors]) => {
              const isCollapsed = collapsedSections.has(sectionTitle);
              return (
                <div key={sectionTitle} className="error-section">
                  <div className="error-section-header">
                    <div className="error-section-title-container">
                      <span className="error-count-badge">{sectionErrors.length}</span>
                      <h3 className="error-section-title">{sectionTitle}</h3>
                    </div>
                    <button
                      className={`error-section-toggle ${isCollapsed ? 'collapsed' : 'expanded'}`}
                      onClick={() => toggleSectionCollapse(sectionTitle)}
                      aria-label={isCollapsed ? 'Expand section' : 'Collapse section'}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        style={{
                          transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
                          transition: 'transform 0.2s ease'
                        }}
                      >
                        <path
                          d="M6 9l6 6 6-6"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </button>
                  </div>
                  {!isCollapsed && (
                    <ul className="error-items">
                      {sectionErrors.map((error, index) => (
                        <li key={index} className="error-item">
                          <button
                            className="error-link"
                            onClick={() => handleErrorClick(error)}
                            title="Click to navigate to this error"
                          >
                            <div className="error-location">{error.location}</div>
                            <div className="error-value">"{error.value}"</div>
                            <div className="error-type">{getErrorTypeDisplay(error.type)}</div>
                            {error.deviceInfo && (
                              <div className="error-details">
                                <div className="device-detail">Type: {error.deviceInfo.device_type}</div>
                                {error.deviceInfo.expected_speed && (
                                  <div className="device-detail">Expected Speed: {error.deviceInfo.expected_speed}</div>
                                )}
                                {error.deviceInfo.actual_speed && (
                                  <div className="device-detail">Actual Speed: {error.deviceInfo.actual_speed}</div>
                                )}
                              </div>
                            )}
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
