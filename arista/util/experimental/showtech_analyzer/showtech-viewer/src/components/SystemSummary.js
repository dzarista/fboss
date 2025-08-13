import React, { useState, useMemo, useCallback } from 'react';
import PortGrid from './SystemSummary/PortGrid';
import PSUGrid from './SystemSummary/PSUGrid';
import FanGrid from './SystemSummary/FanGrid';
import PortDetailView from './SystemSummary/PortDetailView';
import PSUDetailView from './SystemSummary/PSUDetailView';
import FanDetailView from './SystemSummary/FanDetailView';
import {
  extractQsfpData,
  extractFanData,
  extractPsuData,
  extractPsuDebugData,
  extractPhyData,
  extractInterfaceData,
  extractPortTypes,
} from './SystemSummary/extractors';

const SystemSummary = ({ sections }) => {
  const systemMap = useMemo(() => {
    const systemMapSection = sections.find((s) => s.title === 'system_map');
    return systemMapSection?.parsed_data?.data || null;
  }, [sections]);

  const qsfpData = useMemo(() => extractQsfpData(sections), [sections]);
  const fanData = useMemo(() => extractFanData(sections), [sections]);
  const psuData = useMemo(() => extractPsuData(sections), [sections]);
  const psuDebugData = useMemo(() => extractPsuDebugData(sections), [sections]);
  const phyData = useMemo(() => extractPhyData(sections), [sections]);
  const interfaceData = useMemo(() => extractInterfaceData(sections), [sections]);
  const portTypes = useMemo(() => extractPortTypes(sections), [sections]);

  const [selectedPort, setSelectedPort] = useState(null);
  const [selectedPortData, setSelectedPortData] = useState(null);
  const [selectedPhyData, setSelectedPhyData] = useState(null);
  const [selectedInterfaceData, setSelectedInterfaceData] = useState(null);
  const [selectedPortType, setSelectedPortType] = useState(null);
  const [selectedFan, setSelectedFan] = useState(null);
  const [selectedFanData, setSelectedFanData] = useState(null);
  const [selectedPsu, setSelectedPsu] = useState(null);
  const [selectedPsuData, setSelectedPsuData] = useState(null);
  const [heatmapMode, setHeatmapMode] = useState('off'); // 'off' | 'temp' | 'voltage'

  const handlePortClick = useCallback((portNum, portData, portType) => {
    setSelectedPort(portNum);
    setSelectedPortData(portData);
    setSelectedPhyData(phyData[portNum] || []);
    setSelectedInterfaceData(interfaceData[portNum] || {});
    setSelectedPortType(portType);
  }, [phyData, interfaceData]);

  const handleFanClick = useCallback((fanNum, data) => {
    setSelectedFan(fanNum);
    setSelectedFanData(data);
  }, []);

  const handlePsuClick = useCallback((psuNum, data) => {
    setSelectedPsu(psuNum);
    setSelectedPsuData(data);
  }, []);

  const handleBackToSummary = useCallback(() => {
    setSelectedPort(null);
    setSelectedPortData(null);
    setSelectedPhyData(null);
    setSelectedInterfaceData(null);
    setSelectedFan(null);
    setSelectedFanData(null);
    setSelectedPsu(null);
    setSelectedPsuData(null);
  }, []);

  if (!systemMap) {
    return (
      <div className="system-summary-container">
        <div className="error-message">
          <h3>System Configuration Not Available</h3>
          <p>No system map found in the processed data.</p>
          <p>Please ensure the platform is supported and the file was processed correctly.</p>
        </div>
      </div>
    );
  }

  if (selectedFan) {
    return (
      <div className="system-summary-container">
        <FanDetailView fanNum={selectedFan} fanData={selectedFanData} sections={sections} onBack={handleBackToSummary} />
      </div>
    );
  }

  if (selectedPsu) {
    return (
      <div className="system-summary-container">
        <PSUDetailView psuNum={selectedPsu} psuData={selectedPsuData} psuDebugData={psuDebugData} sections={sections} onBack={handleBackToSummary} />
      </div>
    );
  }

  if (selectedPort && selectedPortData) {
    return (
      <div className="system-summary-container">
        <PortDetailView
          portNum={selectedPort}
          portData={selectedPortData}
          phyData={selectedPhyData}
          interfaceData={selectedInterfaceData}
          portType={selectedPortType}
          onBack={handleBackToSummary}
        />
      </div>
    );
  }

  const frontHasPorts = Array.isArray(systemMap.front)
    ? systemMap.front.includes('ports')
    : (typeof systemMap.front === 'string' ? systemMap.front.includes('ports') : !!systemMap.front);

  return (
    <div className="system-summary-container">
      <div className="system-summary-header">
        <h3>
          System Overview - {systemMap.platform_name || 'Unknown Platform'}
          {systemMap.product_name && ` (${systemMap.product_name})`}
        </h3>
        <p>{systemMap.description || 'Platform configuration loaded from processed data'}</p>
      </div>

      {systemMap.front && (
        <div className="system-view front-view">
          <div className="view-header">
            <h4>Front View</h4>
          </div>
          <div className="heatmap-button-group">
            <button className={`heatmap-button ${heatmapMode === 'off' ? 'active' : ''}`} onClick={() => setHeatmapMode('off')} title="Turn off heatmap">OFF</button>
            <button className={`heatmap-button ${heatmapMode === 'temp' ? 'active' : ''}`} onClick={() => setHeatmapMode('temp')} title="Temperature heatmap">°C</button>
            <button className={`heatmap-button ${heatmapMode === 'voltage' ? 'active' : ''}`} onClick={() => setHeatmapMode('voltage')} title="Voltage heatmap">V</button>
          </div>
          <div className="view-content">
            {frontHasPorts && (
              <div className="component-section ports-section">
                <PortGrid portConfig={systemMap.ports} qsfpData={qsfpData} portTypes={portTypes} onPortClick={handlePortClick} heatmapMode={heatmapMode} />
              </div>
            )}
          </div>
        </div>
      )}

      {systemMap.rear && (
        <div className="system-view rear-view">
          <h4>Rear View</h4>
          <div className="view-content rear-flex">
            {systemMap.rear.map((componentType, index) => {
              const getComponentWidth = (type) => {
                if (String(type).startsWith('psu')) return '20%';
                if (type === 'fans') return '60%';
                return 'auto';
              };
              const renderComponent = (type) => {
                if (String(type).startsWith('psu')) {
                  const psuConfig = { ...systemMap[type], section_type: type };
                  return <PSUGrid psuConfig={psuConfig} psuData={psuData} onPsuClick={handlePsuClick} />;
                }
                if (type === 'fans') return <FanGrid fanConfig={systemMap.fans} fanData={fanData} onFanClick={handleFanClick} />;
                return null;
              };
              return (
                <div key={index} className={`component-section ${componentType}-section`} style={{ width: getComponentWidth(componentType) }}>
                  {renderComponent(componentType)}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemSummary;
