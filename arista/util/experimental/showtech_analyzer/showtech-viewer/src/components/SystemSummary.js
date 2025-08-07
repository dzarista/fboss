import React, { useState } from 'react';
import { CollapsibleSection } from './SectionRenderer';

// Helper function to extract platform config (same logic as anomaly detection)
const getPlatformConfig = (sections) => {
  // Look for product name in fboss2 show product section
  const productSection = sections.find(s => s.title === 'fboss2 show product');
  if (productSection && productSection.parsed_data?.type === 'key_value') {
    const productName = productSection.parsed_data.data?.Product;
    if (productName) {
      return getPlatformConfigByProduct(productName);
    }
  }
  
  // Fallback to SMB SERIAL NUMBER
  const smbSection = sections.find(s => s.title === 'SMB SERIAL NUMBER');
  if (smbSection && smbSection.parsed_data?.type === 'key_value') {
    const productName = smbSection.parsed_data.data?.['Product Name'];
    if (productName) {
      return getPlatformConfigByProduct(productName);
    }
  }
  
  return null;
};

// Utility function to infer port type from port number
const inferPortType = (portNum, platform = 'Viper') => {
  // Platform-specific port type inference
  if (platform === 'Viper') {
    // Based on Viper platform: ports 1-10 and 29-39 are fab, ports 11-28 are eth
    if ((portNum >= 1 && portNum <= 10) || (portNum >= 29 && portNum <= 39)) {
      return 'fab';
    } else if (portNum >= 11 && portNum <= 28) {
      return 'eth';
    }
  }
  // Add other platform logic here as needed
  // If port type is unknown, assume it's disabled
  return 'disabled';
};

// Platform config mapping (same as backend config.json)
const getPlatformConfigByProduct = (productName) => {
  const platformConfigs = {
    'MERU800BIA': {
      platform: 'Viper',
      product_name: 'MERU800BIA',
      description: 'Viper platform configuration',
      system_map: {
        front: ['ports'],
        rear: ['psu', 'fans'],
        ports: {
          num_ports: 39,
          grid_rows: 4,
          grid_columns: 12,
          port_map: [
            [1, 5, 0, 11, 15, 0, 21, 25, 0, 31, 35, 0],
            [2, 6, 0, 12, 16, 0, 22, 26, 0, 32, 36, 0],
            [3, 7, 9, 13, 17, 19, 23, 27, 29, 33, 37, 39],
            [4, 8, 10, 14, 18, 20, 24, 28, 30, 34, 38, 0]
          ]
        },
        fans: 4,
        psu: 2
      }
    },
    'MERU800BIAB': {
      platform: 'Viper',
      product_name: 'MERU800BIAB',
      description: 'Viper platform configuration',
      system_map: {
        front: ['ports'],
        rear: ['psu', 'fans'],
        ports: {
          num_ports: 39,
          grid_rows: 4,
          grid_columns: 12,
          port_map: [
            [1, 5, 0, 11, 15, 0, 21, 25, 0, 31, 35, 0],
            [2, 6, 0, 12, 16, 0, 22, 26, 0, 32, 36, 0],
            [3, 7, 9, 13, 17, 19, 23, 27, 29, 33, 37, 39],
            [4, 8, 10, 14, 18, 20, 24, 28, 30, 34, 38, 0]
          ]
        },
        fans: 4,
        psu: 2
      }
    },
    'MERU800BFA': {
      platform: 'Whistler',
      product_name: 'MERU800BFA',
      description: 'Whistler platform configuration',
      system_map: {
        front: ['ports'],
        rear: ['psu', 'fans'],
        // Add Whistler specific config when needed
      }
    },
    'GLATH05a-64o': {
      platform: 'QuicksilverPFb',
      product_name: 'GLATH05a-64o',
      description: 'Quicksilver platform configuration',
      system_map: {
        front: ['ports'],
        rear: ['psu', 'fans'],
        // Add Quicksilver specific config when needed
      }
    }
  };
  
  return platformConfigs[productName] || null;
};

// Extract QSFP util data from sections
const extractQsfpData = (sections) => {
  const qsfpData = {};

  sections.forEach(section => {
    if (section.section_type === 'qsfp_util' && section.parsed_data?.ports) {
      section.parsed_data.ports.forEach(portData => {
        if (portData.port) {
          qsfpData[portData.port] = portData;
        }
      });
    }
  });

  return qsfpData;
};

