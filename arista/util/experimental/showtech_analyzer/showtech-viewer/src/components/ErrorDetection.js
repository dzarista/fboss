// Error detection utility functions and logic

// Removed detectCriticalInValue - now using anomalies data directly

// ------- helpers for new generalized anomaly shape -------

// Prefer section.anomalies (new) but fall back to section.parsed_data.anomalies (old)
const pickAnomalies = (section) => {
  if (Array.isArray(section?.anomalies)) return section.anomalies;
  if (Array.isArray(section?.parsed_data?.anomalies)) return section.parsed_data.anomalies;
  return [];
};

// Normalize legacy vs new fields so downstream code stays simple
const normalizeAnomaly = (a = {}) => {
  // Unify row/row_index and provide a default for existing code paths
  const row_index =
    typeof a.row_index === 'number' ? a.row_index :
    typeof a.row === 'number' ? a.row : undefined;

  // Keep a stable port_name fallback used in older code
  const port_name = a.port_name ?? a.value;

  return {
    ...a,
    row_index,
    port_name
  };
};

// Function to highlight rows based on anomaly severity
export const getRowStyling = (row, rowIndex, sectionTitle, anomalies) => {
  try {
    // Safety check for row and anomalies
    if (!row || typeof row !== 'object' || !anomalies || !Array.isArray(anomalies)) {
      return '';
    }

    // Find anomaly for this row (support both row_index and row)
    const rowAnomaly = anomalies
      .map(normalizeAnomaly)
      .find(anomaly => anomaly.row_index === rowIndex);

    if (rowAnomaly) {
      // Return CSS class based on severity
      if (rowAnomaly.severity === 'high') {
        return 'high-severity-row'; // Red highlight
      } else if (rowAnomaly.severity === 'medium') {
        return 'medium-severity-row'; // Yellow highlight
      } else {
        return 'critical-row'; // Default red for backward compatibility
      }
    }

    return '';
  } catch (error) {
    console.error('Error in getRowStyling:', error, { row, rowIndex, sectionTitle });
    return '';
  }
};

// Helper functions to extract location/value based on anomaly type
const getLocationForAnomaly = (anomaly) => {
  const a = normalizeAnomaly(anomaly);
  if (a.slot) return `${a.location || 'Device'} (${a.slot})`;
  if (a.location) return a.location;
  return undefined;
};

const getValueForAnomaly = (anomaly) => {
  const a = normalizeAnomaly(anomaly);
  switch (a.type) {
    case 'critical_sensor':
      return a.value;
    case 'port_down':
      return a.port_name;
    case 'missing_device':
      return a.description || a.value;
    case 'pcie_speed_mismatch':
      return `Expected: ${a.expected_speed}, Found: ${a.actual_speed}`;
    default:
      return a.value || a.port_name || a.description || 'Unknown';
  }
};

const getPatternForAnomaly = (anomaly) => {
  const a = normalizeAnomaly(anomaly);
  switch (a.type) {
    case 'missing_device':
      return `Expected ${a.device_type}${a.expected_speed ? ` (${a.expected_speed})` : ''}`;
    case 'pcie_speed_mismatch':
      return `PCIe Device Speed Mismatch: Expected ${a.expected_speed}`;
    case 'regex_match':
      return a.message || `Pattern match${a.field ? `: ${a.field}` : ''}`;
    default:
      return a.message || a.pattern || a.type.replace('_', ' ');
  }
};

const getDeviceInfoForAnomaly = (anomaly) => {
  const a = normalizeAnomaly(anomaly);
  if (a.type === 'missing_device') {
    return {
      slot: a.slot,
      device_type: a.device_type,
      location: a.location,
      description: a.description,
      expected_speed: a.expected_speed
    };
  }
  if (a.type === 'pcie_speed_mismatch') {
    return {
      slot: a.slot,
      device_type: a.device_type,
      location: a.location,
      description: a.description,
      expected_speed: a.expected_speed,
      actual_speed: a.actual_speed
    };
  }
  return null;
};

// General anomaly processor - works for any section type
export const detectSectionErrors = (section, sectionIndex) => {
  const errors = [];
  const sectionTitle = section.title || `Section ${sectionIndex + 1}`;

  // Prefer new location; fallback retained for transition
  const anomalies = pickAnomalies(section);

  anomalies.forEach((anomaly) => {
    const a = normalizeAnomaly(anomaly);

    errors.push({
      sectionIndex,
      sectionTitle,
      type: a.type,
      rowIndex: a.row_index,
      location: getLocationForAnomaly(a),
      value: getValueForAnomaly(a),
      pattern: getPatternForAnomaly(a),
      deviceIndex: a.device_index, // For LSPCI device navigation
      deviceInfo: getDeviceInfoForAnomaly(a),
      span: a.span,
      line: a.line
    });
  });

  return errors;
};

// Optional: helper to get highlight ranges for regex matches in raw view
export const getRegexHighlights = (section) => {
  const anomalies = pickAnomalies(section);
  return anomalies
    .map(normalizeAnomaly)
    .filter(a => a.type === 'regex_match' && a.view === 'raw' && a.span && Number.isInteger(a.line))
    .map(a => ({
      line: a.line,
      start: a.span[0],
      end: a.span[1],
      label: a.field || a.type
    }));
};

// Function to detect all errors in a log file
export const detectAllErrors = (log) => {
  if (!log || !log.sections) return [];

  const allErrors = [];
  log.sections.forEach((section, index) => {
    const sectionErrors = detectSectionErrors(section, index);
    allErrors.push(...sectionErrors);
  });

  return allErrors;
};
