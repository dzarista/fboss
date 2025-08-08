import React, { useState } from 'react';
import { CollapsibleSection } from '../SectionRenderer';

const PSUDetailView = ({ psuNum, psuData, psuDebugData, onBack }) => {
  const [expandedSections, setExpandedSections] = useState(new Set(['psu-debug', 'psu-sensors', 'no-data']));
  const [activeSection, setActiveSection] = useState(null);
  const toggleSection = (k) => setExpandedSections((prev) => { const n = new Set(prev); n.has(k) ? n.delete(k) : n.add(k); return n; });
  const activateSection = (k) => setActiveSection(k);

  const debugInfo = psuDebugData?.[`PSU${psuNum}`]?.properties || {};

  return (
    <div className="port-detail-view">
      <div className="section-header">
        <div className="section-header-left">
          <button className="back-button" onClick={onBack}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="15,18 9,12 15,6"></polyline>
            </svg>
          </button>
          <h3 className="section-title">PSU {psuNum} Details</h3>
        </div>
      </div>

      <div className="sections-container">
        {Object.keys(debugInfo).length > 0 && (
          <CollapsibleSection
            title={`PSU debug info - PSU ${psuNum}`}
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

        {psuData && (
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
                  <tr><th>Property</th><th>Value</th></tr>
                </thead>
                <tbody>
                  <tr><td><strong>Status</strong></td><td>{psuData.status}</td></tr>
                  {psuData.voltage_in && (<tr><td><strong>Voltage In</strong></td><td>{psuData.voltage_in}</td></tr>)}
                  {psuData.voltage_out && (<tr><td><strong>Voltage Out</strong></td><td>{psuData.voltage_out}</td></tr>)}
                  {psuData.power_in && (<tr><td><strong>Power In</strong></td><td>{psuData.power_in}</td></tr>)}
                  {psuData.power_out && (<tr><td><strong>Power Out</strong></td><td>{psuData.power_out}</td></tr>)}
                  {Object.entries(psuData.fans || {}).map(([fanKey, fanValue]) => (
                    <tr key={fanKey}><td><strong>{fanKey}</strong></td><td>{fanValue}</td></tr>
                  ))}
                  {Object.entries(psuData.temperatures || {}).map(([tempKey, tempValue]) => (
                    <tr key={tempKey}><td><strong>{tempKey}</strong></td><td>{tempValue}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CollapsibleSection>
        )}

        {Object.keys(debugInfo).length === 0 && !psuData && (
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
