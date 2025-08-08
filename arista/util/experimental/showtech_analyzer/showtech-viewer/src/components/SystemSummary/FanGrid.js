import React, { memo } from 'react';
import { FanIcon } from '../../assets/icons/Icon';

const FanGrid = memo(function FanGrid({ fanConfig, fanData = [], onFanClick }) {
  if (!fanConfig || typeof fanConfig !== 'object') return <div className="config-missing">No fan configuration available</div>;
  const { grid_rows, grid_columns, fan_slots = [] } = fanConfig;

  return (
    <div
      className="fan-grid"
      style={{ display: 'grid', gridTemplateRows: `repeat(${grid_rows}, 1fr)`, gridTemplateColumns: `repeat(${grid_columns}, 1fr)`, gap: '20px', height: '100%' }}
    >
      {fan_slots.length > 0
        ? fan_slots.flat().map((fanNum, idx) => {
            const fanInfo = fanData.find((f) => {
              const name = f.Name || '';
              const match = name.match(/(\d+)$/);
              return match && parseInt(match[1], 10) === fanNum;
            });
            const status = fanInfo?.Status || 'Unknown';
            const rpm = fanInfo?.RPM || 'N/A';
            const percentage = fanInfo?.Percentage || 'N/A';

            return (
              <div
                key={idx}
                className={`fan-slot fan-${String(status).toLowerCase()}`}
                title={`Fan ${fanNum}: ${status}, RPM: ${rpm}, Load: ${percentage}\nClick for details`}
                onClick={() => onFanClick && onFanClick(fanNum, fanInfo)}
                style={{ cursor: onFanClick ? 'pointer' : 'default' }}
              >
                <div className="fan-icon">
                  <FanIcon />
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
          })
        : <div className="config-missing">No fan slots configured</div>}
    </div>
  );
});

export default FanGrid;
