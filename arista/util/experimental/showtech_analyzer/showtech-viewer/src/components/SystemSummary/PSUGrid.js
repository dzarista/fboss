import React, { memo } from 'react';
import { PSUIcon } from '../../assets/icons/Icon';

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
            // Use the slot number directly from the configuration
            const actualPsuNum = slotNum;
            const psuInfo = psuData[`PSU${actualPsuNum}`];

            // Get all display fields dynamically (show everything except name)
            const getAllFields = () => {
              if (!psuInfo) return [];

              // Skip 'name' and show all other fields
              const excludeKeys = ['name'];
              const availableKeys = Object.keys(psuInfo).filter(key => !excludeKeys.includes(key));

              // Return all fields for display
              return availableKeys.map(key => ({
                key,
                value: psuInfo[key] || 'N/A'
              }));
            };

            const displayFields = getAllFields();

            // Create tooltip with all available data
            const createTooltip = () => {
              if (!psuInfo) return `PSU ${actualPsuNum}: No data available`;
              const lines = [`PSU ${actualPsuNum}:`];
              Object.entries(psuInfo).forEach(([key, value]) => {
                if (key !== 'name') {
                  lines.push(`${key}: ${value}`);
                }
              });
              lines.push('Click for details');
              return lines.join('\n');
            };

            return (
              <div
                key={idx}
                className={`psu-slot psu-normal`}
                title={createTooltip()}
                onClick={() => onPsuClick && onPsuClick(actualPsuNum, psuInfo)}
                style={{ cursor: onPsuClick ? 'pointer' : 'default' }}
              >
                <div className="psu-icon">
                  <PSUIcon />
                </div>
                <div className="psu-content">
                  <div className="psu-header">
                    <div className="psu-label">PSU{actualPsuNum}</div>
                  </div>
                  <div className="psu-data-row">
                    {displayFields.map((field, fieldIdx) => (
                      <div key={fieldIdx} className="psu-field">
                        {field.key}: {field.value}
                      </div>
                    ))}
                    {displayFields.length === 0 && (
                      <div className="psu-field">No data</div>
                    )}
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
