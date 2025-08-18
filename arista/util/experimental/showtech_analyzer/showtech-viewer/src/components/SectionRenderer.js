import { forwardRef, useState, useRef, useLayoutEffect } from 'react';
import { getRowStyling } from './ErrorDetection';
import { BackArrowIcon, ChevronDownIcon } from '../assets/icons/Icon';

// NOTE: Ensure in CSS that the scroller has a fixed height + overflow
// .section-content-view.structured-view { max-height: 60vh; overflow-y: auto; }

export const SectionContentRenderer = ({ section, sectionIndex, isRawMode, rawContent }) => {
  const [selectedI2CEntry, setSelectedI2CEntry] = useState(null);

  // Single scroller that contains BOTH the main table and the overlay
  const structuredScrollerRef = useRef(null);
  const rawScrollerRef = useRef(null);

  // Independent scroll memories for the two modes shown inside the same scroller
  const i2cMainYRef = useRef(0);
  const i2cOverlayYRef = useRef(0);

  // Independent scroll memories for raw vs structured views
  const rawScrollYRef = useRef(0);
  const structuredScrollYRef = useRef(0);

  // Switch main -> overlay: save main position, then show overlay
  const openI2COverlay = (entry) => {
    const sc = structuredScrollerRef.current;
    if (sc) i2cMainYRef.current = sc.scrollTop;
    setSelectedI2CEntry(entry);
  };

  // Switch overlay -> main: save overlay position, then show main
  const backToI2CMain = () => {
    const sc = structuredScrollerRef.current;
    if (sc) i2cOverlayYRef.current = sc.scrollTop;
    setSelectedI2CEntry(null);
  };

  // On every flip, restore the scroller to the last saved position for that view
  useLayoutEffect(() => {
    const sc = structuredScrollerRef.current;
    if (!sc) return;
    const y = selectedI2CEntry ? i2cOverlayYRef.current : i2cMainYRef.current;
    sc.scrollTop = y || 0;
    // A second pass next frame helps if layout shifts on toggle
    requestAnimationFrame(() => {
      if (structuredScrollerRef.current) structuredScrollerRef.current.scrollTop = y || 0;
    });
  }, [selectedI2CEntry]);

  try {
    if (!section || !section.parsed_data) {
      return <div className="section-text-content">No content available</div>;
    }

    const { parsed_data } = section;

    if (parsed_data.type === 'raw') {
      return <pre className="section-text-content">{rawContent || 'No content available'}</pre>;
    }

    return (
      <div className="section-content-container">
        {/* Raw View */}
        <div
          className="section-content-view raw-view"
          style={{ display: isRawMode ? 'block' : 'none' }}
        >
          <pre className="section-text-content">{rawContent || 'No raw content available'}</pre>
        </div>

        {/* Structured View: THIS is the scroller */}
        <div
          ref={structuredScrollerRef}
          className="section-content-view structured-view"
          style={{ display: isRawMode ? 'none' : 'block' }}
        >
          {renderStructuredContent(
            parsed_data,
            selectedI2CEntry,
            openI2COverlay,
            backToI2CMain,
            sectionIndex,
            section
          )}
        </div>
      </div>
    );
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

// Helper function to render structured content
const renderStructuredContent = (
  parsed_data,
  selectedI2CEntry,
  openI2COverlay,
  backToI2CMain,
  sectionIndex,
  section
) => {
  if (parsed_data.type === 'key_value') {
    const data = parsed_data.data || {};
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
                <td className="value-col">
                  {value !== null && value !== undefined ? String(value) : ''}
                </td>
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
              {parsed_data.rows &&
                parsed_data.rows.map((row, rowIdx) => {
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
    const registers = parsed_data.data;
    if (!registers || typeof registers !== 'object') {
      return <div className="section-text-content">No I2C dump data available</div>;
    }
    const registerEntries = Object.entries(registers);
    if (registerEntries.length === 0) {
      return <div className="section-text-content">No I2C registers found</div>;
    }

    return (
      <div className="i2c-dump-container">
        {/* Overlay content (bit ranges) */}
        <div className="i2c-view overlay-view" style={{ display: selectedI2CEntry ? 'block' : 'none' }}>
          {selectedI2CEntry && (
            <div className="bit-ranges-view">
              <div className="bit-ranges-header">
                <button className="back-button" onClick={backToI2CMain}>
                  <BackArrowIcon />
                </button>
                <div className="bit-ranges-title">
                  Bit Fields for {selectedI2CEntry.address} ({selectedI2CEntry.data.command}) - Value:{' '}
                  {selectedI2CEntry.data.value}
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
                        <td className="bit-value-col">
                          {bitRange.binary_value} ({bitRange.value})
                        </td>
                        <td className="bit-desc-col">{bitRange.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="no-bit-ranges">No bit range information available for this command.</div>
              )}
            </div>
          )}
        </div>

        {/* Main table content */}
        <div className="i2c-view main-table-view" style={{ display: selectedI2CEntry ? 'none' : 'block' }}>
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
                        onClick={() => openI2COverlay({ address, data: regData })}
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
        </div>
      </div>
    );
  }

  if (parsed_data.type === 'lspci') {
    return (
      <div className="lspci-container">
        {parsed_data.devices && parsed_data.devices.length > 0 ? (
          <div className="lspci-devices">
            {parsed_data.devices.map((device, idx) => {
              const hasSpeedMismatch = parsed_data.anomalies?.some(
                (anomaly) => anomaly.type === 'pcie_speed_mismatch' && anomaly.device_index === idx
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
                      <span className={`status-indicator ${row[header]?.toLowerCase()}`}>{row[header]}</span>
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

            {/* Basic Properties */}
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

            {/* Lane Data */}
            {Object.entries(portData).map(([sectionName, sectionData]) => {
              if (typeof sectionData !== 'object' || !sectionData ||
                  !Object.values(sectionData).some(val => Array.isArray(val))) {
                return null;
              }
              const firstArray = Object.values(sectionData).find(val => Array.isArray(val));
              const numLanes = firstArray ? firstArray.length : 8;

              return (
                <div key={sectionName} className="table-container">
                  <h4 className="table-title">{sectionName}</h4>
                  <table className="section-table">
                    <thead>
                      <tr>
                        <th>Property</th>
                        {Array.from({ length: numLanes }, (_, i) => <th key={i}>Lane {i + 1}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(sectionData).map(([property, values]) => (
                        <tr key={property}>
                          <td><strong>{property}</strong></td>
                          {Array.isArray(values)
                            ? values.map((value, i) => <td key={i}>{value}</td>)
                            : Array.from({ length: numLanes }, (_, i) => <td key={i}>{i === 0 ? values : 'N/A'}</td>)
                          }
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

            {interfaceData.sections && Object.entries(interfaceData.sections).map(([sectionName, sectionData]) => {
              if (sectionName === 'RS FEC') {
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

                    {sectionData.codeword_stats && (
                      <table className="section-table">
                        <thead>
                          <tr>
                            <th>Symbol Errors</th>
                            <th># of codewords</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sectionData.codeword_stats.map((row, i) => (
                            <tr key={i}>
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
                if (sectionData.length === 0) return null;
                const headers = Object.keys(sectionData[0]);
                return (
                  <div key={sectionName} className="table-container">
                    <h4 className="table-title">{sectionName}</h4>
                    <table className="section-table">
                      <thead>
                        <tr>
                          {headers.map((h, i) => <th key={i}>{h}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {sectionData.map((row, i) => (
                          <tr key={i}>
                            {headers.map((h, j) => <td key={j}>{row[h] || 'N/A'}</td>)}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                );
              } else {
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

  return <pre className="section-text-content">No content available</pre>;
};

// Collapsible Section Component
export const CollapsibleSection = forwardRef(
  ({ title, children, isExpanded, onToggle, isActive, onActivate, isRawMode, onToggleRaw, isVisible = true }, ref) => {
    const handleToggleExpanded = (e) => {
      e.stopPropagation();
      onActivate();
      onToggle();
    };

    const handleToggleRaw = (e) => {
      e.stopPropagation();
      onActivate();
      if (onToggleRaw) onToggleRaw();
    };

    const handleSectionClick = () => {
      onActivate();
    };

    return (
      <div
        ref={ref}
        className={`section-card ${isActive ? 'active' : ''}`}
        onClick={handleSectionClick}
        style={{ display: isVisible ? 'block' : 'none' }}
      >
        <div className="section-header">
          <h3 className="section-title">{title}</h3>
          <div className="section-header-controls">
            {onToggleRaw && (
              <button
                className="control-button"
                onClick={handleToggleRaw}
                title={isRawMode ? 'Show structured data' : 'Show raw data'}
                aria-label={isRawMode ? 'Show structured data' : 'Show raw data'}
              >
                {isRawMode ? 'Show Structured' : 'Show Raw'}
              </button>
            )}
            <button
              className={`section-toggle ${isExpanded ? 'expanded' : 'collapsed'}`}
              onClick={handleToggleExpanded}
              title={isExpanded ? 'Collapse section' : 'Expand section'}
              aria-label={isExpanded ? 'Collapse section' : 'Expand section'}
            >
              <ChevronDownIcon />
            </button>
          </div>
        </div>
        <div className={`section-content-wrapper ${isExpanded ? 'expanded' : 'collapsed'}`}>
          <div className="section-content">{children}</div>
        </div>
      </div>
    );
  }
);
