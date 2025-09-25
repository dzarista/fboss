import { findDiff, getDiffCssClass } from './findDiff';

describe('findDiff - Diff Detection Tests', () => {
  describe('I2C dump diffing', () => {
    const createI2CSection = (data) => ({
      parsed_data: {
        type: 'i2c_dump',
        data
      }
    });

    test('should detect no differences when i2c dumps are identical', () => {
      const section1 = createI2CSection({
        '00': { value: '0x12', command: 'read', bytes: 1 },
        '01': { value: '0x34', command: 'read', bytes: 1 }
      });
      const section2 = createI2CSection({
        '00': { value: '0x12', command: 'read', bytes: 1 },
        '01': { value: '0x34', command: 'read', bytes: 1 }
      });

      const file1 = { sections: [section1] };
      const file2 = { sections: [section2] };

      const { file1Diffs, file2Diffs } = findDiff(file1, file2);

      expect(file1Diffs.size).toBe(0);
      expect(file2Diffs.size).toBe(0);
    });

    test('should detect value changes in i2c dumps', () => {
      const section1 = createI2CSection({
        '00': { value: '0x12', command: 'read', bytes: 1 },
        '01': { value: '0x34', command: 'read', bytes: 1 }
      });
      const section2 = createI2CSection({
        '00': { value: '0x56', command: 'read', bytes: 1 }, // Changed value
        '01': { value: '0x34', command: 'read', bytes: 1 }
      });

      const file1 = { sections: [section1] };
      const file2 = { sections: [section2] };

      const { file1Diffs, file2Diffs } = findDiff(file1, file2);

      expect(file1Diffs.size).toBe(1);
      expect(file2Diffs.size).toBe(1);

      const diff = file1Diffs.get(0);
      expect(diff.type).toBe('i2c_dump');
      expect(diff.diffs.size).toBe(1);
      expect(diff.diffs.get('00').type).toBe('change');
      expect(diff.diffs.get('00').data1.value).toBe('0x12');
      expect(diff.diffs.get('00').data2.value).toBe('0x56');
    });

    test('should detect command changes in i2c dumps', () => {
      const section1 = createI2CSection({
        '00': { value: '0x12', command: 'read', bytes: 1 }
      });
      const section2 = createI2CSection({
        '00': { value: '0x12', command: 'write', bytes: 1 } // Changed command
      });

      const file1 = { sections: [section1] };
      const file2 = { sections: [section2] };

      const { file1Diffs, file2Diffs } = findDiff(file1, file2);

      expect(file1Diffs.get(0).diffs.get('00').type).toBe('change');
    });

    test('should detect insertions in i2c dumps', () => {
      const section1 = createI2CSection({
        '00': { value: '0x12', command: 'read', bytes: 1 }
      });
      const section2 = createI2CSection({
        '00': { value: '0x12', command: 'read', bytes: 1 },
        '01': { value: '0x34', command: 'read', bytes: 1 } // New address
      });

      const file1 = { sections: [section1] };
      const file2 = { sections: [section2] };

      const { file1Diffs, file2Diffs } = findDiff(file1, file2);

      const diff = file1Diffs.get(0);
      expect(diff.diffs.get('01').type).toBe('insert');
      expect(diff.diffs.get('01').data1).toBe(null);
      expect(diff.diffs.get('01').data2.value).toBe('0x34');
    });

    test('should detect deletions in i2c dumps', () => {
      const section1 = createI2CSection({
        '00': { value: '0x12', command: 'read', bytes: 1 },
        '01': { value: '0x34', command: 'read', bytes: 1 }
      });
      const section2 = createI2CSection({
        '00': { value: '0x12', command: 'read', bytes: 1 }
        // '01' is deleted
      });

      const file1 = { sections: [section1] };
      const file2 = { sections: [section2] };

      const { file1Diffs, file2Diffs } = findDiff(file1, file2);

      const diff = file1Diffs.get(0);
      expect(diff.diffs.get('01').type).toBe('delete');
      expect(diff.diffs.get('01').data1.value).toBe('0x34');
      expect(diff.diffs.get('01').data2).toBe(null);
    });
  });

  describe('Table diffing', () => {
    const createTableSection = (headers, rows) => ({
      parsed_data: {
        type: 'table',
        headers,
        rows
      }
    });

    test('should detect no differences when tables are identical', () => {
      const section1 = createTableSection(
        ['Name', 'Status', 'Value'],
        [
          { Name: 'Port1', Status: 'Up', Value: '100G' },
          { Name: 'Port2', Status: 'Down', Value: '10G' }
        ]
      );
      const section2 = createTableSection(
        ['Name', 'Status', 'Value'],
        [
          { Name: 'Port1', Status: 'Up', Value: '100G' },
          { Name: 'Port2', Status: 'Down', Value: '10G' }
        ]
      );

      const file1 = { sections: [section1] };
      const file2 = { sections: [section2] };

      const { file1Diffs, file2Diffs } = findDiff(file1, file2);

      expect(file1Diffs.size).toBe(0);
      expect(file2Diffs.size).toBe(0);
    });

    test('should detect value changes in tables', () => {
      const section1 = createTableSection(
        ['Name', 'Status', 'Value'],
        [
          { Name: 'Port1', Status: 'Up', Value: '100G' },
          { Name: 'Port2', Status: 'Down', Value: '10G' }
        ]
      );
      const section2 = createTableSection(
        ['Name', 'Status', 'Value'],
        [
          { Name: 'Port1', Status: 'Down', Value: '100G' }, // Status changed
          { Name: 'Port2', Status: 'Down', Value: '10G' }
        ]
      );

      const file1 = { sections: [section1] };
      const file2 = { sections: [section2] };

      const { file1Diffs, file2Diffs } = findDiff(file1, file2);

      expect(file1Diffs.size).toBe(1);
      const diff = file1Diffs.get(0);
      expect(diff.type).toBe('table');
      expect(diff.diffs.size).toBe(1);
      expect(diff.diffs.get('Port1').type).toBe('change');
      expect(diff.diffs.get('Port1').data1.Status).toBe('Up');
      expect(diff.diffs.get('Port1').data2.Status).toBe('Down');
    });

    test('should detect row insertions in tables', () => {
      const section1 = createTableSection(
        ['Name', 'Status'],
        [{ Name: 'Port1', Status: 'Up' }]
      );
      const section2 = createTableSection(
        ['Name', 'Status'],
        [
          { Name: 'Port1', Status: 'Up' },
          { Name: 'Port2', Status: 'Down' } // New row
        ]
      );

      const file1 = { sections: [section1] };
      const file2 = { sections: [section2] };

      const { file1Diffs, file2Diffs } = findDiff(file1, file2);

      const diff = file1Diffs.get(0);
      expect(diff.diffs.get('Port2').type).toBe('insert');
      expect(diff.diffs.get('Port2').data1).toBe(null);
      expect(diff.diffs.get('Port2').data2.Name).toBe('Port2');
    });

    test('should detect row deletions in tables', () => {
      const section1 = createTableSection(
        ['Name', 'Status'],
        [
          { Name: 'Port1', Status: 'Up' },
          { Name: 'Port2', Status: 'Down' }
        ]
      );
      const section2 = createTableSection(
        ['Name', 'Status'],
        [{ Name: 'Port1', Status: 'Up' }]
        // Port2 deleted
      );

      const file1 = { sections: [section1] };
      const file2 = { sections: [section2] };

      const { file1Diffs, file2Diffs } = findDiff(file1, file2);

      const diff = file1Diffs.get(0);
      expect(diff.diffs.get('Port2').type).toBe('delete');
      expect(diff.diffs.get('Port2').data1.Name).toBe('Port2');
      expect(diff.diffs.get('Port2').data2).toBe(null);
    });
  });

  describe('getDiffCssClass', () => {
    test('should return correct CSS classes', () => {
      expect(getDiffCssClass('insert')).toBe('diff-insert');
      expect(getDiffCssClass('delete')).toBe('diff-delete');
      expect(getDiffCssClass('change')).toBe('diff-change');
      expect(getDiffCssClass('unknown')).toBe('');
      expect(getDiffCssClass(null)).toBe('');
      expect(getDiffCssClass(undefined)).toBe('');
    });
  });
});
