#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Load configuration
const config = JSON.parse(fs.readFileSync('./data_extraction_config.json', 'utf8'));
const DATA_TYPES = config.dataTypes;

// Test utilities
function assert(condition, message) {
    if (!condition) {
        console.error(`❌ ASSERTION FAILED: ${message}`);
        process.exit(1);
    }
}

function assertApproxEqual(actual, expected, tolerance = 0.01, message = '') {
    const diff = Math.abs(actual - expected);
    if (diff > tolerance) {
        console.error(`❌ ASSERTION FAILED: ${message}`);
        console.error(`   Expected: ${expected}, Actual: ${actual}, Diff: ${diff}`);
        process.exit(1);
    }
}

// Import extraction function (simplified version for testing)
function extractTimeSeriesData(content, dataType = 'temperature') {
    const transceiverData = {};
    const fanData = {};
    const timestampSet = new Set();

    const dataTypeConfig = DATA_TYPES[dataType];
    if (!dataTypeConfig) {
        throw new Error(`Unknown data type: ${dataType}`);
    }

    const timeSeriesConfig = dataTypeConfig.timeSeries;
    const lines = content.split('\n');
    let processedLines = 0;

    for (const line of lines) {
        if (!line.trim() || line.startsWith('#')) continue;

        const parts = [];
        let current = '';
        let inQuotes = false;

        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                parts.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        parts.push(current.trim());

        if (parts.length < 4) continue;

        const metric = parts[0].trim();
        let value = parseFloat(parts[1]);
        const timestampUnix = parseInt(parts[3].trim());

        if (isNaN(value) || isNaN(timestampUnix) || timestampUnix <= 0) continue;

        // Extract transceiver data
        const regex = new RegExp(timeSeriesConfig.metricPattern);
        const dataMatch = metric.match(regex);

        if (dataMatch) {
            const portNumber = parseInt(dataMatch[2]);

            if (timeSeriesConfig.conversion) {
                value = value * timeSeriesConfig.conversion.factor;
            }

            const isValid = value >= timeSeriesConfig.validationMin &&
                value <= timeSeriesConfig.validationMax;

            if (isValid) {
                if (!transceiverData[portNumber]) {
                    transceiverData[portNumber] = {};
                }

                const timestampKey = timestampUnix.toString();
                transceiverData[portNumber][timestampKey] = value;
                timestampSet.add(timestampUnix);
                processedLines++;
            }
        }

        // Extract fan data
        const fanMatch = metric.match(/.*::sensor_service\.sensor_read\.FAN(\d+)_RPM\.value/);
        if (fanMatch) {
            const fanNumber = parseInt(fanMatch[1]);
            const maxRPM = 11200;
            const percentage = (value / maxRPM) * 100;

            if (!fanData[fanNumber]) {
                fanData[fanNumber] = {};
            }
            const timestampKey = timestampUnix.toString();
            fanData[fanNumber][timestampKey] = Math.min(100, Math.max(0, percentage));
            timestampSet.add(timestampUnix);
        }
    }

    const timestamps = Array.from(timestampSet).sort((a, b) => a - b);
    return { transceiverData, fanData, timestamps };
}

