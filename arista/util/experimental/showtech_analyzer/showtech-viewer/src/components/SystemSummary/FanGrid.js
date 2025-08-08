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

            // Extract dynamic data from fanInfo
            const getDisplayValue = (value) => {
              if (!value || value === 'N/A') return 'N/A';
              return value;
            };



            // Get all display fields dynamically (show everything except Name)
            const getAllFields = () => {
              if (!fanInfo) return [];

              // Skip 'Name' and show all other fields
              const excludeKeys = ['Name'];
              const availableKeys = Object.keys(fanInfo).filter(key => !excludeKeys.includes(key));

              // Return all fields for display
              return availableKeys.map(key => ({
                key,
                value: getDisplayValue(fanInfo[key])
              }));
            };

            const displayFields = getAllFields();

            // Create tooltip with all available data
            const createTooltip = () => {
              if (!fanInfo) return `Fan ${fanNum}: No data available`;
              const lines = [`Fan ${fanNum}:`];
              Object.entries(fanInfo).forEach(([key, value]) => {
                if (key !== 'Name') {
                  lines.push(`${key}: ${value}`);
                }
              });
              lines.push('Click for details');
              return lines.join('\n');
            };

            return (
              <div
                key={idx}
                className={`fan-slot`}
                title={createTooltip()}
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
                    {displayFields.map((field, fieldIdx) => (
                      <div key={fieldIdx} className="fan-field">
                        {field.key}: {field.value}
                      </div>
                    ))}
                    {displayFields.length === 0 && (
                      <div className="fan-field">No data</div>
                    )}
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
