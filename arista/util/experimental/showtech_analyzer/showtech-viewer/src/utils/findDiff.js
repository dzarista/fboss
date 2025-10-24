/**
 * Unified diff utility for all section types
 */

/**
 * Compare two i2c dump sections
 */
function compareI2CSections(section1, section2) {
  if (!section1?.parsed_data?.data || !section2?.parsed_data?.data) {
    return new Map();
  }

  const data1 = section1.parsed_data.data;
  const data2 = section2.parsed_data.data;
  const diffs = new Map(); // address -> { type, data1, data2 }

  // Get all addresses from both dumps
  const allAddresses = new Set([...Object.keys(data1), ...Object.keys(data2)]);

  for (const address of allAddresses) {
    const reg1 = data1[address];
    const reg2 = data2[address];

    if (!reg1 && reg2) {
      // Address only exists in dump2 - insertion
      diffs.set(address, { 
        type: 'insert', 
        data1: null, 
        data2: reg2 
      });
    } else if (reg1 && !reg2) {
      // Address only exists in dump1 - deletion
      diffs.set(address, { 
        type: 'delete', 
        data1: reg1, 
        data2: null 
      });
    } else if (reg1 && reg2) {
      // Both addresses exist - compare values
      const value1 = reg1.value;
      const value2 = reg2.value;
      const command1 = reg1.command;
      const command2 = reg2.command;

      if (value1 !== value2 || command1 !== command2) {
        diffs.set(address, { 
          type: 'change', 
          data1: reg1, 
          data2: reg2 
        });
      }
    }
  }

  return diffs;
}

/**
 * Compare two table sections using first column as key
 */
function compareTableSections(section1, section2) {
  if (!section1?.parsed_data?.rows || !section2?.parsed_data?.rows) {
    return new Map();
  }

  const rows1 = section1.parsed_data.rows;
  const rows2 = section2.parsed_data.rows;
  const headers1 = section1.parsed_data.headers || [];
  const headers2 = section2.parsed_data.headers || [];

  // Use first header as the key column
  const keyColumn = headers1[0] || headers2[0];
  if (!keyColumn) {
    return new Map();
  }

  const diffs = new Map(); // keyValue -> { type, rowIndex1, rowIndex2, data1, data2 }

  // Create maps using first column value as key
  const map1 = new Map();
  const map2 = new Map();

  rows1.forEach((row, index) => {
    if (row && row[keyColumn] !== undefined && row[keyColumn] !== null) {
      const key = String(row[keyColumn]); // Convert to string for consistent comparison
      map1.set(key, { rowIndex: index, data: row });
    }
  });

  rows2.forEach((row, index) => {
    if (row && row[keyColumn] !== undefined && row[keyColumn] !== null) {
      const key = String(row[keyColumn]); // Convert to string for consistent comparison
      map2.set(key, { rowIndex: index, data: row });
    }
  });

  // Get all keys from both tables
  const allKeys = new Set([...map1.keys(), ...map2.keys()]);

  for (const key of allKeys) {
    const row1 = map1.get(key);
    const row2 = map2.get(key);

    if (!row1 && row2) {
      // Row only exists in table2 - insertion
      diffs.set(key, {
        type: 'insert',
        rowIndex1: null,
        rowIndex2: row2.rowIndex,
        data1: null,
        data2: row2.data
      });
    } else if (row1 && !row2) {
      // Row only exists in table1 - deletion
      diffs.set(key, {
        type: 'delete',
        rowIndex1: row1.rowIndex,
        rowIndex2: null,
        data1: row1.data,
        data2: null
      });
    } else if (row1 && row2) {
      // Both rows exist - compare all columns
      const data1 = row1.data;
      const data2 = row2.data;

      // Check if rows are different by comparing all header values
      const allHeaders = new Set([...headers1, ...headers2]);
      let hasChanges = false;

      for (const header of allHeaders) {
        if (data1[header] !== data2[header]) {
          hasChanges = true;
          break;
        }
      }

      if (hasChanges) {
        diffs.set(key, {
          type: 'change',
          rowIndex1: row1.rowIndex,
          rowIndex2: row2.rowIndex,
          data1: data1,
          data2: data2
        });
      }
    }
  }

  return diffs;
}

/**
 * Compare two sections and return diff information based on section type
 */
function compareSections(section1, section2) {
  if (!section1?.parsed_data || !section2?.parsed_data) {
    return new Map();
  }

  const type1 = section1.parsed_data.type;
  const type2 = section2.parsed_data.type;

  // Only diff if both sections have the same type
  if (type1 !== type2) {
    return new Map();
  }

  switch (type1) {
    case 'i2c_dump':
      return compareI2CSections(section1, section2);
    
    case 'table':
    case 'temperature_table':
      return compareTableSections(section1, section2);
    
    default:
      return new Map(); // Unsupported type
  }
}

/**
 * Generate diffs for all sections between two files
 */
export function findDiff(file1, file2) {
  if (!file1?.sections || !file2?.sections) {
    return { file1Diffs: new Map(), file2Diffs: new Map() };
  }

  const file1Diffs = new Map();
  const file2Diffs = new Map();

  // Compare sections by index (assuming they correspond)
  const maxSections = Math.max(file1.sections.length, file2.sections.length);

  for (let i = 0; i < maxSections; i++) {
    const section1 = file1.sections[i];
    const section2 = file2.sections[i];

    if (section1 && section2) {
      const sectionDiffs = compareSections(section1, section2);
      
      if (sectionDiffs.size > 0) {
        // Store the same diff for both files since they reference the same comparison
        file1Diffs.set(i, {
          type: section1.parsed_data.type,
          diffs: sectionDiffs
        });
        file2Diffs.set(i, {
          type: section2.parsed_data.type,
          diffs: sectionDiffs
        });
      }
    }
  }

  return { file1Diffs, file2Diffs };
}

/**
 * Get the CSS class for a diff type
 */
export function getDiffCssClass(diffType) {
  switch (diffType) {
    case 'insert':
      return 'diff-insert';
    case 'delete':
      return 'diff-delete';
    case 'change':
      return 'diff-change';
    default:
      return '';
  }
}
