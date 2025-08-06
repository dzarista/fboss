import { forwardRef, useState } from 'react';
import { getRowStyling } from './ErrorDetection';

// Section Content Renderer Component
export const SectionContentRenderer = ({ section, sectionIndex }) => {
  const [selectedI2CEntry, setSelectedI2CEntry] = useState(null);

  try {
    if (!section || !section.parsed_data) {
      return <div className="section-text-content">No content available</div>;
    }

    const { parsed_data } = section;

  if (parsed_data.type === 'raw') {
    return <pre className="section-text-content">{parsed_data.data || 'No content available'}</pre>;
  }

  if (parsed_data.type === 'key_value') {
    const data = parsed_data.data || {};

    // Handle case where data might not be an object
    if (typeof data !== 'object' || data === null) {
      return <div className="section-text-content">Invalid key-value data format</div>;
    }

    const entries = Object.entries(data);
    if (entries.length === 0) {
      return <div className="section-text-content">No key-value data available</div>;
    }

    return (
      <div className="key-value-container">
        <table className="section-table key-value-table">
          <tbody>
            {entries.map(([key, value], idx) => (
              <tr key={idx}>
                <td className="key-col">{key}</td>
                <td className="value-col">{value !== null && value !== undefined ? String(value) : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (parsed_data.type === 'table' || parsed_data.type === 'temperature_table') {
    return (
      <div className="table-container">
        {parsed_data.headers && parsed_data.headers.length > 0 ? (
          <table className="section-table">
            <thead>
              <tr>
                {parsed_data.headers.map((header, idx) => (
                  <th key={idx}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {parsed_data.rows && parsed_data.rows.map((row, rowIdx) => {
                // Determine row styling based on content and anomalies
                let rowClass = '';
                try {
                  rowClass = getRowStyling(row, rowIdx, section.title, parsed_data.anomalies);
                } catch (error) {
                  console.error('Error in getRowStyling:', error);
                  rowClass = '';
                }

                return (
                  <tr key={rowIdx} className={rowClass} id={`section-${sectionIndex}-row-${rowIdx}`}>
                    {parsed_data.headers.map((header, colIdx) => (
                      <td key={colIdx}>{row[header] !== null ? String(row[header]) : ''}</td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="section-text-content">No table data available</div>
        )}
      </div>
    );
  }

  if (parsed_data.type === 'i2c_dump') {
    // Backend provides 'data' field, not 'registers'
    const registers = parsed_data.data;

    // Safety check for registers
    if (!registers || typeof registers !== 'object') {
      return <div className="section-text-content">No I2C dump data available</div>;
    }

    const registerEntries = Object.entries(registers);
    if (registerEntries.length === 0) {
      return <div className="section-text-content">No I2C registers found</div>;
    }

    return (
      <div className="i2c-dump-container">
        {selectedI2CEntry ? (
          // Bit ranges view
          <div className="bit-ranges-view">
            <div className="bit-ranges-header">
              <button
                className="back-button"
                onClick={() => setSelectedI2CEntry(null)}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <polyline points="15,18 9,12 15,6"></polyline>
                </svg>
              </button>
              <div className="bit-ranges-title">
                Bit Fields for {selectedI2CEntry.address} ({selectedI2CEntry.data.command}) - Value: {selectedI2CEntry.data.value}
              </div>
            </div>
            {selectedI2CEntry.data.bitRanges && selectedI2CEntry.data.bitRanges.length > 0 ? (
              <table className="section-table bit-ranges-table">
                <thead>
                  <tr>
                    <th>Bits</th>
                    <th>Name</th>
                    <th>Value</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedI2CEntry.data.bitRanges.map((bitRange, bitIdx) => (
                    <tr key={bitIdx}>
                      <td className="bits-col">{bitRange.bits}</td>
                      <td className="bit-name-col">{bitRange.name}</td>
                      <td className="bit-value-col">{bitRange.binary_value} ({bitRange.value})</td>
                      <td className="bit-desc-col">{bitRange.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="no-bit-ranges">No bit range information available for this command.</div>
            )}
          </div>
        ) : (
          // Main table view
          <table className="section-table i2c-dump-table">
            <thead>
              <tr>
                <th>Address</th>
                <th>Command</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {registerEntries.map(([address, regData]) => (
                <tr key={address}>
                  <td className="address-col">{address}</td>
                  <td className="command-col">
                    {regData.bitRanges && regData.bitRanges.length > 0 ? (
                      <button
                        className="command-link"
                        onClick={() => setSelectedI2CEntry({ address, data: regData })}
                        title="Click to view bit ranges"
                      >
                        {regData.command || 'Unknown'}
                      </button>
                    ) : (
                      <span>{regData.command || 'Unknown'}</span>
                    )}
                  </td>
                  <td className="value-col">{regData.value || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    );
  }

  if (parsed_data.type === 'lspci') {
    return (
      <div className="lspci-container">
        {parsed_data.devices && parsed_data.devices.length > 0 ? (
          <div className="lspci-devices">
            {parsed_data.devices.map((device, idx) => {
              // Check if this device has a speed mismatch anomaly
              const hasSpeedMismatch = parsed_data.anomalies?.some(
                anomaly => anomaly.type === 'pcie_speed_mismatch' && anomaly.device_index === idx
              );

              return (
                <div
                  key={idx}
                  className={`lspci-device ${hasSpeedMismatch ? 'speed-mismatch' : ''}`}
                  id={`section-${sectionIndex}-device-${idx}`}
                >
                  <div className="device-header">
                    <span className="device-id">{device.slot}</span>
                    <span className="device-class">{device.class}</span>
                    <span className="device-description">{device.description}</span>
                  </div>
                  {device.details && device.details.trim() && (
                    <div className="device-details">
                      <pre className="device-detail">{device.details}</pre>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="section-text-content">No LSPCI data available</div>
        )}
      </div>
    );
  }

    // Fallback for unknown format
    return <pre className="section-text-content">No content available</pre>;
  } catch (error) {
    console.error('Error in SectionContentRenderer:', error);
    return (
      <div className="section-error">
        <p>Error rendering section content</p>
        <details>
          <summary>Error details</summary>
          <pre>{error.message}</pre>
        </details>
      </div>
    );
  }
};

// Collapsible Section Component
export const CollapsibleSection = forwardRef(({ title, children, isExpanded, onToggle, isFullscreen, onFullscreenToggle, isActive, onActivate }, ref) => {
  const handleToggleExpanded = (e) => {
    e.stopPropagation();
    onToggle();
  };

  const handleFullscreenToggle = (e) => {
    e.stopPropagation();
    onFullscreenToggle();
  };

  const handleSectionClick = () => {
    onActivate();
  };

  return (
    <div
      ref={ref}
      className={`section-card ${isFullscreen ? 'fullscreen' : ''} ${isActive ? 'active' : ''}`}
      onClick={handleSectionClick}
    >
      <div className="section-header">
        <h3 className="section-title">{title}</h3>
        <div className="section-header-controls">
          <button
            className="fullscreen-button"
            onClick={handleFullscreenToggle}
            title={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
            aria-label={isFullscreen ? "Exit Fullscreen" : "Enter Fullscreen"}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              {isFullscreen ? (
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
              ) : (
                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
              )}
            </svg>
          </button>
          {!isFullscreen && (
            <button
              className={`section-toggle ${isExpanded ? 'expanded' : 'collapsed'}`}
              onClick={handleToggleExpanded}
              title={isExpanded ? "Collapse section" : "Expand section"}
              aria-label={isExpanded ? "Collapse section" : "Expand section"}
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="6,9 12,15 18,9"></polyline>
              </svg>
            </button>
          )}
        </div>
      </div>
      <div className={`section-content-wrapper ${isExpanded ? 'expanded' : 'collapsed'}`}>
        <div className="section-content">
          {children}
        </div>
      </div>
    </div>
  );
});
