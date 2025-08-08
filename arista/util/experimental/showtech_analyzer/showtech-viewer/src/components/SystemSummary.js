import React, { useState } from 'react';
import { CollapsibleSection } from './SectionRenderer';

// Helper function to extract platform config (same logic as anomaly detection)
const getPlatformConfig = (sections) => {
  // Look for product name in fboss2 show product section
  const productSection = sections.find(s => s.title === 'fboss2 show product');
  if (productSection && productSection.parsed_data?.type === 'key_value') {
    const productName = productSection.parsed_data.data?.Product;
    if (productName) {
      const config = getPlatformConfigByProduct(productName);
      if (config) return config;
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

// Utility function to calculate percentile
const calculatePercentile = (values, percentile) => {
  const sorted = [...values].sort((a, b) => a - b);
  const index = (percentile / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index % 1;

  if (upper >= sorted.length) return sorted[sorted.length - 1];
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
};

// Utility function to get temperature color based on percentiles
const getTemperatureColor = (temperature, temperaturePercentiles) => {
  if (!temperature || !temperaturePercentiles) return null;

  const temp = typeof temperature === 'number' ? temperature : parseFloat(temperature);
  if (isNaN(temp)) return null;

  const { p25, p50, p75, p90 } = temperaturePercentiles;

  if (temp >= p90) return '#dc2626'; // Darker red - hottest 10%
  if (temp >= p75) return '#ea580c'; // Darker orange - 75th-90th percentile
  if (temp >= p50) return '#d97706'; // Darker yellow - 50th-75th percentile
  if (temp >= p25) return '#65a30d'; // Darker light green - 25th-50th percentile
  return '#16a34a'; // Darker green - coolest 25%
};

// Utility function to get voltage color based on percentiles
const getVoltageColor = (voltage, voltagePercentiles) => {
  if (!voltage || !voltagePercentiles) return null;

  const volt = typeof voltage === 'number' ? voltage : parseFloat(voltage);
  if (isNaN(volt)) return null;

  const { p25, p50, p75, p90 } = voltagePercentiles;

  if (volt >= p90) return '#dc2626'; // Darker red - highest 10%
  if (volt >= p75) return '#ea580c'; // Darker orange - 75th-90th percentile
  if (volt >= p50) return '#d97706'; // Darker yellow - 50th-75th percentile
  if (volt >= p25) return '#65a30d'; // Darker light green - 25th-50th percentile
  return '#16a34a'; // Darker green - lowest 25%
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
        fans: {
          num_fans: 4,
          grid_rows: 1,
          grid_columns: 4,
          fan_slots: [[1, 2, 3, 4]]
        },
        psu: {
          num_psu: 2,
          grid_rows: 2,
          grid_columns: 1,
          psu_slots: [[1],
                      [2]]
        }
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
        fans: {
          num_fans: 4,
          grid_rows: 1,
          grid_columns: 4,
          fan_slots: [[1, 2, 3, 4]]
        },
        psu: {
          num_psu: 2,
          grid_rows: 2,
          grid_columns: 1,
          psu_slots: [[1],
                      [2]]
        }
      }
    },
    'MERU800BFA': {
      platform: 'Whistler',
      product_name: 'MERU800BFA',
      description: 'Whistler platform configuration',
      system_map: {
        front: ['ports'],
        rear: ['psu_left', 'fans', 'psu_right'],
        ports: {
          num_ports: 128,
          grid_rows: 8,
          grid_columns: 16,
          port_map: [
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            [17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32],
            [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48],
            [49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64],
            [65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80],
            [81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96],
            [97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112],
            [113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128]
          ]
        },
        fans: {
          num_fans: 12,
          grid_rows: 3,
          grid_columns: 4,
          fan_slots: [[1, 2, 3, 4],
                      [5, 6, 7, 8],
                      [9, 10, 11, 12]]
        },
        psu_left: {
          num_psu: 2,
          grid_rows: 2,
          grid_columns: 1,
          psu_slots: [[1],
                      [2]]
        },
        psu_right: {
          num_psu: 2,
          grid_rows: 2,
          grid_columns: 1,
          psu_slots: [[1],
                      [2]]
        }
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
  
  const result = platformConfigs[productName] || null;
  console.log('getPlatformConfigByProduct result for', productName, ':', !!result);
  return result;
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
const PortGrid = ({ portConfig, qsfpData, onPortClick, platform, heatmapMode = 'off' }) => {
  if (!portConfig) return <div className="config-missing">No port configuration available</div>;

  const { grid_rows, grid_columns, port_map } = portConfig;

  // Calculate temperature percentiles for color coding
  const temperatures = Object.values(qsfpData || {})
    .map(portData => {
      const temp = portData?.['Global DOM Monitors']?.['Temperature (C)'] ||
                   portData?.Temperature ||
                   (portData?.Temperature && parseFloat(portData.Temperature.replace(' C', '')));
      return typeof temp === 'number' ? temp :
             typeof temp === 'string' ? parseFloat(temp.replace(' C', '')) : null;
    })
    .filter(temp => temp !== null && !isNaN(temp));

  const temperaturePercentiles = temperatures.length > 0 ? {
    p25: calculatePercentile(temperatures, 25),
    p50: calculatePercentile(temperatures, 50),
    p75: calculatePercentile(temperatures, 75),
    p90: calculatePercentile(temperatures, 90)
  } : null;

  // Calculate voltage percentiles for color coding
  const voltages = Object.values(qsfpData || {})
    .map(portData => {
      const voltage = portData?.['Global DOM Monitors']?.['Voltage (V)'] ||
                     portData?.['Global DOM Monitors']?.['Voltage'] ||
                     portData?.Voltage ||
                     portData?.['Supply Voltage'] ||
                     (portData?.Voltage && parseFloat(portData.Voltage.replace(' V', '')));

      return typeof voltage === 'number' ? voltage :
             typeof voltage === 'string' ? parseFloat(voltage.replace(' V', '')) : null;
    })
    .filter(volt => volt !== null && !isNaN(volt));

  const voltagePercentiles = voltages.length > 0 ? {
    p25: calculatePercentile(voltages, 25),
    p50: calculatePercentile(voltages, 50),
    p75: calculatePercentile(voltages, 75),
    p90: calculatePercentile(voltages, 90)
  } : null;

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

        // Try multiple possible voltage locations
        const voltage = portData?.['Global DOM Monitors']?.['Voltage (V)'] ||
                       portData?.['Global DOM Monitors']?.['Voltage'] ||
                       portData?.Voltage ||
                       portData?.['Supply Voltage'] ||
                       (portData?.Voltage && parseFloat(portData.Voltage.replace(' V', '')));

        const hasQsfpData = !!portData;
        const portType = inferPortType(portNum, platform);

        // Get color based on heatmap mode
        let heatmapColor = null;
        let displayValue = null;

        if (hasQsfpData && heatmapMode === 'temp') {
          heatmapColor = getTemperatureColor(temperature, temperaturePercentiles);
          displayValue = temperature;
        } else if (hasQsfpData && heatmapMode === 'voltage') {
          heatmapColor = getVoltageColor(voltage, voltagePercentiles);
          displayValue = voltage;
        }

        // Create tooltip based on heatmap mode
        let tooltip = `Port ${portNum} (${portType})`;
        if (hasQsfpData) {
          if (heatmapMode === 'temp' && temperature) {
            const tempDisplay = typeof temperature === 'number' ? `${temperature.toFixed(1)}°C` :
                               (String(temperature).includes('°C') || String(temperature).includes('C') ? temperature : `${temperature}°C`);
            tooltip += `\nTemp: ${tempDisplay}`;
          } else if (heatmapMode === 'voltage' && voltage) {
            const voltDisplay = typeof voltage === 'number' ? `${voltage.toFixed(2)}V` :
                               (String(voltage).includes('V') ? voltage : `${voltage}V`);
            tooltip += `\nVoltage: ${voltDisplay}`;
          }
          tooltip += '\nClick for details';
        } else {
          tooltip += ' - Inactive';
        }

        return (
          <div
            key={idx}
            className={`port-slot ${hasQsfpData ? 'has-qsfp-data' : 'inactive-port'} port-type-${portType}`}
            title={tooltip}
            onClick={hasQsfpData ? () => onPortClick(portNum, portData, portType) : undefined}
            style={{
              cursor: hasQsfpData ? 'pointer' : 'default',
              backgroundColor: heatmapColor || undefined
            }}
          >
            <span className="port-number">{portNum}</span>
            {heatmapMode !== 'off' && displayValue && (
              <span className="port-value">
                {heatmapMode === 'temp'
                  ? (typeof displayValue === 'number' ? `${displayValue.toFixed(1)}°C` :
                     (String(displayValue).includes('°C') ? displayValue :
                      String(displayValue).includes('C') ? displayValue.replace('C', '°C') : `${displayValue}°C`))
                  : (typeof displayValue === 'number' ? `${displayValue.toFixed(2)}V` :
                     (String(displayValue).includes('V') ? displayValue : `${displayValue}V`))
                }
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
  if (!psuConfig || typeof psuConfig !== 'object') return <div className="config-missing">No PSU configuration available</div>;

  const { num_psu, grid_rows, grid_columns, psu_slots = [] } = psuConfig;

  return (
    <div
      className="psu-grid"
      style={{
        display: 'grid',
        gridTemplateRows: `repeat(${grid_rows}, 1fr)`,
        gridTemplateColumns: `repeat(${grid_columns}, 1fr)`,
        gap: '20px',
        height: '100%'
      }}
    >
      {psu_slots.length > 0 ? psu_slots.flat().map((slotNum, idx) => {
        // For psu_left and psu_right, we need to map slot numbers to actual PSU numbers
        // psu_left uses PSU1, PSU2; psu_right uses PSU3, PSU4
        let actualPsuNum = slotNum;
        if (psuConfig.section_type === 'psu_right') {
          actualPsuNum = slotNum + 2; // psu_right slots 1,2 map to PSU3,PSU4
        }

        const psuInfo = psuData[`PSU${actualPsuNum}`];

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
            title={`PSU ${actualPsuNum}: ${status}\nVin: ${voltageIn}, Vout: ${voltageOut}\nPower: ${powerOut}\nFans: ${fanSpeedText}\nClick for details`}
            onClick={() => onPsuClick && onPsuClick(actualPsuNum, psuInfo)}
            style={{ cursor: onPsuClick ? 'pointer' : 'default' }}
          >
            <div className="psu-icon">
              <svg width="16" height="16" viewBox="0 0 120 120" fill="black">
                <path d="M80 10 L30 70 H55 L45 110 L95 50 H65 L80 10 Z"/>
              </svg>
            </div>
            <div className="psu-content">
              <div className="psu-header">
                <div className="psu-label">PSU{actualPsuNum}</div>
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
      }) : <div className="config-missing">No PSU slots configured</div>}
    </div>
  );
};

// Fan Grid Component
const FanGrid = ({ fanConfig, fanData = [], onFanClick }) => {
  if (!fanConfig || typeof fanConfig !== 'object') return <div className="config-missing">No fan configuration available</div>;

  const { num_fans, grid_rows, grid_columns, fan_slots = [] } = fanConfig;

  return (
    <div
      className="fan-grid"
      style={{
        display: 'grid',
        gridTemplateRows: `repeat(${grid_rows}, 1fr)`,
        gridTemplateColumns: `repeat(${grid_columns}, 1fr)`,
        gap: '20px',
        height: '100%'
      }}
    >
      {fan_slots.length > 0 ? fan_slots.flat().map((fanNum, idx) => {

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
      }) : <div className="config-missing">No fan slots configured</div>}
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
  const [heatmapMode, setHeatmapMode] = useState('off'); // 'off', 'temp', 'voltage'

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
          <div className="view-header">
            <h4>Front View</h4>
          </div>
          <div className="heatmap-button-group">
            <button
              className={`heatmap-button ${heatmapMode === 'off' ? 'active' : ''}`}
              onClick={() => setHeatmapMode('off')}
              title="Turn off heatmap"
            >
              OFF
            </button>
            <button
              className={`heatmap-button ${heatmapMode === 'temp' ? 'active' : ''}`}
              onClick={() => setHeatmapMode('temp')}
              title="Temperature heatmap"
            >
              °C
            </button>
            <button
              className={`heatmap-button ${heatmapMode === 'voltage' ? 'active' : ''}`}
              onClick={() => setHeatmapMode('voltage')}
              title="Voltage heatmap"
            >
              V
            </button>
          </div>
          <div className="view-content">
            {systemMap.front.includes('ports') && (
              <div className="component-section ports-section">
                <PortGrid
                  portConfig={systemMap.ports}
                  qsfpData={qsfpData}
                  onPortClick={handlePortClick}
                  platform={platformConfig.platform}
                  heatmapMode={heatmapMode}
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
            {systemMap.rear.map((componentType, index) => {
              // Determine component width based on type
              const getComponentWidth = (type) => {
                if (type.startsWith('psu')) return '20%';
                if (type === 'fans') return '60%';
                return 'auto';
              };

              // Render component based on type
              const renderComponent = (type) => {
                if (type.startsWith('psu')) {
                  const psuConfig = { ...systemMap[type], section_type: type };
                  return <PSUGrid psuConfig={psuConfig} psuData={psuData} onPsuClick={handlePsuClick} />;
                } else if (type === 'fans') {
                  return <FanGrid fanConfig={systemMap.fans} fanData={fanData} onFanClick={handleFanClick} />;
                }
                return null;
              };

              return (
                <div
                  key={index}
                  className={`component-section ${componentType}-section`}
                  style={{ width: getComponentWidth(componentType) }}
                >
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