// Utilities used across SystemSummary components

// Infer port type from port number (platform-specific heuristics)
export const inferPortType = (portNum, platform = null) => {
  return 'Unknown';
};

// Percentile calculation (inclusive, linear interpolation)
export const calculatePercentile = (values, percentile) => {
  const sorted = [...values].sort((a, b) => a - b);
  const index = (percentile / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index % 1;
  if (upper >= sorted.length) return sorted[sorted.length - 1];
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
};

// Heatmap color helpers
const getGradientColor = (value, minValue, maxValue) => {
  if (minValue === maxValue) return '#16a34a'; // All same value = green (original)

  // Linear interpolation from green (low) → yellow (mid) → red (high)
  const ratio = Math.max(0, Math.min(1, (value - minValue) / (maxValue - minValue)));
  let red, green, blue;

  if (ratio <= 0.5) {
    // Green to Yellow (first half) - darker colors
    const localRatio = ratio * 2; // 0 to 1
    red = Math.round(22 + (215 - 22) * localRatio);   // 22 → 215
    green = Math.round(163 + (183 - 163) * localRatio); // 163 → 183
    blue = Math.round(74 - 74 * localRatio);           // 74 → 0
  } else {
    // Yellow to Red (second half) - darker colors
    const localRatio = (ratio - 0.5) * 2;    // 0 to 1
    red = Math.round(215 + (220 - 215) * localRatio);   // 215 → 220
    green = Math.round(183 - (183 - 38) * localRatio);  // 183 → 38
    blue = Math.round(0 + (38 - 0) * localRatio);       // 0 → 38
  }

  return `rgb(${red}, ${green}, ${blue})`;
};
export const getTemperatureColor = (temperature, temperaturePercentiles, heatmapSettings) => {
  if (temperature == null) return null;
  const temp = typeof temperature === 'number' ? temperature : parseFloat(String(temperature).replace(' C', '').replace('°C', ''));
  if (Number.isNaN(temp)) return null;

  // Use custom settings if provided and not using default, otherwise fall back to percentiles
  if (heatmapSettings && !heatmapSettings.useDefault) {
    const { tempLow, tempHigh } = heatmapSettings;
    return getGradientColor(temp, tempLow, tempHigh);
  }

  // Fallback to percentile-based coloring with same gradient
  if (!temperaturePercentiles) return null;
  const { p25, p90 } = temperaturePercentiles;
  return getGradientColor(temp, p25, p90);
};

export const getVoltageColor = (voltage, voltagePercentiles, heatmapSettings) => {
  if (voltage == null) return null;
  const volt = typeof voltage === 'number' ? voltage : parseFloat(String(voltage).replace(' V', ''));
  if (Number.isNaN(volt)) return null;

  // Use custom settings if provided and not using default, otherwise fall back to percentiles
  if (heatmapSettings && !heatmapSettings.useDefault) {
    const { voltageLow, voltageHigh } = heatmapSettings;
    return getGradientColor(volt, voltageLow, voltageHigh);
  }

  // Fallback to percentile-based coloring with same gradient
  if (!voltagePercentiles) return null;
  const { p25, p90 } = voltagePercentiles;
  return getGradientColor(volt, p25, p90);
};

// Numeric extractors (safe parsing of text like "42 C" or "3.3 V")
export const pickTemperature = (portData) => {
  if (!portData) return null;
  const t = portData?.['Global DOM Monitors']?.['Temperature (C)'] ?? portData?.Temperature;
  if (t == null) return null;
  if (typeof t === 'number') return t;
  const n = parseFloat(String(t).replace(' C', '').replace('°C', ''));
  return Number.isNaN(n) ? null : n;
};

export const pickVoltage = (portData) => {
  if (!portData) return null;
  const v = portData?.['Global DOM Monitors']?.['Voltage (V)']
    ?? portData?.['Global DOM Monitors']?.['Voltage']
    ?? portData?.Voltage
    ?? portData?.['Supply Voltage'];
  if (v == null) return null;
  if (typeof v === 'number') return v;
  const n = parseFloat(String(v).replace(' V', ''));
  return Number.isNaN(n) ? null : n;
};
