import React, { useState } from 'react';
import { BackArrowIcon } from '../../assets/icons/Icon';
import { CollapsibleSection } from '../SectionRenderer';

const PSUDetailView = ({ psuNum, psuData, psuDebugData, onBack, sections }) => {
  const [expandedSections, setExpandedSections] = useState(new Set(['psu-debug', 'psu-sensors', 'no-data']));
  const [activeSection, setActiveSection] = useState(null);
  const toggleSection = (k) => setExpandedSections((prev) => { const n = new Set(prev); n.has(k) ? n.delete(k) : n.add(k); return n; });
  const activateSection = (k) => setActiveSection(k);

  const debugInfo = psuDebugData?.[`PSU${psuNum}`]?.properties || {};

  // Get the full sensor table data for this PSU
  const getSensorTableData = () => {
    const sensorSection = sections?.find((s) => s.title === 'fboss2 show environment sensor');
    if (!sensorSection || sensorSection.parsed_data?.type !== 'table') return null;

    const allRows = sensorSection.parsed_data.rows || [];
    const headers = sensorSection.parsed_data.headers || [];

    // Filter rows that belong to this PSU
    const psuRows = allRows.filter(row => {
      const sensor = row.Sensor || '';
      return sensor.match(new RegExp(`^PSU${psuNum}_`));
    });

    return {
      headers,
      rows: psuRows
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
          <h3 className="section-title">PSU {psuNum} Details</h3>
        </div>
      </div>

      <div className="sections-container">
        {Object.keys(debugInfo).length > 0 && (
          <CollapsibleSection
            title={`PSU Debug Info - PSU ${psuNum}`}
            isExpanded={expandedSections.has('psu-debug')}
            onToggle={() => toggleSection('psu-debug')}
            isActive={activeSection === 'psu-debug'}
            onActivate={() => activateSection('psu-debug')}
          >
            <div className="table-container">
              <table className="section-table">
                <thead>
                  <tr><th>Property</th><th>Value</th></tr>
                </thead>
                <tbody>
                  {Object.entries(debugInfo).map(([key, value]) => (
                    <tr key={key}><td><strong>{key}</strong></td><td>{value}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CollapsibleSection>
        )}

        {sensorTableData && sensorTableData.rows.length > 0 && (
          <CollapsibleSection
            title={`fboss2 show environment sensor - PSU ${psuNum}`}
            isExpanded={expandedSections.has('psu-sensors')}
            onToggle={() => toggleSection('psu-sensors')}
            isActive={activeSection === 'psu-sensors'}
            onActivate={() => activateSection('psu-sensors')}
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

        {Object.keys(debugInfo).length === 0 && (!sensorTableData || sensorTableData.rows.length === 0) && (
          <CollapsibleSection
            title="No Data Available"
            isExpanded={expandedSections.has('no-data')}
            onToggle={() => toggleSection('no-data')}
            isActive={activeSection === 'no-data'}
            onActivate={() => activateSection('no-data')}
          >
            <div className="table-container"><p>No PSU debug information or sensor data available for PSU {psuNum}.</p></div>
          </CollapsibleSection>
        )}
      </div>
    </div>
  );
};

export default PSUDetailView;
