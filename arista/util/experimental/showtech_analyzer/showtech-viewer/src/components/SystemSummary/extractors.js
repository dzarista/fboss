// Pure extractors for SystemSummary

export const extractQsfpData = (sections) => {
  const qsfpData = {};
  sections.forEach((section) => {
    if (section.section_type === 'qsfp_util' && section.parsed_data?.ports) {
      section.parsed_data.ports.forEach((portData) => {
        if (portData?.port) qsfpData[portData.port] = portData;
      });
    }
  });
  return qsfpData;
};

export const extractFanData = (sections) => {
  const fansSection = sections.find((s) => s.title === 'FANS');
  if (fansSection && fansSection.parsed_data?.type === 'fans') return fansSection.parsed_data.rows || [];
  const fanSection = sections.find((s) => s.title === 'fboss2 show environment fan');
  if (fanSection && fanSection.parsed_data?.type === 'table') return fanSection.parsed_data.rows || [];
  return [];
};

export const extractPsuData = (sections) => {
  const sensorSection = sections.find((s) => s.title === 'fboss2 show environment sensor');
  if (!sensorSection || sensorSection.parsed_data?.type !== 'table') return {};

  const rows = sensorSection.parsed_data.rows || [];
  const psuData = {};

  rows.forEach((row) => {
    const sensor = row.Sensor || '';
    const value = row.Value || '';
    const health = row.SensorHealth || '';
    const psuMatch = sensor.match(/^PSU(\d+)_(.+)$/);
    if (!psuMatch) return;

    const psuNum = psuMatch[1];
    const metric = psuMatch[2];
    const key = `PSU${psuNum}`;

    if (!psuData[key]) {
      psuData[key] = {
        name: key,
        status: 'Good',
        fans: {},
        voltage_in: null,
        voltage_out: null,
        power_in: null,
        power_out: null,
        temperatures: {},
      };
    }

    const psu = psuData[key];
    if (health && health !== 'Good') psu.status = health;

    if (metric.includes('FAN') && metric.includes('RPM')) psu.fans[metric] = `${value} RPM`;
    else if (metric === 'VIN') psu.voltage_in = `${value}V`;
    else if (metric === 'VOUT') psu.voltage_out = `${value}V`;
    else if (metric === 'PIN') psu.power_in = `${value}W`;
    else if (metric === 'POUT') psu.power_out = `${value}W`;
    else if (metric.includes('TEMP')) psu.temperatures[metric] = `${value}°C`;
  });

  return psuData;
};

export const extractPsuDebugData = (sections) => {
  const psuDebugSection = sections.find((s) => s.title === 'PSU debug info');
  if (!psuDebugSection || psuDebugSection.parsed_data?.type !== 'psu_debug') return {};
  const psuSlots = psuDebugSection.parsed_data.psu_slots || [];
  const psuDebugData = {};
  psuSlots.forEach((psuSlot) => {
    const psuNum = psuSlot.slot;
    psuDebugData[`PSU${psuNum}`] = {
      slot: psuNum,
      properties: psuSlot.properties || {},
    };
  });
  return psuDebugData;
};

export const extractPhyData = (sections) => {
  const phySection = sections.find(
    (section) => section.title === 'fboss2 show interface phy' && section.parsed_data?.type === 'fboss2_interface_phy'
  );
  if (!phySection || !phySection.parsed_data?.interfaces) return {};

  const phyData = {};
  phySection.parsed_data.interfaces.forEach((interfaceData) => {
    const match = interfaceData.interface.match(/eth\d+\/(\d+)\/\d+/);
    if (match) {
      const portNum = parseInt(match[1], 10);
      if (!phyData[portNum]) phyData[portNum] = [];
      phyData[portNum].push(interfaceData);
    }
  });
  return phyData;
};

export const extractInterfaceData = (sections) => {
  const interfaceData = {};
  const interfaceSections = [
    'fboss2 show lldp',
    'fboss2 show interface counters',
    'fboss2 show interface errors',
    'fboss2 show interface flaps',
    'fboss2 show transceiver',
  ];

  interfaceSections.forEach((sectionTitle) => {
    const section = sections.find((s) => s.title === sectionTitle);
    if (!(section && section.parsed_data?.type === 'table' && section.parsed_data?.rows)) return;

    section.parsed_data.rows.forEach((row) => {
      let interfaceName = null;
      const possibleColumns = [
        'Interface Name',
        'Interface',
        'Local Int',
        'Name',
        'Port',
        'LocalInterface',
        'LocalPort',
        'Local Interface',
        'Local Port',
      ];
      for (const col of possibleColumns) {
        if (row[col]) { interfaceName = row[col]; break; }
      }
      if (!interfaceName) return;

      const ethMatch = interfaceName.match(/eth\d+\/(\d+)\/\d+/);
      const fabMatch = interfaceName.match(/fab\d+\/(\d+)\/\d+/);
      const match = ethMatch || fabMatch;
      if (!match) return;

      const portNum = parseInt(match[1], 10);
      if (!interfaceData[portNum]) interfaceData[portNum] = {};
      if (!interfaceData[portNum][sectionTitle]) interfaceData[portNum][sectionTitle] = [];
      interfaceData[portNum][sectionTitle].push({ interface: interfaceName, ...row });
    });
  });

  return interfaceData;
};

// Extract port type information from interface sections
export const extractPortTypes = (sections) => {
  const portTypes = {};

  // Look for sections that contain interface information
  const interfaceSections = [
    'fboss2 show interface',
    'fboss2 show interface status',
    'fboss2 show interface counters',
    'fboss2 show port',
    'fboss2 show port status'
  ];

  interfaceSections.forEach((sectionTitle) => {
    const section = sections.find((s) => s.title === sectionTitle);
    if (!(section && section.parsed_data?.type === 'table' && section.parsed_data?.rows)) return;

    section.parsed_data.rows.forEach((row) => {
      // Look for interface name in various possible column names
      let interfaceName = null;
      const possibleColumns = [
        'Interface Name',
        'Interface',
        'Name',
        'Port',
        'Port Name',
        'Intf',
        'Local Interface'
      ];

      for (const col of possibleColumns) {
        if (row[col]) {
          interfaceName = row[col];
          break;
        }
      }

      if (!interfaceName) return;

      // Extract port number and type from interface name patterns like:
      // eth1/11/1 -> port 11, type 'eth'
      // fab1/25/1 -> port 25, type 'fab'
      const ethMatch = interfaceName.match(/eth\d+\/(\d+)\/\d+/);
      const fabMatch = interfaceName.match(/fab\d+\/(\d+)\/\d+/);

      if (ethMatch) {
        const portNum = parseInt(ethMatch[1], 10);
        portTypes[portNum] = 'eth';
      } else if (fabMatch) {
        const portNum = parseInt(fabMatch[1], 10);
        portTypes[portNum] = 'fab';
      }
    });
  });

  return portTypes;
};
