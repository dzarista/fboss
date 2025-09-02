import { memo } from 'react';
import { pickTemperature, pickVoltage, getTemperatureColor, getVoltageColor } from './utils';

const PortSlot = memo(function PortSlot({
  idx,
  portNum,
  qsfpData,
  portType,
  heatmapMode,
  temperaturePercentiles,
  voltagePercentiles,
  heatmapSettings,
  onPortClick,
}) {
  if (portNum == null || portNum === 0) return <div key={idx} className="port-slot empty" />;

  const portData = qsfpData[portNum];
  const hasQsfpData = !!portData;

  const temperature = pickTemperature(portData);
  const voltage = pickVoltage(portData);

  let heatmapColor = null;
  let displayValue = null;

  if (hasQsfpData) {
    const value = heatmapMode === 'temp' ? temperature : voltage;

    if (value != null) {
      heatmapColor = heatmapMode === 'temp'
        ? getTemperatureColor(value, temperaturePercentiles, heatmapSettings)
        : getVoltageColor(value, voltagePercentiles, heatmapSettings);
      displayValue = value;
    }
  }

  const value = heatmapMode === 'temp' ? temperature : voltage;
  const unit = heatmapMode === 'temp' ? '°C' : 'V';
  const decimals = heatmapMode === 'temp' ? 1 : 2;

  let tooltip = `Port ${portNum} (${portType})`;
  if (hasQsfpData) {
    if (value != null) {
      const valueDisplay = `${typeof value === 'number' ? value.toFixed(decimals) : value}${unit}`;
      tooltip += `\n${heatmapMode === 'temp' ? 'Temp' : 'Voltage'}: ${valueDisplay}`;
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
      {displayValue != null && (
        <span className="port-value">
          {`${typeof displayValue === 'number' ? displayValue.toFixed(decimals) : displayValue}${unit}`}
        </span>
      )}
    </div>
  );
});

export default PortSlot;
