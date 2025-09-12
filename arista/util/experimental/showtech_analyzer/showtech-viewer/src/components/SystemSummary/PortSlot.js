import { memo } from 'react';
import { pickTemperature, pickVoltage, getTemperatureColor, getVoltageColor } from './utils';

const PortSlot = memo(function PortSlot({
  idx,
  portNum,
  qsfpData,
  portType,
  portStatus,
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

  // Determine port status light
  let statusLight = null;
  if (portStatus) {
    const { adminState, linkState, transceiver } = portStatus;
    const isActiveAndDown = adminState === 'Enabled' && transceiver === 'Present' && linkState === 'Down';
    const isActiveAndUp = adminState === 'Enabled' && transceiver === 'Present' && linkState === 'Up';

    if (isActiveAndDown) {
      statusLight = 'error'; // Red light for active but down ports
    } else if (isActiveAndUp) {
      statusLight = 'success'; // Green light for active and up ports
    }
  }

  let tooltip = `Port ${portNum} (${portType})`;
  if (portStatus) {
    tooltip += `\nAdmin: ${portStatus.adminState}, Link: ${portStatus.linkState}, Transceiver: ${portStatus.transceiver}`;
  }
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
      {statusLight && (
        <div className={`port-status-light ${statusLight}`} />
      )}
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
