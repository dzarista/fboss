import React, { useMemo, memo } from 'react';
import PortSlot from './PortSlot';
import { pickTemperature, pickVoltage, calculatePercentile } from './utils';

const PortGrid = memo(function PortGrid({ portConfig, qsfpData, portTypes = {}, onPortClick, heatmapMode = 'off' }) {
  const { grid_rows, grid_columns, port_map } = portConfig || {};

  const grid = useMemo(() => {
    if (!portConfig) return [];

    if (Array.isArray(port_map)) return port_map;
    if (Array.isArray(port_map)) return port_map;
    const { major_order, empty_grid_slots = [] } = portConfig;
    const empty = new Set(empty_grid_slots.map((slot) => `${slot[0]}-${slot[1]}`));
    const g = Array(grid_rows).fill(null).map(() => Array(grid_columns).fill(null));

    let portIndex = 1;
    if (major_order === 'column') {
      for (let col = 0; col < grid_columns; col++) {
        for (let row = 0; row < grid_rows; row++) {
          if (!empty.has(`${row}-${col}`)) g[row][col] = portIndex++;
        }
      }
    } else {
      for (let row = 0; row < grid_rows; row++) {
        for (let col = 0; col < grid_columns; col++) {
          if (!empty.has(`${row}-${col}`)) g[row][col] = portIndex++;
        }
      }
    }
    return g;
  }, [grid_rows, grid_columns, port_map, portConfig]);

  const { temperaturePercentiles, voltagePercentiles } = useMemo(() => {
    const temps = Object.values(qsfpData || {})
      .map(pickTemperature)
      .filter((t) => t != null && !Number.isNaN(t));
    const volts = Object.values(qsfpData || {})
      .map(pickVoltage)
      .filter((v) => v != null && !Number.isNaN(v));
    return {
      temperaturePercentiles: temps.length
        ? { p25: calculatePercentile(temps, 25), p50: calculatePercentile(temps, 50), p75: calculatePercentile(temps, 75), p90: calculatePercentile(temps, 90) }
        : null,
      voltagePercentiles: volts.length
        ? { p25: calculatePercentile(volts, 25), p50: calculatePercentile(volts, 50), p75: calculatePercentile(volts, 75), p90: calculatePercentile(volts, 90) }
        : null,
    };
  }, [qsfpData]);

  return (
    <div
      className="port-grid"
      style={{
        display: 'grid',
        gridTemplateRows: `repeat(${grid_rows}, 1fr)`,
        gridTemplateColumns: `repeat(${grid_columns}, 1fr)`,
        gap: '4px',
        minHeight: '200px',
      }}
    >
      {grid.flat().map((portNum, idx) => (
        <PortSlot
          key={idx}
          idx={idx}
          portNum={portNum}
          qsfpData={qsfpData}
          portType={portTypes[portNum] || 'unknown'}
          heatmapMode={heatmapMode}
          temperaturePercentiles={temperaturePercentiles}
          voltagePercentiles={voltagePercentiles}
          onPortClick={onPortClick}
        />
      ))}
    </div>
  );
});

export default PortGrid;
