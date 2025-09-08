import { useState, useMemo, useCallback, useEffect, useRef } from 'react';
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
  extractPortStatus,
  extractCpuUptime,
  extractFpgaVersions,
} from '../utils/extractors';

const SystemSummary = ({ sections, systemMap, slotIndex }) => {

  const qsfpData = useMemo(() => extractQsfpData(sections), [sections]);
  const fanData = useMemo(() => extractFanData(sections), [sections]);
  const psuData = useMemo(() => extractPsuData(sections), [sections]);
  const psuDebugData = useMemo(() => extractPsuDebugData(sections), [sections]);
  const phyData = useMemo(() => extractPhyData(sections), [sections]);
  const interfaceData = useMemo(() => extractInterfaceData(sections), [sections]);
  const portTypes = useMemo(() => extractPortTypes(sections), [sections]);
  const portStatus = useMemo(() => extractPortStatus(sections), [sections]);
  const cpuUptime = useMemo(() => extractCpuUptime(sections), [sections]);
  const fpgaVersions = useMemo(() => extractFpgaVersions(sections), [sections]);

  const [selectedPort, setSelectedPort] = useState(null);
  const [selectedPortData, setSelectedPortData] = useState(null);
  const [selectedPhyData, setSelectedPhyData] = useState(null);
  const [selectedInterfaceData, setSelectedInterfaceData] = useState(null);
  const [selectedPortType, setSelectedPortType] = useState(null);
  const [selectedFan, setSelectedFan] = useState(null);
  const [selectedFanData, setSelectedFanData] = useState(null);
  const [selectedPsu, setSelectedPsu] = useState(null);
  const [selectedPsuData, setSelectedPsuData] = useState(null);
  const [heatmapMode, setHeatmapMode] = useState('temp'); // 'temp' | 'voltage'
  const [heatmapSettings, setHeatmapSettings] = useState({
    tempLow: 50,
    tempHigh: 75,
    voltageLow: 3.0,
    voltageHigh: 3.6,
    useDefault: false
  });

  const calculateDataRange = (mode) => {
    const values = Object.values(qsfpData).map(portData => {
      let val;
      if (mode === 'temp') {
        val = portData?.['Global DOM Monitors']?.['Temperature (C)']
              ?? portData?.Temperature;
      } else {
        val = portData?.['Global DOM Monitors']?.['Voltage (V)']
              ?? portData?.['Supply Voltage']
              ?? portData?.Voltage;
      }
      if (val == null) return null;
      const num = typeof val === 'number' ? val : parseFloat(String(val).replace(/ [CV]|°C/g, ''));
      return !Number.isNaN(num) ? num : null;
    }).filter(Boolean);


    return values.length ? { min: Math.min(...values), max: Math.max(...values) }
                         : { min: mode === 'temp' ? 50 : 3.0, max: mode === 'temp' ? 75 : 3.6 };
  };

  const handlePercentilesToggle = (checked) => {
    if (checked) {
      // When enabling percentiles, don't change the input values - just switch mode
      setHeatmapSettings(prev => ({ ...prev, useDefault: true }));
    } else {
      // When disabling percentiles, populate with actual data ranges
      const tempRange = calculateDataRange('temp');
      const voltageRange = calculateDataRange('voltage');
      setHeatmapSettings(prev => ({
        ...prev,
        useDefault: false,
        tempLow: tempRange.min,
        tempHigh: tempRange.max,
        voltageLow: voltageRange.min,
        voltageHigh: voltageRange.max
      }));
    }
  };

  // Ref to store the saved scroll position
  const savedScrollPosition = useRef(0);

  const handlePortClick = useCallback((portNum, portData, portType) => {
    // Save current scroll position before navigating - target specific window
    const currentContent = document.querySelector(`.content:nth-child(${slotIndex + 1})`);
    const container = currentContent?.querySelector('.system-summary-container');
    if (container) {
      savedScrollPosition.current = container.scrollTop;
    }

    setSelectedPort(portNum);
    setSelectedPortData(portData);
    setSelectedPhyData(phyData[portNum] || []);
    setSelectedInterfaceData(interfaceData[portNum] || {});
    setSelectedPortType(portType);
  }, [phyData, interfaceData, slotIndex]);

  const handleFanClick = useCallback((fanNum, data) => {
    // Save current scroll position before navigating - target specific window
    const currentContent = document.querySelector(`.content:nth-child(${slotIndex + 1})`);
    const container = currentContent?.querySelector('.system-summary-container');
    if (container) {
      savedScrollPosition.current = container.scrollTop;
    }

    setSelectedFan(fanNum);
    setSelectedFanData(data);
  }, [slotIndex]);

  const handlePsuClick = useCallback((psuNum, data) => {
    // Save current scroll position before navigating - target specific window
    const currentContent = document.querySelector(`.content:nth-child(${slotIndex + 1})`);
    const container = currentContent?.querySelector('.system-summary-container');
    if (container) {
      savedScrollPosition.current = container.scrollTop;
    }

    setSelectedPsu(psuNum);
    setSelectedPsuData(data);
  }, [slotIndex]);

  const handleBackToSummary = useCallback(() => {
    setSelectedPort(null);
    setSelectedPortData(null);
    setSelectedPhyData(null);
    setSelectedInterfaceData(null);
    setSelectedFan(null);
    setSelectedFanData(null);
    setSelectedPsu(null);
    setSelectedPsuData(null);

    // Restore scroll position after state update - target specific window
    setTimeout(() => {
      const currentContent = document.querySelector(`.content:nth-child(${slotIndex + 1})`);
      const container = currentContent?.querySelector('.system-summary-container');
      if (container) {
        container.scrollTop = savedScrollPosition.current;
      }
    }, 0);
  }, [slotIndex]);

  // Scroll to top when detail views are opened (but not when going back to main view)
  useEffect(() => {
    if (selectedPort || selectedFan || selectedPsu) {
      // Scroll detail view to top - target specific window
      const currentContent = document.querySelector(`.content:nth-child(${slotIndex + 1})`);
      const container = currentContent?.querySelector('.system-summary-container');
      if (container) {
        container.scrollTop = 0;
      }
    }
  }, [selectedPort, selectedFan, selectedPsu, slotIndex]);

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
          <div className="system-header">
            <h4>Front View</h4>
            <div className="heatmap-controls">
              <div className="heatmap-settings">
                {!heatmapSettings.useDefault && ['Low', 'High'].map(type => (
                  <div key={type} className="setting-row">
                    <label>{type}:</label>
                    <input
                      type="number"
                      value={heatmapSettings[heatmapMode === 'temp' ? `temp${type}` : `voltage${type}`]}
                      onChange={(e) => setHeatmapSettings(prev => ({
                        ...prev,
                        [heatmapMode === 'temp' ? `temp${type}` : `voltage${type}`]: parseFloat(e.target.value) || 0
                      }))}
                      min="0"
                      max={heatmapMode === 'temp' ? 100 : 5}
                      step={heatmapMode === 'temp' ? 1 : 0.1}
                    />
                  </div>
                ))}
                <div className="setting-row">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={heatmapSettings.useDefault}
                      onChange={(e) => handlePercentilesToggle(e.target.checked)}
                    />
                    Percentiles
                  </label>
                </div>
              </div>
              <div className="heatmap-button-group">
                <button className={`heatmap-button ${heatmapMode === 'temp' ? 'active' : ''}`} onClick={() => setHeatmapMode('temp')} title="Temperature heatmap">°C</button>
                <button className={`heatmap-button ${heatmapMode === 'voltage' ? 'active' : ''}`} onClick={() => setHeatmapMode('voltage')} title="Voltage heatmap">V</button>
              </div>
            </div>
          </div>
          <div className="view-content">
            {frontHasPorts && (
              <div className="component-section ports-section">
                <PortGrid portConfig={systemMap.ports} qsfpData={qsfpData} portTypes={portTypes} portStatus={portStatus} onPortClick={handlePortClick} heatmapMode={heatmapMode} heatmapSettings={heatmapSettings} />
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

      {/* System Data View */}
      <div className="system-view system-data-view">
        <h4>System Data</h4>
        <div className="view-content">
          <div className="component-section system-data-entry">
            <div className="system-data-grid">
              <div className="system-data-slot">
                <div className="system-data-content">
                  <div className="system-data-header">
                    <div className="system-data-label">CPU UPTIME</div>
                  </div>
                  <div className="system-data-row">
                    {cpuUptime ? (
                      <div className="system-data-field">{cpuUptime}</div>
                    ) : (
                      <div className="system-data-field">No data</div>
                    )}
                  </div>
                </div>
              </div>

              <div className="system-data-slot">
                <div className="system-data-content">
                  <div className="system-data-header">
                    <div className="system-data-label">FPGA VERSIONS</div>
                  </div>
                  <div className="system-data-row">
                    {fpgaVersions ? (
                      Object.entries(fpgaVersions).map(([key, value]) => (
                        <div key={key} className="system-data-field">
                          {key}: {value}
                        </div>
                      ))
                    ) : (
                      <div className="system-data-field">No data</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSummary;