// Test cases
function runTests() {
    console.log('🧪 FBOSS HEATMAP TEST SUITE');
    console.log('============================\n');

    const testData = fs.readFileSync('./test_data/sample_time_series.csv', 'utf8');

    // Test 1: Temperature extraction
    console.log('📊 Test 1: Temperature Extraction');
    const tempResult = extractTimeSeriesData(testData, 'temperature');

    // Should extract temperature data for ports 1, 2, 10, 100, 128
    assert(Object.keys(tempResult.transceiverData).length === 5, 'Should extract 5 ports with temperature data');
    assert(tempResult.transceiverData[1], 'Port 1 should have temperature data');
    assert(tempResult.transceiverData[1]['1746687600'] === 56, 'Port 1 first timestamp should be 56°C');
    assert(tempResult.transceiverData[2]['1746687600'] === 45, 'Port 2 should be 45°C');
    assert(tempResult.transceiverData[100]['1746687600'] === 62, 'Port 100 should be 62°C');

    // Should ignore bad metrics (temp.high.sum.60, temp.low.sum.60)
    assert(tempResult.transceiverData[1]['1746687600'] !== 0, 'Port 1 should not be overwritten by bad metrics');

    // Should filter out invalid temperatures (port 3 with 200°C)
    assert(!tempResult.transceiverData[3], 'Port 3 with invalid temp should be filtered out');

    console.log('✅ Temperature extraction tests passed\n');

    // Test 2: Voltage extraction
    console.log('📊 Test 2: Voltage Extraction');
    const voltResult = extractTimeSeriesData(testData, 'voltage');

    // Should extract voltage data for ports 1, 2, 3, 10, 100 (1000mV is valid)
    assert(Object.keys(voltResult.transceiverData).length === 5, 'Should extract 5 ports with voltage data');
    assertApproxEqual(voltResult.transceiverData[1]['1746687600'], 3299.33, 0.01, 'Port 1 voltage should be 3299.33mV');
    assertApproxEqual(voltResult.transceiverData[2]['1746687600'], 3301.5, 0.01, 'Port 2 voltage should be 3301.5mV');
    assertApproxEqual(voltResult.transceiverData[3]['1746687600'], 1000, 0.01, 'Port 3 voltage should be 1000mV (valid)');

    console.log('✅ Voltage extraction tests passed\n');

    // Test 3: Fan data extraction
    console.log('📊 Test 3: Fan Data Extraction');

    assert(Object.keys(tempResult.fanData).length === 3, 'Should extract 3 fans');
    assert(tempResult.fanData[1], 'Fan 1 should have data');
    assert(tempResult.fanData[2], 'Fan 2 should have data');
    assert(tempResult.fanData[12], 'Fan 12 should have data');

    // Check fan percentage calculation (5600 RPM / 11200 max = 50%)
    assertApproxEqual(tempResult.fanData[1]['1746687600'], 50, 0.1, 'Fan 1 should be 50%');

    console.log('✅ Fan data extraction tests passed\n');

    // Test 4: Regex pattern specificity
    console.log('📊 Test 4: Regex Pattern Specificity');

    // Create test data with both good and bad metrics
    const regexTestData = `
host123::qsfp_service.qsfp.interface.fab1/1/1.temp,56,"Thu, 08 May 25 00:00:00 -0700",1746687600
host123::qsfp_service.qsfp.interface.fab1/1/1.temp.high.sum.60,0,"Thu, 08 May 25 00:00:00 -0700",1746687600
host123::qsfp_service.qsfp.interface.fab1/1/1.temp.low.sum.60,0,"Thu, 08 May 25 00:00:00 -0700",1746687600
    `.trim();

    const regexResult = extractTimeSeriesData(regexTestData, 'temperature');
    assert(regexResult.transceiverData[1]['1746687600'] === 56, 'Should match only exact .temp metrics, not .temp.* variants');

    console.log('✅ Regex pattern specificity tests passed\n');

    // Test 5: Multiple hostname formats
    console.log('📊 Test 5: Multiple Hostname Formats');

    const hostnameTestData = `
host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/1/1.temp,56,"Thu, 08 May 25 00:00:00 -0700",1746687600
rdsw025.u001.c086.ash6::qsfp_service.qsfp.interface.eth1/2/1.temp,48,"Thu, 08 May 25 00:00:00 -0700",1746687600
    `.trim();

    const hostnameResult = extractTimeSeriesData(hostnameTestData, 'temperature');
    assert(hostnameResult.transceiverData[1]['1746687600'] === 56, 'Should handle host123 hostname');
    assert(hostnameResult.transceiverData[2]['1746687600'] === 48, 'Should handle rdsw hostname');

    console.log('✅ Multiple hostname format tests passed\n');

    // Test 6: Data consistency and types
    console.log('📊 Test 6: Data Consistency and Types');

    assert(Array.isArray(tempResult.timestamps), 'Timestamps should be an array');
    assert(tempResult.timestamps.length > 0, 'Should have timestamps');
    assert(tempResult.timestamps.every(t => typeof t === 'number'), 'All timestamps should be numbers');
    assert(tempResult.timestamps[0] === 1746687600, 'First timestamp should be correct');

    // Check that all stored values are numbers
    Object.values(tempResult.transceiverData).forEach(portData => {
        Object.values(portData).forEach(value => {
            assert(typeof value === 'number', 'All temperature values should be numbers');
        });
    });

    console.log('✅ Data consistency tests passed\n');

    console.log('🎉 ALL TESTS PASSED!');
    console.log('====================');
    console.log(`✅ Temperature extraction: ${Object.keys(tempResult.transceiverData).length} ports`);
    console.log(`✅ Voltage extraction: ${Object.keys(voltResult.transceiverData).length} ports`);
    console.log(`✅ Fan extraction: ${Object.keys(tempResult.fanData).length} fans`);
    console.log(`✅ Timestamps: ${tempResult.timestamps.length} unique timestamps`);
    console.log(`✅ Regex patterns working correctly`);
    console.log(`✅ Data validation working correctly`);
}

// Run tests
if (require.main === module) {
    try {
        runTests();
        process.exit(0);
    } catch (error) {
        console.error('💥 TEST SUITE FAILED:', error.message);
        process.exit(1);
    }
}
