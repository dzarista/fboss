// Error detection utility functions and logic

// Error detection utility functions - only detect existing critical highlighting
export const detectCriticalInValue = (value) => {
  // This matches the existing logic in SectionContentRenderer for critical row detection
  return value && String(value).toLowerCase().includes('critical');
};

// Function to determine row styling based on port status and anomalies
export const getRowStyling = (row, rowIndex, sectionTitle, anomalies) => {
  try {
    // Safety check for row
    if (!row || typeof row !== 'object') {
      return '';
    }

    // Check for critical values first (highest priority)
    const rowValues = Object.values(row);
    const isCritical = rowValues.some(value => detectCriticalInValue(value));
    if (isCritical) {
      return 'critical-row';
    }

    // Check for port-specific styling (only for fboss2 show port sections)
    if (sectionTitle === 'fboss2 show port') {
      const adminState = row.AdminState;
      const linkState = row.LinkState;
      const transceiver = row.Transceiver;

      // Disabled ports get dark background
      if (adminState === 'Disabled') {
        return 'disabled-port-row';
      }

      // Enabled + Present + Down ports get red background (problem ports)
      if (adminState === 'Enabled' && transceiver === 'Present' && linkState === 'Down') {
        return 'problem-port-row';
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
  switch (anomaly.type) {
    case 'critical_sensor':
      return `Row ${anomaly.row_index + 1}, ${anomaly.field}`;
    case 'port_down':
      return `Row ${anomaly.row_index + 1}`;
    case 'missing_device':
      return `${anomaly.location} (${anomaly.slot})`;
    case 'pcie_speed_mismatch':
      return `${anomaly.location} (${anomaly.slot})`;
    default:
      return anomaly.location || `Row ${(anomaly.row_index || 0) + 1}`;
  }
};

const getValueForAnomaly = (anomaly) => {
  switch (anomaly.type) {
    case 'critical_sensor':
      return anomaly.value;
    case 'port_down':
      return anomaly.port_name;
    case 'missing_device':
      return anomaly.description;
    case 'pcie_speed_mismatch':
      return `Expected: ${anomaly.expected_speed}, Found: ${anomaly.actual_speed}`;
    default:
      return anomaly.value || anomaly.port_name || anomaly.description || 'Unknown';
  }
};

const getPatternForAnomaly = (anomaly) => {
  switch (anomaly.type) {
    case 'missing_device':
      return `Expected ${anomaly.device_type}${anomaly.expected_speed ? ` (${anomaly.expected_speed})` : ''}`;
    case 'pcie_speed_mismatch':
      return `PCIe Device Speed Mismatch: Expected ${anomaly.expected_speed}`;
    default:
      return anomaly.message || anomaly.pattern || anomaly.type.replace('_', ' ');
  }
};

const getDeviceInfoForAnomaly = (anomaly) => {
  if (anomaly.type === 'missing_device') {
    return {
      slot: anomaly.slot,
      device_type: anomaly.device_type,
      location: anomaly.location,
      description: anomaly.description,
      expected_speed: anomaly.expected_speed
    };
  }
  if (anomaly.type === 'pcie_speed_mismatch') {
    return {
      slot: anomaly.slot,
      device_type: anomaly.device_type,
      location: anomaly.location,
      description: anomaly.description,
      expected_speed: anomaly.expected_speed,
      actual_speed: anomaly.actual_speed
    };
  }
  return null;
};

// General anomaly processor - works for any section type
export const detectSectionErrors = (section, sectionIndex) => {
  const errors = [];
  const sectionTitle = section.title || `Section ${sectionIndex + 1}`;

  // Process anomalies from any section type
  if (section.parsed_data?.anomalies && Array.isArray(section.parsed_data.anomalies)) {
    section.parsed_data.anomalies.forEach((anomaly) => {


      errors.push({
        sectionIndex,
        sectionTitle,
        type: anomaly.type,
        location: getLocationForAnomaly(anomaly),
        value: getValueForAnomaly(anomaly),
        pattern: getPatternForAnomaly(anomaly),
        rowIndex: anomaly.row_index || 0,
        deviceIndex: anomaly.device_index, // For LSPCI device navigation
        deviceInfo: getDeviceInfoForAnomaly(anomaly)
      });
    });
  }

  return errors;
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