// Port Grid Component
const PortGrid = ({ portConfig, qsfpData, onPortClick, platform }) => {
  if (!portConfig) return <div className="config-missing">No port configuration available</div>;

  const { grid_rows, grid_columns, port_map } = portConfig;

  // Use the explicit port_map if available, otherwise fall back to the old method
  let grid;
  if (port_map && Array.isArray(port_map)) {
    grid = port_map;
  } else {
    // Fallback to old method for backward compatibility
    const { major_order, empty_grid_slots = [] } = portConfig;
    const emptySlots = new Set(empty_grid_slots.map(slot => `${slot[0]}-${slot[1]}`));

    grid = Array(grid_rows).fill(null).map(() => Array(grid_columns).fill(null));

    let portIndex = 1;
    if (major_order === 'column') {
      for (let col = 0; col < grid_columns; col++) {
        for (let row = 0; row < grid_rows; row++) {
          if (!emptySlots.has(`${row}-${col}`)) {
            grid[row][col] = portIndex++;
          }
        }
      }
    } else { // row major
      for (let row = 0; row < grid_rows; row++) {
        for (let col = 0; col < grid_columns; col++) {
          if (!emptySlots.has(`${row}-${col}`)) {
            grid[row][col] = portIndex++;
          }
        }
      }
    }
  }

  return (
    <div className="port-grid" style={{
      display: 'grid',
      gridTemplateRows: `repeat(${grid_rows}, 1fr)`,
      gridTemplateColumns: `repeat(${grid_columns}, 1fr)`,
      gap: '4px',
      minHeight: '200px'
    }}>
      {grid.flat().map((portNum, idx) => {
        if (portNum === null || portNum === 0) {
          return <div key={idx} className="port-slot empty"></div>;
        }

        const portData = qsfpData[portNum];
        // Try multiple possible temperature locations
        const temperature = portData?.['Global DOM Monitors']?.['Temperature (C)'] ||
                           portData?.Temperature ||
                           (portData?.Temperature && parseFloat(portData.Temperature.replace(' C', '')));
        const hasQsfpData = !!portData;
        const portType = inferPortType(portNum, platform);

        return (
          <div
            key={idx}
            className={`port-slot ${hasQsfpData ? 'has-qsfp-data' : 'inactive-port'} port-type-${portType}`}
            title={hasQsfpData ? `Port ${portNum} (${portType})\nTemp: ${temperature || 'N/A'}°C\nClick for details` : `Port ${portNum} (${portType}) - Inactive`}
            onClick={hasQsfpData ? () => onPortClick(portNum, portData, portType) : undefined}
            style={{ cursor: hasQsfpData ? 'pointer' : 'default' }}
          >
            <span className="port-number">{portNum}</span>
            {temperature && (
              <span className="port-temperature">
                {typeof temperature === 'number' ? `${temperature.toFixed(1)}°C` :
                 typeof temperature === 'string' ? (temperature.includes('C') ? temperature : `${temperature}°C`) :
                 `${temperature}°C`}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};

// PSU Grid Component
const PSUGrid = ({ psuConfig, psuData = {}, onPsuClick }) => {
  if (typeof psuConfig !== 'number') return <div className="config-missing">No PSU configuration available</div>;

  const num_psu = psuConfig;
  const grid_rows = num_psu;
  const grid_columns = 1;
  const psu_index = Array.from({ length: num_psu }, (_, i) => i + 1);

  return (
    <div className="psu-grid" style={{
      display: 'grid',
      gridTemplateRows: `repeat(${grid_rows}, 1fr)`,
      gridTemplateColumns: `repeat(${grid_columns}, 1fr)`,
      gap: '8px',
      minHeight: '100px'
    }}>
      {psu_index.map((psuNum, idx) => {
        const psuInfo = psuData[`PSU${psuNum}`];

        const status = psuInfo?.status || 'Unknown';
        const voltageIn = psuInfo?.voltage_in || 'N/A';
        const voltageOut = psuInfo?.voltage_out || 'N/A';
        const powerOut = psuInfo?.power_out || 'N/A';

        // Get fan speeds
        const fanSpeeds = psuInfo?.fans || {};
        const fanSpeedText = Object.keys(fanSpeeds).length > 0
          ? Object.values(fanSpeeds).join(', ')
          : 'N/A';

        return (
          <div
            key={idx}
            className={`psu-slot psu-${status.toLowerCase()}`}
            title={`PSU ${psuNum}: ${status}\nVin: ${voltageIn}, Vout: ${voltageOut}\nPower: ${powerOut}\nFans: ${fanSpeedText}\nClick for details`}
            onClick={() => onPsuClick && onPsuClick(psuNum, psuInfo)}
            style={{ cursor: onPsuClick ? 'pointer' : 'default' }}
          >
            <div className="psu-icon">
              <svg width="16" height="16" viewBox="0 0 120 120" fill="black">
                <path d="M80 10 L30 70 H55 L45 110 L95 50 H65 L80 10 Z"/>
              </svg>
            </div>
            <div className="psu-content">
              <div className="psu-header">
                <div className="psu-label">PSU{psuNum}</div>
              </div>
              <div className="psu-data-row">
                <div className="psu-voltage">In: {voltageIn}</div>
                <div className="psu-voltage">Out: {voltageOut}</div>
                <div className="psu-power">Power: {powerOut}</div>
                {Object.keys(fanSpeeds).length > 0 && (
                  Object.entries(fanSpeeds).map(([fanName, speed], fanIdx) => (
                    <div key={fanIdx} className="psu-fan-speed">
                      {fanName.replace('_RPM', '')}: {speed}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Fan Grid Component
const FanGrid = ({ fanConfig, fanData = [], onFanClick }) => {
  if (typeof fanConfig !== 'number') return <div className="config-missing">No fan configuration available</div>;

  const num_fans = fanConfig;
  const grid_rows = 1;
  const grid_columns = num_fans;

  return (
    <div className="fan-grid" style={{
      display: 'grid',
      gridTemplateRows: `repeat(${grid_rows}, 1fr)`,
      gridTemplateColumns: `repeat(${grid_columns}, 1fr)`,
      gap: '8px',
      minHeight: '80px'
    }}>
      {Array.from({ length: num_fans }, (_, idx) => {
        const fanNum = idx + 1;

        // Find fan data for this fan number
        const fanInfo = fanData.find(f => {
          const name = f.Name || '';
          const match = name.match(/(\d+)$/);
          return match && parseInt(match[1]) === fanNum;
        });

        const status = fanInfo?.Status || 'Unknown';
        const rpm = fanInfo?.RPM || 'N/A';
        const percentage = fanInfo?.Percentage || 'N/A';

        return (
          <div
            key={idx}
            className={`fan-slot fan-${status.toLowerCase()}`}
            title={`Fan ${fanNum}: ${status}, RPM: ${rpm}, Load: ${percentage}\nClick for details`}
            onClick={() => onFanClick && onFanClick(fanNum, fanInfo)}
            style={{ cursor: onFanClick ? 'pointer' : 'default' }}
          >
            <div className="fan-icon">
              <svg width="16" height="16" viewBox="0 0 122.88 122.07" fill="currentColor">
                <path fillRule="evenodd" d="M67.29,82.9c-.11,1.3-.26,2.6-.47,3.9-1.43,9-5.79,14.34-8.08,22.17C56,118.45,65.32,122.53,73.27,122A37.63,37.63,0,0,0,85,119a45,45,0,0,0,9.32-5.36c20.11-14.8,16-34.9-6.11-46.36a15,15,0,0,0-4.14-1.4,22,22,0,0,1-6,11.07l0,0A22.09,22.09,0,0,1,67.29,82.9ZM62.4,44.22a17.1,17.1,0,1,1-17.1,17.1,17.1,17.1,0,0,1,17.1-17.1ZM84.06,56.83c1.26.05,2.53.14,3.79.29,9.06,1,14.58,5.16,22.5,7.1,9.6,2.35,13.27-7.17,12.41-15.09a37.37,37.37,0,0,0-3.55-11.57,45.35,45.35,0,0,0-5.76-9.08C97.77,9,77.88,14,67.4,36.63a14.14,14.14,0,0,0-1,2.94A22,22,0,0,1,78,45.68l0,0a22.07,22.07,0,0,1,6,11.13Zm-26.9-17c0-1.6.13-3.21.31-4.81,1-9.07,5.12-14.6,7-22.52C66.86,2.89,57.32-.75,49.41.13A37.4,37.4,0,0,0,37.84,3.7a44.58,44.58,0,0,0-9.06,5.78C9.37,25.2,14.39,45.08,37,55.51a14.63,14.63,0,0,0,3.76,1.14A22.12,22.12,0,0,1,57.16,39.83ZM40.66,65.42a52.11,52.11,0,0,1-5.72-.24c-9.08-.88-14.67-4.92-22.62-6.73C2.68,56.25-.83,65.84.16,73.74A37.45,37.45,0,0,0,3.9,85.25a45.06,45.06,0,0,0,5.91,9c16,19.17,35.8,13.87,45.91-8.91a15.93,15.93,0,0,0,.88-2.66A22.15,22.15,0,0,1,40.66,65.42Z"/>
              </svg>
            </div>
            <div className="fan-content">
              <div className="fan-header">
                <div className="fan-label">Fan{fanNum}</div>
              </div>
              <div className="fan-data-row">
                <div className="fan-speed">Speed: {rpm} RPM</div>
                <div className="fan-percentage">PWM: {percentage}</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Helper function to extract fan data from sections
const extractFanData = (sections) => {
  // Try FANS section first (new format)
  const fansSection = sections.find(s => s.title === 'FANS');
  if (fansSection && fansSection.parsed_data?.type === 'fans') {
    return fansSection.parsed_data.rows || [];
  }

  // Fallback to fboss2 show environment fan (old format)
  const fanSection = sections.find(s => s.title === 'fboss2 show environment fan');
  if (fanSection && fanSection.parsed_data?.type === 'table') {
    return fanSection.parsed_data.rows || [];
  }

  return [];
};

// Helper function to extract PSU data from sensor sections
const extractPsuData = (sections) => {
  const sensorSection = sections.find(s => s.title === 'fboss2 show environment sensor');
  if (!sensorSection || sensorSection.parsed_data?.type !== 'table') {
    return {};
  }

  const rows = sensorSection.parsed_data.rows || [];
  const psuData = {};

  rows.forEach(row => {
    const sensor = row.Sensor || '';
    const value = row.Value || '';
    const health = row.SensorHealth || '';

    // Extract PSU number and metric type
    const psuMatch = sensor.match(/^PSU(\d+)_(.+)$/);
    if (psuMatch) {
      const psuNum = psuMatch[1];
      const metric = psuMatch[2];

      if (!psuData[`PSU${psuNum}`]) {
        psuData[`PSU${psuNum}`] = {
          name: `PSU${psuNum}`,
          status: 'Good',
          fans: {},
          voltage_in: null,
          voltage_out: null,
          power_in: null,
          power_out: null,
          temperatures: {}
        };
      }

      const psu = psuData[`PSU${psuNum}`];

      // Update overall status if any sensor is not Good
      if (health !== 'Good') {
        psu.status = health;
      }

      // Parse different metrics
      if (metric.includes('FAN') && metric.includes('RPM')) {
        psu.fans[metric] = `${value} RPM`;
      } else if (metric === 'VIN') {
        psu.voltage_in = `${value}V`;
      } else if (metric === 'VOUT') {
        psu.voltage_out = `${value}V`;
      } else if (metric === 'PIN') {
        psu.power_in = `${value}W`;
      } else if (metric === 'POUT') {
        psu.power_out = `${value}W`;
      } else if (metric.includes('TEMP')) {
        psu.temperatures[metric] = `${value}°C`;
      }
    }
  });

  return psuData;
};

// Helper function to extract PSU debug info from sections
const extractPsuDebugData = (sections) => {
  const psuDebugSection = sections.find(s => s.title === 'PSU debug info');
  if (!psuDebugSection || psuDebugSection.parsed_data?.type !== 'psu_debug') {
    return {};
  }

  const psuSlots = psuDebugSection.parsed_data.psu_slots || [];
  const psuDebugData = {};

  psuSlots.forEach(psuSlot => {
    const psuNum = psuSlot.slot;
    psuDebugData[`PSU${psuNum}`] = {
      slot: psuNum,
      properties: psuSlot.properties || {}
    };
  });

  return psuDebugData;
};

// Fan Detail View Component
const FanDetailView = ({ fanNum, fanData, onBack }) => {
  // Start with all sections expanded
  const [expandedSections, setExpandedSections] = useState(new Set([
    'fan-placeholder'
  ]));
  const [activeSection, setActiveSection] = useState(null);

  const toggleSection = (sectionKey) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionKey)) {
      newExpanded.delete(sectionKey);
    } else {
      newExpanded.add(sectionKey);
    }
    setExpandedSections(newExpanded);
  };

  const activateSection = (sectionKey) => {
    setActiveSection(sectionKey);
  };

  return (
    <div className="port-detail-view">
      {/* Header matching section-header styling */}
      <div className="section-header">
        <div className="section-header-left">
          <button className="back-button" onClick={onBack}>
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
          <h3 className="section-title">Fan {fanNum} Details</h3>
        </div>
      </div>

      <div className="sections-container">
        {/* Placeholder section - will be replaced with actual fan data */}
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

// PSU Detail View Component
const PSUDetailView = ({ psuNum, psuData, psuDebugData, onBack }) => {
  // Start with all sections expanded
  const [expandedSections, setExpandedSections] = useState(new Set([
    'psu-debug', 'psu-sensors', 'no-data'
  ]));
  const [activeSection, setActiveSection] = useState(null);

  const toggleSection = (sectionKey) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionKey)) {
      newExpanded.delete(sectionKey);
    } else {
      newExpanded.add(sectionKey);
    }
    setExpandedSections(newExpanded);
  };

  const activateSection = (sectionKey) => {
    setActiveSection(sectionKey);
  };

  // Get PSU debug info for this specific PSU
  const debugInfo = psuDebugData?.[`PSU${psuNum}`]?.properties || {};

  return (
    <div className="port-detail-view">
      {/* Header matching section-header styling */}
      <div className="section-header">
        <div className="section-header-left">
          <button className="back-button" onClick={onBack}>
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
          <h3 className="section-title">PSU {psuNum} Details</h3>
        </div>
      </div>

      <div className="sections-container">
        {/* PSU Debug Info Section */}
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
                  <tr>
                    <th>Property</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(debugInfo).map(([key, value]) => (
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

        {/* PSU Sensor Data Section */}
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
                  <tr>
                    <th>Property</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><strong>Status</strong></td>
                    <td>{psuData.status}</td>
                  </tr>
                  {psuData.voltage_in && (
                    <tr>
                      <td><strong>Voltage In</strong></td>
                      <td>{psuData.voltage_in}</td>
                    </tr>
                  )}
                  {psuData.voltage_out && (
                    <tr>
                      <td><strong>Voltage Out</strong></td>
                      <td>{psuData.voltage_out}</td>
                    </tr>
                  )}
                  {psuData.power_in && (
                    <tr>
                      <td><strong>Power In</strong></td>
                      <td>{psuData.power_in}</td>
                    </tr>
                  )}
                  {psuData.power_out && (
                    <tr>
                      <td><strong>Power Out</strong></td>
                      <td>{psuData.power_out}</td>
                    </tr>
                  )}
                  {Object.entries(psuData.fans || {}).map(([fanKey, fanValue]) => (
                    <tr key={fanKey}>
                      <td><strong>{fanKey}</strong></td>
                      <td>{fanValue}</td>
                    </tr>
                  ))}
                  {Object.entries(psuData.temperatures || {}).map(([tempKey, tempValue]) => (
                    <tr key={tempKey}>
                      <td><strong>{tempKey}</strong></td>
                      <td>{tempValue}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CollapsibleSection>
        )}

        {/* No Data Message */}
        {Object.keys(debugInfo).length === 0 && !psuData && (
          <CollapsibleSection
            title="No Data Available"
            isExpanded={expandedSections.has('no-data')}
            onToggle={() => toggleSection('no-data')}
            isActive={activeSection === 'no-data'}
            onActivate={() => activateSection('no-data')}
          >
            <div className="table-container">
              <p>No PSU debug information or sensor data available for PSU {psuNum}.</p>
            </div>
          </CollapsibleSection>
        )}
      </div>
    </div>
  );
};



// Port Detail View Component
const PortDetailView = ({ portNum, portData, phyData, interfaceData, portType, onBack }) => {
  // Start with all sections expanded
  const [expandedSections, setExpandedSections] = useState(() => {
    const allSections = new Set(['qsfp-basic']);

    // Add all QSFP lane data sections
    Object.entries(portData).forEach(([sectionName, sectionData]) => {
      if (typeof sectionData === 'object' && sectionData &&
          Object.values(sectionData).some(val => Array.isArray(val))) {
        allSections.add(`qsfp-${sectionName}`);
      }
    });

    // Add all PHY sections
    if (phyData && phyData.length > 0) {
      phyData.forEach(singlePhyData => {
        allSections.add(`phy-${singlePhyData.interface}`);
        if (singlePhyData.sections) {
          Object.keys(singlePhyData.sections).forEach(sectionName => {
            allSections.add(`phy-${singlePhyData.interface}-${sectionName}-props`);
            allSections.add(`phy-${singlePhyData.interface}-${sectionName}-stats`);
            allSections.add(`phy-${singlePhyData.interface}-${sectionName}`);
          });
        }
      });
    }

    // Add all interface sections
    if (interfaceData && Object.keys(interfaceData).length > 0) {
      Object.keys(interfaceData).forEach(sectionTitle => {
        allSections.add(sectionTitle);
      });
    }

    return allSections;
  });
  const [activeSection, setActiveSection] = useState(null);

  const toggleSection = (sectionKey) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionKey)) {
      newExpanded.delete(sectionKey);
    } else {
      newExpanded.add(sectionKey);
    }
    setExpandedSections(newExpanded);
  };

  const activateSection = (sectionKey) => {
    setActiveSection(sectionKey);
  };

  return (
    <div className="port-detail-view">
      {/* Header matching section-header styling */}
      <div className="section-header">
        <div className="section-header-left">
          <button className="back-button" onClick={onBack}>
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
          <h3 className="section-title">Port {portNum} Details</h3>
          <span className="port-type-badge">
            {portType === 'eth' ? 'Ethernet' : portType === 'fab' ? 'Fabric' : 'Disabled'}
          </span>
        </div>
      </div>

      <div className="sections-container">
        {/* wedge_qsfp_util - Basic Properties */}
        <CollapsibleSection
          title={`wedge_qsfp_util - Port ${portNum}`}
          isExpanded={expandedSections.has('qsfp-basic')}
          onToggle={() => toggleSection('qsfp-basic')}
          isActive={activeSection === 'qsfp-basic'}
          onActivate={() => activateSection('qsfp-basic')}
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
        </CollapsibleSection>

        {/* wedge_qsfp_util - Lane Data Sections */}
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
            </CollapsibleSection>
          );
        })}



        {/* PHY Information - Individual Sections */}
        {phyData && phyData.length > 0 && phyData.map((singlePhyData, phyIdx) => (
          <React.Fragment key={phyIdx}>
            {/* Basic PHY Properties */}
            <CollapsibleSection
              title={`fboss2 show interface phy - Interface ${singlePhyData.interface}`}
              isExpanded={expandedSections.has(`phy-${singlePhyData.interface}`)}
              onToggle={() => toggleSection(`phy-${singlePhyData.interface}`)}
              isActive={activeSection === `phy-${singlePhyData.interface}`}
              onActivate={() => activateSection(`phy-${singlePhyData.interface}`)}
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
                    {Object.entries(singlePhyData).map(([key, value]) => {
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
            </CollapsibleSection>

            {/* PHY Subsections as individual CollapsibleSections */}
            {singlePhyData.sections && Object.entries(singlePhyData.sections).map(([sectionName, sectionData]) => {
              if (sectionName === 'RS FEC') {
                // RS FEC section with key-value pairs and codeword stats table
                return (
                  <React.Fragment key={sectionName}>
                    {/* FEC Properties */}
                    <CollapsibleSection
                      title={`${sectionName} - Properties - Interface ${singlePhyData.interface}`}
                      isExpanded={expandedSections.has(`phy-${singlePhyData.interface}-${sectionName}-props`)}
                      onToggle={() => toggleSection(`phy-${singlePhyData.interface}-${sectionName}-props`)}
                      isActive={activeSection === `phy-${singlePhyData.interface}-${sectionName}-props`}
                      onActivate={() => activateSection(`phy-${singlePhyData.interface}-${sectionName}-props`)}
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

                    {/* Codeword stats table */}
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
                        </div>
                      </CollapsibleSection>
                    )}
                  </React.Fragment>
                );
              } else if (Array.isArray(sectionData)) {
                // RX PMD or TX PMD sections with lane data
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
                  </CollapsibleSection>
                );
              }
              return null;
            })}
          </React.Fragment>
        ))}



        {/* Interface Information - Individual Sections */}
        {interfaceData && Object.keys(interfaceData).length > 0 &&
          Object.entries(interfaceData).map(([sectionTitle, interfaces]) => {
            if (interfaces.length === 0) return null;

            // Get all unique column names from all interfaces
            const allColumns = new Set();
            interfaces.forEach(interfaceRow => {
              Object.keys(interfaceRow).forEach(key => allColumns.add(key));
            });
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
                      <tr>
                        {columns.map((column, idx) => (
                          <th key={idx}>{column}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {interfaces.map((interfaceRow, rowIdx) => (
                        <tr key={rowIdx}>
                          {columns.map((column, colIdx) => (
                            <td key={colIdx}>
                              {interfaceRow[column] !== null && interfaceRow[column] !== undefined
                                ? String(interfaceRow[column])
                                : 'N/A'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CollapsibleSection>
            );
          })
        }
      </div>
    </div>
  );
};



// Extract PHY data from sections
const extractPhyData = (sections) => {
  const phySection = sections.find(section =>
    section.title === 'fboss2 show interface phy' && section.parsed_data?.type === 'fboss2_interface_phy'
  );

  if (!phySection || !phySection.parsed_data?.interfaces) {
    return {};
  }

  const phyData = {};
  phySection.parsed_data.interfaces.forEach(interfaceData => {
    // Extract port number from interface name (e.g., "eth1/11/1" -> "11", "eth1/11/5" -> "11")
    const match = interfaceData.interface.match(/eth\d+\/(\d+)\/\d+/);
    if (match) {
      const portNum = parseInt(match[1]);
      // Store multiple PHY interfaces per port in an array
      if (!phyData[portNum]) {
        phyData[portNum] = [];
      }
      phyData[portNum].push(interfaceData);
    }
  });

  return phyData;
};

// Extract interface data from various interface sections
const extractInterfaceData = (sections) => {
  const interfaceData = {};

  // Define the sections we want to extract data from
  const interfaceSections = [
    'fboss2 show lldp',
    'fboss2 show interface counters',
    'fboss2 show interface errors',
    'fboss2 show interface flaps',
    'fboss2 show transceiver'
  ];

  interfaceSections.forEach(sectionTitle => {
    const section = sections.find(s => s.title === sectionTitle);
    if (section && section.parsed_data?.type === 'table' && section.parsed_data?.rows) {
      const rows = section.parsed_data.rows;

      rows.forEach((row, rowIdx) => {
        // Look for interface name in common column names - try all possible column names
        let interfaceName = null;
        const possibleColumns = [
          'Interface Name',  // Used by counters, errors, flaps
          'Interface',       // Used by transceiver
          'Local Int',       // Used by lldp
          'Name',
          'Port',
          'LocalInterface',
          'LocalPort',
          'Local Interface',
          'Local Port'
        ];

        for (const col of possibleColumns) {
          if (row[col]) {
            interfaceName = row[col];
            break;
          }
        }

        if (interfaceName) {
          // Extract port number from interface name (e.g., "eth1/11/1" -> "11", "fab1/5/1" -> "5")
          const ethMatch = interfaceName.match(/eth\d+\/(\d+)\/\d+/);
          const fabMatch = interfaceName.match(/fab\d+\/(\d+)\/\d+/);

          if (ethMatch || fabMatch) {
            const portNum = parseInt(ethMatch ? ethMatch[1] : fabMatch[1]);

            if (!interfaceData[portNum]) {
              interfaceData[portNum] = {};
            }

            if (!interfaceData[portNum][sectionTitle]) {
              interfaceData[portNum][sectionTitle] = [];
            }

            // Store the entire row with the interface name for context
            interfaceData[portNum][sectionTitle].push({
              interface: interfaceName,
              ...row
            });
          }
        }
      });
    }
  });

  return interfaceData;
};

// Main System Summary Component
const SystemSummary = ({ sections }) => {
  const [selectedPort, setSelectedPort] = useState(null);
  const [selectedPortData, setSelectedPortData] = useState(null);
  const [selectedPhyData, setSelectedPhyData] = useState(null);
  const [selectedInterfaceData, setSelectedInterfaceData] = useState(null);
  const [selectedPortType, setSelectedPortType] = useState(null);
  const [selectedFan, setSelectedFan] = useState(null);
  const [selectedFanData, setSelectedFanData] = useState(null);
  const [selectedPsu, setSelectedPsu] = useState(null);
  const [selectedPsuData, setSelectedPsuData] = useState(null);

  const platformConfig = getPlatformConfig(sections);
  const fanData = extractFanData(sections);
  const psuData = extractPsuData(sections);
  const psuDebugData = extractPsuDebugData(sections);
  const qsfpData = extractQsfpData(sections);
  const phyData = extractPhyData(sections);
  const interfaceData = extractInterfaceData(sections);

  const handlePortClick = (portNum, portData, portType) => {
    setSelectedPort(portNum);
    setSelectedPortData(portData);
    setSelectedPhyData(phyData[portNum] || []);
    setSelectedInterfaceData(interfaceData[portNum] || {});
    setSelectedPortType(portType);
  };

  const handleFanClick = (fanNum, fanData) => {
    setSelectedFan(fanNum);
    setSelectedFanData(fanData);
  };

  const handlePsuClick = (psuNum, psuData) => {
    setSelectedPsu(psuNum);
    setSelectedPsuData(psuData);
  };

  const handleBackToSummary = () => {
    setSelectedPort(null);
    setSelectedPortData(null);
    setSelectedPhyData(null);
    setSelectedInterfaceData(null);
    setSelectedFan(null);
    setSelectedFanData(null);
    setSelectedPsu(null);
    setSelectedPsuData(null);
  };

  if (!platformConfig) {
    return (
      <div className="system-summary-container">
        <div className="system-summary-header">
          <h3>System Summary</h3>
          <p>Unable to detect platform configuration</p>
        </div>
        <div className="no-platform-message">
          <p>No platform configuration found. Please ensure the file contains product information.</p>
        </div>
      </div>
    );
  }

  // Show fan detail view if a fan is selected
  if (selectedFan) {
    return (
      <div className="system-summary-container">
        <FanDetailView
          fanNum={selectedFan}
          fanData={selectedFanData}
          onBack={handleBackToSummary}
        />
      </div>
    );
  }

  // Show PSU detail view if a PSU is selected
  if (selectedPsu) {
    return (
      <div className="system-summary-container">
        <PSUDetailView
          psuNum={selectedPsu}
          psuData={selectedPsuData}
          psuDebugData={psuDebugData}
          onBack={handleBackToSummary}
        />
      </div>
    );
  }

  // Show port detail view if a port is selected
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

  const systemMap = platformConfig.system_map || {};

  return (
    <div className="system-summary-container">
      <div className="system-summary-header">
        <h3>System Overview - {platformConfig.platform}</h3>
        <p>{platformConfig.description}</p>
      </div>

      {/* Front View */}
      {systemMap.front && (
        <div className="system-view front-view">
          <h4>Front View</h4>
          <div className="view-content">
            {systemMap.front.includes('ports') && (
              <div className="component-section ports-section">
                <PortGrid
                  portConfig={systemMap.ports}
                  qsfpData={qsfpData}
                  onPortClick={handlePortClick}
                  platform={platformConfig.platform}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Rear View */}
      {systemMap.rear && (
        <div className="system-view rear-view">
          <h4>Rear View</h4>
          <div className="view-content rear-flex">
            {systemMap.rear.includes('psu') && (
              <div className="component-section psu-section">
                <PSUGrid psuConfig={systemMap.psu} psuData={psuData} onPsuClick={handlePsuClick} />
              </div>
            )}
            {systemMap.rear.includes('fans') && (
              <div className="component-section fans-section">
                <FanGrid fanConfig={systemMap.fans} fanData={fanData} onFanClick={handleFanClick} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemSummary;