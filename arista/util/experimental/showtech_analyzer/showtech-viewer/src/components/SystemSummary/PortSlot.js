import React, { memo } from 'react';
import { pickTemperature, pickVoltage, getTemperatureColor, getVoltageColor } from './utils';

const PortSlot = memo(function PortSlot({
  idx,
  portNum,
  qsfpData,
  portType,
  heatmapMode,
  temperaturePercentiles,
  voltagePercentiles,
  onPortClick,
}) {
  if (portNum == null || portNum === 0) return <div key={idx} className="port-slot empty" />;

  const portData = qsfpData[portNum];
  const hasQsfpData = !!portData;

  const temperature = pickTemperature(portData);
  const voltage = pickVoltage(portData);

  let heatmapColor = null;
  let displayValue = null;
  if (hasQsfpData && heatmapMode === 'temp') {
    heatmapColor = getTemperatureColor(temperature, temperaturePercentiles);
    displayValue = temperature;
  } else if (hasQsfpData && heatmapMode === 'voltage') {
    heatmapColor = getVoltageColor(voltage, voltagePercentiles);
    displayValue = voltage;
  }

  let tooltip = `Port ${portNum} (${portType})`;
  if (hasQsfpData) {
    if (heatmapMode === 'temp' && temperature != null) {
      const tempDisplay = typeof temperature === 'number' ? `${temperature.toFixed(1)}°C` : `${temperature}°C`;
      tooltip += `\nTemp: ${tempDisplay}`;
    } else if (heatmapMode === 'voltage' && voltage != null) {
      const voltDisplay = typeof voltage === 'number' ? `${voltage.toFixed(2)}V` : `${voltage}V`;
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
      style={{ cursor: hasQsfpData ? 'pointer' : 'default', backgroundColor: heatmapColor || undefined }}
    >
      <span className="port-number">{portNum}</span>
      {heatmapMode !== 'off' && displayValue != null && (
        <span className="port-value">
          {heatmapMode === 'temp'
            ? (typeof displayValue === 'number' ? `${displayValue.toFixed(1)}°C` : `${displayValue}°C`)
            : (typeof displayValue === 'number' ? `${displayValue.toFixed(2)}V` : `${displayValue}V`)}
        </span>
      )}
    </div>
  );
});

export default PortSlot;
