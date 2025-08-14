import { forwardRef, useState } from 'react';
import { getRowStyling } from './ErrorDetection';
import { BackArrowIcon, ChevronDownIcon } from '../assets/icons/Icon';
import LoadingSpinner from './LoadingSpinner';

// Section Content Renderer Component
export const SectionContentRenderer = ({ section, sectionIndex, isRawMode, rawContent, isLoadingRaw }) => {
  const [selectedI2CEntry, setSelectedI2CEntry] = useState(null);

  try {
    // Handle raw mode
    if (isRawMode) {
      if (isLoadingRaw) {
        return <LoadingSpinner message="Fetching raw data..." size="medium" />;
      }
      if (rawContent) {
        return <pre className="section-text-content">{rawContent}</pre>;
      }
      return <div className="section-text-content">No raw content available</div>;
    }

    if (!section || !section.parsed_data) {
      return <div className="section-text-content">No content available</div>;
    }

    const { parsed_data } = section;

  // Handle auto-compressed sections
  if (parsed_data.type === 'auto_compressed') {
    return (
      <div className="section-text-content auto-compressed-message">
        <p>{parsed_data.message}</p>
        <p><em>Content size: {parsed_data.content_size?.toLocaleString()} characters</em></p>
      </div>
    );
  }

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
                <BackArrowIcon />
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

  if (parsed_data.type === 'fans') {
    const headers = parsed_data.headers || [];
    const rows = parsed_data.rows || [];

    if (rows.length === 0) {
      return <div className="section-text-content">No fan data available</div>;
    }

    return (
      <div className="table-container">
        <table className="section-table">
          <thead>
            <tr>
              {headers.map((header, idx) => (
                <th key={idx}>{header}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr key={idx} className={getRowStyling(row, sectionIndex)}>
                {headers.map((header, headerIdx) => (
                  <td key={headerIdx}>
                    {header === 'Status' ? (
                      <span className={`status-indicator ${row[header]?.toLowerCase()}`}>
                        {row[header]}
                      </span>
                    ) : (
                      row[header] || 'N/A'
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (parsed_data.type === 'qsfp_util') {
    const ports = parsed_data.ports || [];

    if (ports.length === 0) {
      return <div className="section-text-content">No QSFP data available</div>;
    }

    return (
      <div className="section-text-content">
        {ports.map((portData, idx) => (
          <div key={idx} className="qsfp-port-section">
            <div className="qsfp-port-header">
              <span className="qsfp-port-id">Port {portData.port}</span>
            </div>

            {/* Basic Properties Table */}
            <div className="table-container">
              <table className="section-table">
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(portData).map(([key, value]) => {
                    // Skip port number and complex objects
                    if (key === 'port' || typeof value === 'object') return null;

                    return (
                      <tr key={key}>
                        <td><strong>{key}</strong></td>
                        <td>{value}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Lane Data Tables */}
            {Object.entries(portData).map(([sectionName, sectionData]) => {
              // Only show sections that contain lane data (objects with arrays)
              if (typeof sectionData !== 'object' || !sectionData ||
                  !Object.values(sectionData).some(val => Array.isArray(val))) {
                return null;
              }

              // Get the number of lanes from the first array
              const firstArray = Object.values(sectionData).find(val => Array.isArray(val));
              const numLanes = firstArray ? firstArray.length : 8;

              return (
                <div key={sectionName} className="table-container">
                  <h4 className="table-title">{sectionName}</h4>
                  <table className="section-table">
                    <thead>
                      <tr>
                        <th>Property</th>
                        {Array.from({length: numLanes}, (_, i) => (
                          <th key={i}>Lane {i + 1}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(sectionData).map(([property, values]) => (
                        <tr key={property}>
                          <td><strong>{property}</strong></td>
                          {Array.isArray(values) ? values.map((value, valueIdx) => (
                            <td key={valueIdx}>{value}</td>
                          )) : (
                            // If not an array, show the single value in first column, N/A in others
                            Array.from({length: numLanes}, (_, i) => (
                              <td key={i}>{i === 0 ? values : 'N/A'}</td>
                            ))
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    );
  }

  if (parsed_data.type === 'fboss2_interface_phy') {
    const interfaces = parsed_data.interfaces || [];

    if (interfaces.length === 0) {
      return <div className="section-text-content">No PHY interface data available</div>;
    }

    return (
      <div className="section-text-content">
        {interfaces.map((interfaceData, idx) => (
          <div key={idx} className="qsfp-port-section">
            <div className="qsfp-port-header">
              <span className="qsfp-port-id">Interface {interfaceData.interface}</span>
            </div>

            {/* Basic Properties Table */}
            <div className="table-container">
              <table className="section-table">
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(interfaceData).map(([key, value]) => {
                    // Skip interface name and sections object
                    if (key === 'interface' || key === 'sections') return null;

                    return (
                      <tr key={key}>
                        <td><strong>{key}</strong></td>
                        <td>{value}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* PHY Sections */}
            {interfaceData.sections && Object.entries(interfaceData.sections).map(([sectionName, sectionData]) => {
              if (sectionName === 'RS FEC') {
                // RS FEC section with key-value pairs and codeword stats table
                return (
                  <div key={sectionName} className="table-container">
                    <h4 className="table-title">{sectionName}</h4>

                    {/* Key-value pairs */}
                    <table className="section-table">
                      <thead>
                        <tr>
                          <th>Property</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(sectionData).map(([key, value]) => {
                          if (key === 'codeword_stats') return null;
                          return (
                            <tr key={key}>
                              <td><strong>{key}</strong></td>
                              <td>{value}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>

                    {/* Codeword stats table */}
                    {sectionData.codeword_stats && (
                      <table className="section-table">
                        <thead>
                          <tr>
                            <th>Symbol Errors</th>
                            <th># of codewords</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sectionData.codeword_stats.map((row, idx) => (
                            <tr key={idx}>
                              <td>{row['Symbol Errors']}</td>
                              <td>{row['# of codewords']}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                );
              } else if (Array.isArray(sectionData)) {
                // RX PMD or TX PMD sections with lane data
                if (sectionData.length === 0) return null;

                const headers = Object.keys(sectionData[0]);

                return (
                  <div key={sectionName} className="table-container">
                    <h4 className="table-title">{sectionName}</h4>
                    <table className="section-table">
                      <thead>
                        <tr>
                          {headers.map((header, idx) => (
                            <th key={idx}>{header}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {sectionData.map((row, idx) => (
                          <tr key={idx}>
                            {headers.map((header, headerIdx) => (
                              <td key={headerIdx}>{row[header] || 'N/A'}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              } else {
                // Other sections with simple key-value pairs
                return (
                  <div key={sectionName} className="table-container">
                    <h4 className="table-title">{sectionName}</h4>
                    <table className="section-table">
                      <thead>
                        <tr>
                          <th>Property</th>
                          <th>Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(sectionData).map(([key, value]) => (
                          <tr key={key}>
                            <td><strong>{key}</strong></td>
                            <td>{value}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              }
            })}
          </div>
        ))}
      </div>
    );
  }

  if (parsed_data.type === 'psu_debug') {
    const psuSlots = parsed_data.psu_slots || [];

    if (psuSlots.length === 0) {
      return <div className="section-text-content">No PSU debug data available</div>;
    }

    return (
      <div className="psu-debug-container">
        {psuSlots.map((psuSlot, idx) => (
          <div key={idx} className="psu-debug-slot">
            <div className="psu-debug-header">
              <h4 className="psu-slot-title">Power Supply Slot {psuSlot.slot}</h4>
            </div>

            <div className="table-container">
              <table className="section-table">
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(psuSlot.properties || {}).map(([key, value]) => (
                    <tr key={key}>
                      <td className="psu-property-key">{key}</td>
                      <td className="psu-property-value">{value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
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
export const CollapsibleSection = forwardRef(({ title, children, isExpanded, onToggle, isActive, onActivate, isRawMode, isLoadingRaw, onToggleRaw }, ref) => {
  const handleToggleExpanded = (e) => {
    e.stopPropagation();
    // Activate the section when expand/collapse is clicked
    onActivate();
    onToggle();
  };

  const handleToggleRaw = (e) => {
    e.stopPropagation();
    // Activate the section when raw toggle is clicked
    onActivate();
    if (onToggleRaw) {
      onToggleRaw();
    }
  };

  const handleSectionClick = () => {
    onActivate();
  };

  return (
    <div
      ref={ref}
      className={`section-card ${isActive ? 'active' : ''}`}
      onClick={handleSectionClick}
    >
      <div className="section-header">
        <h3 className="section-title">{title}</h3>
        <div className="section-header-controls">
          {onToggleRaw && (
            <button
              className="control-button"
              onClick={handleToggleRaw}
              title={isLoadingRaw ? "Loading data..." : (isRawMode ? "Show structured data" : "Show raw data")}
              aria-label={isLoadingRaw ? "Loading data..." : (isRawMode ? "Show structured data" : "Show raw data")}
              disabled={isLoadingRaw}
            >
              {isLoadingRaw ? (
                <span className="button-loading">
                  <span className="button-spinner"></span>
                  Loading data...
                </span>
              ) : (
                isRawMode ? 'Show Structured' : 'Show Raw'
              )}
            </button>
          )}
          <button
            className={`section-toggle ${isExpanded ? 'expanded' : 'collapsed'}`}
            onClick={handleToggleExpanded}
            title={isExpanded ? "Collapse section" : "Expand section"}
            aria-label={isExpanded ? "Collapse section" : "Expand section"}
          >
            <ChevronDownIcon />
          </button>
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