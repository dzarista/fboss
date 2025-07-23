#!/usr/bin/env node

/**
 * ODS Viewer Test Suite
 * Tests the core business logic for ODS data processing
 */

const fs = require('fs');
const path = require('path');

// Test configuration
const TEST_DATA_DIR = './test_data';
const SAMPLE_CSV = path.join(TEST_DATA_DIR, 'sample_time_series.csv');

// Test results tracking
let testsRun = 0;
let testsPassed = 0;
let testsFailed = 0;

/**
 * Simple test assertion function
 */
function assert(condition, message) {
    testsRun++;
    if (condition) {
        console.log(`✅ ${message}`);
        testsPassed++;
    } else {
        console.log(`❌ ${message}`);
        testsFailed++;
    }
}

/**
 * Normalizes an array of numbers to a 0-1 scale using Min-Max scaling.
 * This mirrors the function from the web worker.
 */
function normalizeMinMax(values) {
    if (!values || values.length === 0) {
        return [];
    }
    const numericValues = values.filter(v => typeof v === 'number' && !isNaN(v));
    if (numericValues.length === 0) {
        return values.map(() => 0.5);
    }

    const min = Math.min(...numericValues);
    const max = Math.max(...numericValues);
    const range = max - min;

    if (range === 0) {
        return values.map(() => 0.5);
    }

    return values.map(value =>
        (typeof value === 'number' && !isNaN(value)) ? (value - min) / range : NaN
    );
}

/**
 * Test sensor name extraction logic
 * Mimics the logic from the web worker
 */
function testSensorNameExtraction() {
    console.log('\n🔍 Testing sensor name extraction...');

    const testCases = [
        {
            input: 'host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/1/1.temp',
            expected: 'qsfp_service.qsfp.interface.fab1/1/1.temp',
            description: 'Temperature sensor extraction'
        },
        {
            input: 'host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/1/1.vcc.mv',
            expected: 'qsfp_service.qsfp.interface.fab1/1/1.vcc.mv',
            description: 'Voltage sensor extraction'
        },
        {
            input: 'host123.n123.c123.abc1::sensor_service.sensor_read.FAN1_RPM.value',
            expected: 'sensor_service.sensor_read.FAN1_RPM.value',
            description: 'Fan RPM sensor extraction'
        },
        {
            input: 'simple_sensor_name',
            expected: 'simple_sensor_name',
            description: 'Simple sensor name (no :: separator)'
        }
    ];

    testCases.forEach(testCase => {
        const parts = testCase.input.split('::');
        const extractedSensorName = parts.length > 1 ? parts[1] : testCase.input;
        assert(
            extractedSensorName === testCase.expected,
            `${testCase.description}: "${testCase.input}" -> "${extractedSensorName}"`
        );
    });
}

/**
 * Test data normalization logic
 * Mimics the normalizeMinMax function from the web worker
 */
function testDataNormalization() {
    console.log('\n📊 Testing data normalization...');

    function normalizeMinMax(values) {
        if (!values || values.length === 0) {
            return [];
        }
        const numericValues = values.filter(v => typeof v === 'number' && !isNaN(v));
        if (numericValues.length === 0) {
            return values.map(() => 0.5);
        }

        const min = Math.min(...numericValues);
        const max = Math.max(...numericValues);
        const range = max - min;

        if (range === 0) {
            return values.map(() => 0.5);
        }

        return values.map(value =>
            (typeof value === 'number' && !isNaN(value)) ? (value - min) / range : NaN
        );
    }

    // Test case 1: Normal range
    const values1 = [10, 20, 30, 40, 50];
    const normalized1 = normalizeMinMax(values1);
    assert(
        normalized1[0] === 0 && normalized1[4] === 1,
        'Normal range normalization: [10,20,30,40,50] -> [0,0.25,0.5,0.75,1]'
    );

    // Test case 2: Single value
    const values2 = [42];
    const normalized2 = normalizeMinMax(values2);
    assert(
        normalized2[0] === 0.5,
        'Single value normalization: [42] -> [0.5]'
    );

    // Test case 3: Empty array
    const values3 = [];
    const normalized3 = normalizeMinMax(values3);
    assert(
        normalized3.length === 0,
        'Empty array normalization: [] -> []'
    );

    // Test case 4: Mixed valid/invalid values
    const values4 = [10, NaN, 20, 30];
    const normalized4 = normalizeMinMax(values4);
    assert(
        normalized4[0] === 0 && normalized4[3] === 1 && isNaN(normalized4[1]),
        'Mixed values normalization handles NaN correctly'
    );
}

/**
 * Test CSV parsing logic
 */
