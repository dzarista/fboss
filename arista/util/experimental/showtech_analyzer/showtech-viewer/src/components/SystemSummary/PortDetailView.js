import React, { useState } from 'react';
import { CollapsibleSection } from '../SectionRenderer';

const PortDetailView = ({ portNum, portData, phyData, interfaceData, portType, onBack }) => {
  const [expandedSections, setExpandedSections] = useState(() => {
    const all = new Set(['qsfp-basic']);
    Object.entries(portData).forEach(([sectionName, sectionData]) => {
      if (typeof sectionData === 'object' && sectionData && Object.values(sectionData).some((val) => Array.isArray(val))) {
        all.add(`qsfp-${sectionName}`);
      }
    });
    if (Array.isArray(phyData) && phyData.length > 0) {
      phyData.forEach((singlePhyData) => {
        all.add(`phy-${singlePhyData.interface}`);
        if (singlePhyData.sections) {
          Object.keys(singlePhyData.sections).forEach((sectionName) => {
            all.add(`phy-${singlePhyData.interface}-${sectionName}-props`);
            all.add(`phy-${singlePhyData.interface}-${sectionName}-stats`);
            all.add(`phy-${singlePhyData.interface}-${sectionName}`);
          });
        }
      });
    }
    if (interfaceData && Object.keys(interfaceData).length > 0) {
      Object.keys(interfaceData).forEach((sectionTitle) => all.add(sectionTitle));
    }
    return all;
  });
  const [activeSection, setActiveSection] = useState(null);
  const toggleSection = (k) => setExpandedSections((prev) => { const n = new Set(prev); n.has(k) ? n.delete(k) : n.add(k); return n; });
  const activateSection = (k) => setActiveSection(k);

  return (
    <div className="port-detail-view">
      <div className="section-header">
        <div className="section-header-left">
          <button className="back-button" onClick={onBack}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="15,18 9,12 15,6"></polyline>
            </svg>
          </button>
          <h3 className="section-title">Port {portNum} Details</h3>
          <span className="port-type-badge">{portType === 'eth' ? 'Ethernet' : portType === 'fab' ? 'Fabric' : 'Disabled'}</span>
        </div>
      </div>

      <div className="sections-container">
        <CollapsibleSection
          title={`wedge_qsfp_util - Port ${portNum}`}
          isExpanded={expandedSections.has('qsfp-basic')}
          onToggle={() => toggleSection('qsfp-basic')}
          isActive={activeSection === 'qsfp-basic'}
          onActivate={() => activateSection('qsfp-basic')}
        >
          <div className="table-container">
            <table className="section-table">
              <thead><tr><th>Property</th><th>Value</th></tr></thead>
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
        </CollapsibleSection>

        {Object.entries(portData).map(([sectionName, sectionData]) => {
          if (typeof sectionData !== 'object' || !sectionData || !Object.values(sectionData).some((val) => Array.isArray(val))) return null;
          const firstArray = Object.values(sectionData).find((val) => Array.isArray(val));
          const numLanes = firstArray ? firstArray.length : 8;
          return (
            <CollapsibleSection
              key={sectionName}
              title={`wedge_qsfp_util - ${sectionName}`}
              isExpanded={expandedSections.has(`qsfp-${sectionName}`)}
              onToggle={() => toggleSection(`qsfp-${sectionName}`)}
              isActive={activeSection === `qsfp-${sectionName}`}
              onActivate={() => activateSection(`qsfp-${sectionName}`)}
            >
              <div className="table-container">
                <table className="section-table">
                  <thead>
                    <tr>
                      <th>Property</th>
                      {Array.from({ length: numLanes }, (_, i) => (
                        <th key={i}>Lane {i + 1}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(sectionData).map(([property, values]) => (
                      <tr key={property}>
                        <td><strong>{property}</strong></td>
                        {Array.isArray(values)
                          ? values.map((value, valueIdx) => <td key={valueIdx}>{value}</td>)
                          : Array.from({ length: numLanes }, (_, i) => <td key={i}>{i === 0 ? values : 'N/A'}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CollapsibleSection>
          );
        })}

        {Array.isArray(phyData) && phyData.length > 0 &&
          phyData.map((singlePhyData, phyIdx) => (
            <React.Fragment key={phyIdx}>
              <CollapsibleSection
                title={`fboss2 show interface phy - Interface ${singlePhyData.interface}`}
                isExpanded={expandedSections.has(`phy-${singlePhyData.interface}`)}
                onToggle={() => toggleSection(`phy-${singlePhyData.interface}`)}
                isActive={activeSection === `phy-${singlePhyData.interface}`}
                onActivate={() => activateSection(`phy-${singlePhyData.interface}`)}
              >
                <div className="table-container">
                  <table className="section-table">
                    <thead><tr><th>Property</th><th>Value</th></tr></thead>
                    <tbody>
                      {Object.entries(singlePhyData).map(([key, value]) => {
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
              </CollapsibleSection>

              {singlePhyData.sections &&
                Object.entries(singlePhyData.sections).map(([sectionName, sectionData]) => {
                  if (sectionName === 'RS FEC') {
                    return (
                      <React.Fragment key={sectionName}>
                        <CollapsibleSection
                          title={`${sectionName} - Properties - Interface ${singlePhyData.interface}`}
                          isExpanded={expandedSections.has(`phy-${singlePhyData.interface}-${sectionName}-props`)}
                          onToggle={() => toggleSection(`phy-${singlePhyData.interface}-${sectionName}-props`)}
                          isActive={activeSection === `phy-${singlePhyData.interface}-${sectionName}-props`}
                          onActivate={() => activateSection(`phy-${singlePhyData.interface}-${sectionName}-props`)}
                        >
                          <div className="table-container">
                            <table className="section-table">
                              <thead><tr><th>Property</th><th>Value</th></tr></thead>
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
                          </div>
                        </CollapsibleSection>

                        {sectionData.codeword_stats && (
                          <CollapsibleSection
                            title={`${sectionName} - Codeword Statistics - Interface ${singlePhyData.interface}`}
                            isExpanded={expandedSections.has(`phy-${singlePhyData.interface}-${sectionName}-stats`)}
                            onToggle={() => toggleSection(`phy-${singlePhyData.interface}-${sectionName}-stats`)}
                            isActive={activeSection === `phy-${singlePhyData.interface}-${sectionName}-stats`}
                            onActivate={() => activateSection(`phy-${singlePhyData.interface}-${sectionName}-stats`)}
                          >
                            <div className="table-container">
                              <table className="section-table">
                                <thead><tr><th>Symbol Errors</th><th># of codewords</th></tr></thead>
                                <tbody>
                                  {sectionData.codeword_stats.map((row, idx) => (
                                    <tr key={idx}><td>{row['Symbol Errors']}</td><td>{row['# of codewords']}</td></tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </CollapsibleSection>
                        )}
                      </React.Fragment>
                    );
                  }

                  if (Array.isArray(sectionData)) {
                    if (sectionData.length === 0) return null;
                    const headers = Object.keys(sectionData[0]);
                    return (
                      <CollapsibleSection
                        key={sectionName}
                        title={`${sectionName} - Interface ${singlePhyData.interface}`}
                        isExpanded={expandedSections.has(`phy-${singlePhyData.interface}-${sectionName}`)}
                        onToggle={() => toggleSection(`phy-${singlePhyData.interface}-${sectionName}`)}
                        isActive={activeSection === `phy-${singlePhyData.interface}-${sectionName}`}
                        onActivate={() => activateSection(`phy-${singlePhyData.interface}-${sectionName}`)}
                      >
                        <div className="table-container">
                          <table className="section-table">
                            <thead>
                              <tr>
                                {headers.map((header, idx) => (<th key={idx}>{header}</th>))}
                              </tr>
                            </thead>
                            <tbody>
                              {sectionData.map((row, idx) => (
                                <tr key={idx}>
                                  {headers.map((header, headerIdx) => (
                                    <td key={headerIdx}>{row[header] ?? 'N/A'}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </CollapsibleSection>
                    );
                  }
                  return null;
                })}
            </React.Fragment>
          ))}

        {interfaceData && Object.keys(interfaceData).length > 0 &&
          Object.entries(interfaceData).map(([sectionTitle, interfaces]) => {
            if (!interfaces || interfaces.length === 0) return null;
            const allColumns = new Set();
            interfaces.forEach((row) => Object.keys(row).forEach((k) => allColumns.add(k)));
            const columns = Array.from(allColumns);
            return (
              <CollapsibleSection
                key={sectionTitle}
                title={sectionTitle}
                isExpanded={expandedSections.has(sectionTitle)}
                onToggle={() => toggleSection(sectionTitle)}
                isActive={activeSection === sectionTitle}
                onActivate={() => activateSection(sectionTitle)}
              >
                <div className="table-container">
                  <table className="section-table">
                    <thead>
                      <tr>{columns.map((column, idx) => (<th key={idx}>{column}</th>))}</tr>
                    </thead>
                    <tbody>
                      {interfaces.map((interfaceRow, rowIdx) => (
                        <tr key={rowIdx}>
                          {columns.map((column, colIdx) => (
                            <td key={colIdx}>{interfaceRow[column] != null ? String(interfaceRow[column]) : 'N/A'}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CollapsibleSection>
            );
          })}
      </div>
    </div>
  );
};

export default PortDetailView;
