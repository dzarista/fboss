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
export const getTemperatureColor = (temperature, temperaturePercentiles) => {
  if (temperature == null || !temperaturePercentiles) return null;
  const temp = typeof temperature === 'number' ? temperature : parseFloat(String(temperature).replace(' C', '').replace('°C', ''));
  if (Number.isNaN(temp)) return null;
  const { p25, p50, p75, p90 } = temperaturePercentiles;
  if (temp >= p90) return '#dc2626';
  if (temp >= p75) return '#ea580c';
  if (temp >= p50) return '#d97706';
  if (temp >= p25) return '#65a30d';
  return '#16a34a';
};

export const getVoltageColor = (voltage, voltagePercentiles) => {
  if (voltage == null || !voltagePercentiles) return null;
  const volt = typeof voltage === 'number' ? voltage : parseFloat(String(voltage).replace(' V', ''));
  if (Number.isNaN(volt)) return null;
  const { p25, p50, p75, p90 } = voltagePercentiles;
  if (volt >= p90) return '#dc2626';
  if (volt >= p75) return '#ea580c';
  if (volt >= p50) return '#d97706';
  if (volt >= p25) return '#65a30d';
  return '#16a34a';
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