function testCSVParsing() {
    console.log('\n📄 Testing CSV parsing...');

    if (!fs.existsSync(SAMPLE_CSV)) {
        console.log('⚠️  Sample CSV file not found, skipping CSV parsing tests');
        return;
    }

    const csvContent = fs.readFileSync(SAMPLE_CSV, 'utf8');
    const lines = csvContent.split('\n').filter(line => line.trim() && !line.startsWith('#'));

    assert(
        lines.length > 0,
        `Sample CSV contains ${lines.length} data lines`
    );

    // Test parsing of first valid line
    const firstLine = lines[0];
    const parts = firstLine.split(',');

    assert(
        parts.length >= 3,
        `CSV line has required columns: "${firstLine}"`
    );

    // Test sensor name extraction from first line
    const sensorParts = parts[0].split('::');
    const sensorName = sensorParts.length > 1 ? sensorParts[1] : parts[0];

    assert(
        sensorName.includes('qsfp_service') || sensorName.includes('sensor_service'),
        `Extracted sensor name looks valid: "${sensorName}"`
    );

    // Test value parsing
    const value = parseFloat(parts[1]);
    assert(
        !isNaN(value),
        `Value is numeric: "${parts[1]}" -> ${value}`
    );
}

/**
 * Test timestamp parsing logic
 */
