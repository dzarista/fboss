import { useState, useEffect } from 'react';
import { ErrorTriangleIcon, ChevronDownIcon } from '../assets/icons/Icon';

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
    case 'regex_match':
      return 'Regex Match';
    default:
      return (errorType || '').replace('_', ' ');
  }
};

// -------- dynamic details helpers --------

const isPresent = (v) => v !== null && v !== undefined && v !== '';

const startCase = (s) =>
  String(s || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

const LABEL_MAP = {
  device_type: 'Type',
  description: 'Desc',
  location: 'Location',
  slot: 'Slot',
  expected_speed: 'Expected Speed',
  actual_speed: 'Actual Speed',
  view: 'View',
  line: 'Line',
  rowIndex: 'Row',
  pattern: 'Pattern',
  message: 'Message'
};

// Build an array of {label?, value} lines from an error object
const buildDetailLines = (error) => {
  const lines = [];

  // 1) Primary message (or pattern) — show as a plain line (no label)
  if (isPresent(error?.message) || isPresent(error?.pattern)) {
    lines.push({ value: error.message || error.pattern });
  }

  // 2) Device info block (if present) — iterate keys dynamically
  if (error?.deviceInfo && typeof error.deviceInfo === 'object') {
    Object.entries(error.deviceInfo).forEach(([k, v]) => {
      if (!isPresent(v)) return;
      lines.push({ label: LABEL_MAP[k] || startCase(k), value: v });
    });
  }

  // 3) Other commonly useful fields on the error itself (dynamic)
  // Only include if they are actually present AND meaningful.
  const ownFields = [
    // numeric/int-ish
    ...(Object.prototype.hasOwnProperty.call(error, 'rowIndex') && Number.isInteger(error.rowIndex)
      ? [{ label: LABEL_MAP.rowIndex, value: error.rowIndex + 1 }]
      : []),
    ...(Object.prototype.hasOwnProperty.call(error, 'line') && Number.isInteger(error.line)
      ? [{ label: LABEL_MAP.line, value: error.line + 1 }]
      : []),

    // simple strings
    ...(isPresent(error.view) ? [{ label: LABEL_MAP.view, value: error.view }] : []),

    // include slot/description/etc if they were put on the top-level error (some detectors do)
    ...(isPresent(error.slot) ? [{ label: LABEL_MAP.slot, value: error.slot }] : []),
    ...(isPresent(error.location) ? [{ label: LABEL_MAP.location, value: error.location }] : []),
    ...(isPresent(error.description) ? [{ label: LABEL_MAP.description, value: error.description }] : []),
    ...(isPresent(error.expected_speed) ? [{ label: LABEL_MAP.expected_speed, value: error.expected_speed }] : []),
    ...(isPresent(error.actual_speed) ? [{ label: LABEL_MAP.actual_speed, value: error.actual_speed }] : [])
  ];

  lines.push(...ownFields);

  // Remove duplicates (same label+value pairs)
  const seen = new Set();
  return lines.filter(({ label = '', value = '' }) => {
    const key = `${label}::${value}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

// ------------------------------------------

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
        <ErrorTriangleIcon />
      </div>
      <span className="error-count">{errorCount}</span>
    </button>
  );
};

export const ErrorSummaryModal = ({ errors, isOpen, onClose, onNavigateToSection }) => {
  const [collapsedSections, setCollapsedSections] = useState(new Set());

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
    if (e.target === e.currentTarget) onClose();
  };

  const handleErrorClick = (error) => {
    onNavigateToSection(error);
    onClose();
  };

  const toggleSectionCollapse = (sectionTitle) => {
    const next = new Set(collapsedSections);
    if (next.has(sectionTitle)) next.delete(sectionTitle);
    else next.add(sectionTitle);
    setCollapsedSections(next);
  };

  const groupedErrors = errors.reduce((acc, error) => {
    const key = error.sectionTitle;
    if (!acc[key]) acc[key] = [];
    acc[key].push(error);
    return acc;
  }, {});

  return (
    <div className="error-modal-backdrop" onClick={handleBackdropClick}>
      <div className="error-modal">
        <div className="error-modal-header">
          <h2>Critical Items</h2>
          <button className="error-modal-close" onClick={onClose} aria-label="Close error summary">
            &times;
          </button>
        </div>
        <div className="error-modal-content">
          <div className="error-summary-stats">
            <p>
              {errors.length} critical item{errors.length !== 1 ? 's' : ''} found across{' '}
              {Object.keys(groupedErrors).length} section
              {Object.keys(groupedErrors).length !== 1 ? 's' : ''}
            </p>
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
                      <ChevronDownIcon
                        style={{
                          transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
                          transition: 'transform 0.2s ease'
                        }}
                      />
                    </button>
                  </div>

                  {!isCollapsed && (
                    <ul className="error-items">
                      {sectionErrors.map((error, index) => {
                        const details = buildDetailLines(error);
                        return (
                          <li key={index} className="error-item">
                            <button
                              className="error-link"
                              onClick={() => handleErrorClick(error)}
                              title="Click to navigate to this error"
                            >
                              {/* 1) Type first (always) */}
                              <div className="error-type">{getErrorTypeDisplay(error.type)}</div>

                              {/* 2) Value second (always if provided) */}
                              {isPresent(error.value) && (
                                <div className="error-value">"{error.value}"</div>
                              )}

                              {/* 3) Dynamic details (only fields that exist) */}
                              {details.length > 0 && (
                                <div className="error-details">
                                  {details.map((d, i) => (
                                    <div key={i} className="device-detail">
                                      {d.label ? `${d.label}: ${d.value}` : d.value}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </button>
                          </li>
                        );
                      })}
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
