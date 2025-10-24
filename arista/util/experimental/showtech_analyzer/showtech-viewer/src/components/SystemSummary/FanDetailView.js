import React, { useState } from 'react';
import { BackArrowIcon } from '../../assets/icons/Icon';
import { CollapsibleSection } from '../SectionRenderer';

const FanDetailView = ({ fanNum, fanData, sections, onBack }) => {
  const [expandedSections, setExpandedSections] = useState(new Set(['fan-data', 'fan-sensors']));
  const [activeSection, setActiveSection] = useState(null);
  const toggleSection = (k) => setExpandedSections((prev) => { const n = new Set(prev); n.has(k) ? n.delete(k) : n.add(k); return n; });
  const activateSection = (k) => setActiveSection(k);

  // Get the full sensor table data for this Fan
  const getSensorTableData = () => {
    const sensorSection = sections?.find((s) => s.title === 'fboss2 show environment sensor');
    if (!sensorSection || sensorSection.parsed_data?.type !== 'table') return null;

    const allRows = sensorSection.parsed_data.rows || [];
    const headers = sensorSection.parsed_data.headers || [];

    // Filter rows that belong to this Fan (various patterns)
    const fanRows = allRows.filter(row => {
      const sensor = row.Sensor || '';
      // Look for patterns like FAN1, Fan1, FAN_1, etc.
      return sensor.match(new RegExp(`^(FAN|Fan)[_\\s]*${fanNum}[_\\s]`, 'i')) ||
             sensor.match(new RegExp(`^(FAN|Fan)[_\\s]*${fanNum}$`, 'i'));
    });

    return {
      headers,
      rows: fanRows
    };
  };

  const sensorTableData = getSensorTableData();

  return (
    <div className="port-detail-view">
      <div className="section-header">
        <div className="section-header-left">
          <button className="back-button" onClick={onBack}>
            <BackArrowIcon />
          </button>
          <h3 className="section-title">Fan {fanNum} Details</h3>
        </div>
      </div>

      <div className="sections-container">
        {fanData && Object.keys(fanData).length > 0 && (
          <CollapsibleSection
            title={`FANS Section - Fan ${fanNum}`}
            isExpanded={expandedSections.has('fan-data')}
            onToggle={() => toggleSection('fan-data')}
            isActive={activeSection === 'fan-data'}
            onActivate={() => activateSection('fan-data')}
          >
            <div className="table-container">
              <table className="section-table">
                <thead>
                  <tr>
                    <th>Property</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(fanData).map(([key, value]) => (
                    <tr key={key}>
                      <td><strong>{key}</strong></td>
                      <td>{value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CollapsibleSection>
        )}

        {sensorTableData && sensorTableData.rows.length > 0 && (
          <CollapsibleSection
            title={`fboss2 show environment sensor - Fan ${fanNum}`}
            isExpanded={expandedSections.has('fan-sensors')}
            onToggle={() => toggleSection('fan-sensors')}
            isActive={activeSection === 'fan-sensors'}
            onActivate={() => activateSection('fan-sensors')}
          >
            <div className="table-container">
              <table className="section-table">
                <thead>
                  <tr>
                    {sensorTableData.headers.map((header, idx) => (
                      <th key={idx}>{header}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sensorTableData.rows.map((row, rowIdx) => (
                    <tr key={rowIdx}>
                      {sensorTableData.headers.map((header, colIdx) => (
                        <td key={colIdx}>{row[header] || ''}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CollapsibleSection>
        )}

        {(!fanData || Object.keys(fanData).length === 0) && (!sensorTableData || sensorTableData.rows.length === 0) && (
          <CollapsibleSection
            title="No Data Available"
            isExpanded={expandedSections.has('no-data')}
            onToggle={() => toggleSection('no-data')}
            isActive={activeSection === 'no-data'}
            onActivate={() => activateSection('no-data')}
          >
            <div className="table-container"><p>No fan data or sensor information available for Fan {fanNum}.</p></div>
          </CollapsibleSection>
        )}
      </div>
    </div>
  );
};

export default FanDetailView;