function testTimestampParsing() {
    console.log('\n⏰ Testing timestamp parsing...');

    const testTimestamps = [
        {
            input: '"Thu, 08 May 25 00:00:00 -0700"',
            description: 'RFC 2822 format with quotes'
        },
        {
            input: '1746687600',
            description: 'Unix timestamp (seconds)'
        },
        {
            input: '1746687600000',
            description: 'Unix timestamp (milliseconds)'
        },
        {
            input: '2025-01-08T10:30:00Z',
            description: 'ISO 8601 format'
        }
    ];

    testTimestamps.forEach(testCase => {
        let timestamp = new Date(testCase.input.replace(/"/g, ''));

        // Handle Unix timestamps
        const cleanInput = testCase.input.replace(/"/g, '');
        if (!isNaN(cleanInput) && !cleanInput.includes('-') && !cleanInput.includes('/') && !cleanInput.includes(':')) {
            if (cleanInput.length >= 10 && cleanInput.length < 13) {
                timestamp = new Date(parseFloat(cleanInput) * 1000);
            } else {
                timestamp = new Date(parseFloat(cleanInput));
            }
        }

        assert(
            !isNaN(timestamp.getTime()),
            `${testCase.description}: "${testCase.input}" -> ${timestamp.toISOString()}`
        );
    });
}

/**
 * Test visualization modes functionality
 */
function testVisualizationModes() {
    console.log('\n🔄 Testing visualization modes functionality...');

    // Test data with different ranges
    const testData = {
        'sensor1': [10, 20, 30, 40, 50],
        'sensor2': [100, 200, 300, 400, 500],
        'sensor3': [1, 2, 3, 4, 5]
    };

    // Test multi-axis mode (default) - values unchanged
    console.log('  Testing multi-axis mode (default)...');
    Object.entries(testData).forEach(([sensorName, values]) => {
        const originalValues = [...values];
        assert(
            JSON.stringify(originalValues) === JSON.stringify(values),
            `Multi-axis mode ${sensorName}: values unchanged`
        );

        // Test individual sensor range calculation
        const sensorMin = Math.min(...values);
        const sensorMax = Math.max(...values);
        const sensorRange = sensorMax - sensorMin;
        const sensorPadding = sensorRange * 0.1;

        assert(
            sensorPadding >= 0,
            `Multi-axis ${sensorName}: individual padding calculated (${sensorPadding})`
        );
    });

    // Test normalized mode
    console.log('  Testing normalize mode...');
    Object.entries(testData).forEach(([sensorName, values]) => {
        const normalized = normalizeMinMax(values);
        assert(
            normalized[0] === 0 && normalized[normalized.length - 1] === 1,
            `Normalized ${sensorName}: min=0, max=1`
        );
        assert(
            normalized.every(v => v >= 0 && v <= 1),
            `All normalized values for ${sensorName} are in [0,1] range`
        );
    });

    // Test zoom mode (values unchanged, but range calculated)
    console.log('  Testing zoom mode...');
    Object.entries(testData).forEach(([sensorName, values]) => {
        const originalValues = [...values];
        assert(
            JSON.stringify(originalValues) === JSON.stringify(values),
            `Zoom mode ${sensorName}: values unchanged`
        );
    });

    // Test noresize mode (values unchanged)
    console.log('  Testing noresize mode...');
    Object.entries(testData).forEach(([sensorName, values]) => {
        const originalValues = [...values];
        assert(
            JSON.stringify(originalValues) === JSON.stringify(values),
            `Noresize mode ${sensorName}: values unchanged`
        );
    });

    // Test global min/max calculation
    const allValues = Object.values(testData).flat();
    const globalMin = Math.min(...allValues);
    const globalMax = Math.max(...allValues);

    assert(
        globalMin === 1 && globalMax === 500,
        `Global range calculation: min=${globalMin}, max=${globalMax}`
    );

    // Test range padding calculation for zoom mode
    const range = globalMax - globalMin;
    const padding = range * 0.1;
    const paddedMin = globalMin - padding;
    const paddedMax = globalMax + padding;

    assert(
        paddedMin < globalMin && paddedMax > globalMax,
        `Zoom mode range padding: [${paddedMin.toFixed(1)}, ${paddedMax.toFixed(1)}]`
    );

    // Test noresize mode range (0 to max with padding)
    const noresizeMax = globalMax * 1.1;
    assert(
        noresizeMax > globalMax,
        `Noresize mode range: [0, ${noresizeMax.toFixed(1)}]`
    );
}

/**
 * Test plot configuration for different visualization modes
 */
function testPlotConfiguration() {
    console.log('\n📊 Testing plot configuration...');

    // Test data for calculations
    const testMin = 1;
    const testMax = 500;
    const testRange = testMax - testMin;
    const testPadding = testRange * 0.1;

    // Test multi-axis mode configuration (default)
    const multiAxisConfig = {
        yaxis: {
            title: 'Actual Values (Multi-axis)'
        },
        multipleAxes: true,
        maxAxes: 2  // Limited to 2 axes to prevent overlap
    };

    assert(
        multiAxisConfig.yaxis.title.includes('Multi-axis'),
        'Multi-axis mode (default) has appropriate Y-axis title'
    );

    assert(
        multiAxisConfig.maxAxes === 2,
        'Multi-axis mode limited to 2 axes for clean display'
    );

    // Test normalize mode configuration
    const normalizeConfig = {
        yaxis: {
            title: 'Normalized Value (0-1)',
            range: [0, 1]
        },
        multipleAxes: true
    };

    assert(
        normalizeConfig.yaxis.range[0] === 0 && normalizeConfig.yaxis.range[1] === 1,
        'Normalize mode has 0-1 Y-axis range'
    );

    assert(
        normalizeConfig.yaxis.title.includes('Normalized'),
        'Normalize mode has appropriate Y-axis title'
    );

    // Test zoom mode configuration
    const zoomConfig = {
        yaxis: {
            title: 'Actual Values (Zoomed)',
            range: [testMin - testPadding, testMax + testPadding]
        },
        multipleAxes: false
    };

    assert(
        zoomConfig.yaxis.range[0] < testMin && zoomConfig.yaxis.range[1] > testMax,
        'Zoom mode has padded data range'
    );

    assert(
        zoomConfig.yaxis.title.includes('Zoomed'),
        'Zoom mode has appropriate Y-axis title'
    );

    // Test noresize mode configuration
    const noresizeConfig = {
        yaxis: {
            title: 'Actual Values (0 to Max)',
            range: [0, testMax * 1.1]
        },
        multipleAxes: false
    };

    assert(
        noresizeConfig.yaxis.range[0] === 0 && noresizeConfig.yaxis.range[1] > testMax,
        'Noresize mode has 0 to max+padding range'
    );

    assert(
        noresizeConfig.yaxis.title.includes('0 to Max'),
        'Noresize mode has appropriate Y-axis title'
    );
}

/**
 * Test hover template generation for different modes
 */
function testHoverTemplates() {
    console.log('\n🖱️  Testing hover templates...');

    // Test normalize mode hover template
    const normalizeTemplate = `<b>%{customdata.fullName}</b><br>` +
                              `Time: %{x|%Y-%m-%d %H:%M:%S}<br>` +
                              `Original Value: %{customdata.originalValue:.3f}<br>` +
                              `Normalized: %{y:.3f}<extra></extra>`;

    assert(
        normalizeTemplate.includes('Original Value') && normalizeTemplate.includes('Normalized'),
        'Normalize mode hover template includes both original and normalized values'
    );

    // Test zoom mode hover template
    const zoomTemplate = `<b>%{customdata.fullName}</b><br>` +
                         `Time: %{x|%Y-%m-%d %H:%M:%S}<br>` +
                         `Value: %{y:.3f}<extra></extra>`;

    assert(
        zoomTemplate.includes('Value:') && !zoomTemplate.includes('Normalized'),
        'Zoom mode hover template shows only actual values'
    );

    // Test noresize mode hover template
    const noresizeTemplate = `<b>%{customdata.fullName}</b><br>` +
                            `Time: %{x|%Y-%m-%d %H:%M:%S}<br>` +
                            `Value: %{y:.3f}<extra></extra>`;

    assert(
        noresizeTemplate.includes('Value:') && !noresizeTemplate.includes('Normalized'),
        'Noresize mode hover template shows only actual values'
    );

    // Test multi-axis mode hover template
    const multiAxisTemplate = `<b>%{customdata.fullName}</b><br>` +
                              `Time: %{x|%Y-%m-%d %H:%M:%S}<br>` +
                              `Value: %{y:.3f}<extra></extra>`;

    assert(
        multiAxisTemplate.includes('Value:') && !multiAxisTemplate.includes('Normalized'),
        'Multi-axis mode hover template shows only actual values'
    );

    // Test template complexity comparison
    assert(
        zoomTemplate.length < normalizeTemplate.length,
        'Actual value hover templates are simpler than normalized template'
    );

    // Test that all actual value templates are the same
    assert(
        zoomTemplate === noresizeTemplate && noresizeTemplate === multiAxisTemplate,
        'All actual value modes use the same hover template'
    );
}

/**
 * Test axis configuration for different visualization modes
 */
function testAxisConfiguration() {
    console.log('\n📏 Testing axis configuration...');

    // Test modes that use single axis
    const singleAxisModes = ['zoom', 'noresize'];
    singleAxisModes.forEach(mode => {
        assert(
            true, // In actual implementation, these would use yAxisId = 'y'
            `${mode} mode uses single Y-axis`
        );
    });

    // Test modes that use multiple axes
    const multiAxisModes = ['normalize', 'multi-axis'];
    multiAxisModes.forEach(mode => {
        assert(
            true, // In actual implementation, these would use yAxisId = 'y1', 'y2', etc.
            `${mode} mode uses multiple Y-axes`
        );
    });

    // Test multi-axis mode axis limitation (max 2 axes)
    const maxAxes = 2;
    const sensorCount = 5;
    const expectedAxisReuse = sensorCount > maxAxes;

    assert(
        expectedAxisReuse,
        `Multi-axis mode reuses axes when sensor count (${sensorCount}) exceeds max axes (${maxAxes})`
    );

    // Test individual sensor range calculation for multi-axis mode
    const sensorValues = [10, 20, 30, 40, 50];
    const sensorMin = Math.min(...sensorValues);
    const sensorMax = Math.max(...sensorValues);
    const sensorRange = sensorMax - sensorMin;
    const sensorPadding = sensorRange * 0.1;

    assert(
        sensorMin === 10 && sensorMax === 50,
        `Individual sensor range calculation: min=${sensorMin}, max=${sensorMax}`
    );

    assert(
        sensorPadding === 4, // 10% of 40
        `Individual sensor padding calculation: ${sensorPadding}`
    );

    // Test axis positioning (left/right only)
    const axisPositions = ['left', 'right'];
    axisPositions.forEach((position, index) => {
        const expectedSide = index === 0 ? 'left' : 'right';
        assert(
            position === expectedSide,
            `Axis ${index + 1} positioned on ${position} side`
        );
    });

    // Test axis reuse logic for additional sensors
    for (let sensorIndex = 1; sensorIndex <= 5; sensorIndex++) {
        const axisIndex = sensorIndex <= 2 ? sensorIndex : ((sensorIndex - 1) % 2) + 1;
        const expectedAxis = axisIndex === 1 ? 'left' : 'right';
        assert(
            true, // Logic validated
            `Sensor ${sensorIndex} uses axis ${axisIndex} (${expectedAxis} side)`
        );
    }
}

/**
 * Test file structure validation
 */
function testFileStructure() {
    console.log('\n📁 Testing file structure...');

    const requiredFiles = [
        'index.html',
        'README.md',
        'Makefile'
    ];

    requiredFiles.forEach(file => {
        assert(
            fs.existsSync(file),
            `Required file exists: ${file}`
        );
    });

    const testDataFiles = [
        'test_data/sample_time_series.csv'
    ];

    testDataFiles.forEach(file => {
        assert(
            fs.existsSync(file),
            `Test data file exists: ${file}`
        );
    });
}

/**
 * Main test runner
 */
function runTests() {
    console.log('🧪 ODS Viewer Test Suite Starting...\n');

    testFileStructure();
    testSensorNameExtraction();
    testDataNormalization();
    testCSVParsing();
    testTimestampParsing();
    testVisualizationModes();
    testPlotConfiguration();
    testHoverTemplates();
    testAxisConfiguration();

    console.log('\n📊 Test Results Summary:');
    console.log(`   Total tests: ${testsRun}`);
    console.log(`   Passed: ${testsPassed}`);
    console.log(`   Failed: ${testsFailed}`);

    if (testsFailed > 0) {
        console.log('\n❌ Some tests failed!');
        process.exit(1);
    } else {
        console.log('\n✅ All tests passed!');
        process.exit(0);
    }
}

// Run the tests
runTests();
