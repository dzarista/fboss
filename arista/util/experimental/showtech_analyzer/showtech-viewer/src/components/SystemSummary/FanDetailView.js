import React, { useState } from 'react';
import { CollapsibleSection } from '../SectionRenderer';

const FanDetailView = ({ fanNum, fanData, onBack }) => {
  const [expandedSections, setExpandedSections] = useState(new Set(['fan-placeholder']));
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
          <h3 className="section-title">Fan {fanNum} Details</h3>
        </div>
      </div>

      <div className="sections-container">
        <CollapsibleSection
          title={`Fan ${fanNum} Information`}
          isExpanded={expandedSections.has('fan-placeholder')}
          onToggle={() => toggleSection('fan-placeholder')}
          isActive={activeSection === 'fan-placeholder'}
          onActivate={() => activateSection('fan-placeholder')}
        >
          <div className="table-container">
            <p>Fan {fanNum} detail content will be implemented here.</p>
          </div>
        </CollapsibleSection>
      </div>
    </div>
  );
};

export default FanDetailView;
