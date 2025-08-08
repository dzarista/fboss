import React, { memo } from 'react';

const PSUGrid = memo(function PSUGrid({ psuConfig, psuData = {}, onPsuClick }) {
  if (!psuConfig || typeof psuConfig !== 'object') return <div className="config-missing">No PSU configuration available</div>;
  const { grid_rows, grid_columns, psu_slots = [] } = psuConfig;

  return (
    <div
      className="psu-grid"
      style={{ display: 'grid', gridTemplateRows: `repeat(${grid_rows}, 1fr)`, gridTemplateColumns: `repeat(${grid_columns}, 1fr)`, gap: '20px', height: '100%' }}
    >
      {psu_slots.length > 0
        ? psu_slots.flat().map((slotNum, idx) => {
            let actualPsuNum = slotNum;
            if (psuConfig.section_type === 'psu_right') actualPsuNum = slotNum + 2; // right maps to PSU3/4
            const psuInfo = psuData[`PSU${actualPsuNum}`];
            const status = psuInfo?.status || 'Unknown';
            const voltageIn = psuInfo?.voltage_in || 'N/A';
            const voltageOut = psuInfo?.voltage_out || 'N/A';
            const powerOut = psuInfo?.power_out || 'N/A';
            const fanSpeeds = psuInfo?.fans || {};
            const fanSpeedText = Object.keys(fanSpeeds).length > 0 ? Object.values(fanSpeeds).join(', ') : 'N/A';

            return (
              <div
                key={idx}
                className={`psu-slot psu-${String(status).toLowerCase()}`}
                title={`PSU ${actualPsuNum}: ${status}\nVin: ${voltageIn}, Vout: ${voltageOut}\nPower: ${powerOut}\nFans: ${fanSpeedText}\nClick for details`}
                onClick={() => onPsuClick && onPsuClick(actualPsuNum, psuInfo)}
                style={{ cursor: onPsuClick ? 'pointer' : 'default' }}
              >
                <div className="psu-icon">
                  <svg width="16" height="16" viewBox="0 0 120 120" fill="black">
                    <path d="M80 10 L30 70 H55 L45 110 L95 50 H65 L80 10 Z" />
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
                    {Object.keys(fanSpeeds).length > 0 &&
                      Object.entries(fanSpeeds).map(([fanName, speed], fanIdx) => (
                        <div key={fanIdx} className="psu-fan-speed">
                          {fanName.replace('_RPM', '')}: {speed}
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            );
          })
        : <div className="config-missing">No PSU slots configured</div>}
    </div>
  );
});

export default PSUGrid;
