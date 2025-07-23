#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Load configuration
const config = JSON.parse(fs.readFileSync('./data_extraction_config.json', 'utf8'));
const DATA_TYPES = config.dataTypes;

// Test data - sample lines from the CSV
const testLines = [
    'host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/1/1.temp,56,"Thu, 08 May 25 00:00:00 -0700",1746687600',
    'host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/1/1.temp,56,"Thu, 08 May 25 01:00:00 -0700",1746691200',
    'host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/1/1.temp,56,"Thu, 08 May 25 02:00:00 -0700",1746694800',
    'host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/2/1.temp,45,"Thu, 08 May 25 00:00:00 -0700",1746687600',
    'host123.n123.c123.abc1::qsfp_service.qsfp.interface.fab1/1/1.vcc.mv,3299.33,"Thu, 08 May 25 00:00:00 -0700",1746687600'
];

function extractTimeSeriesData(content, dataType = 'temperature') {
    console.log(`\n=== TESTING ${dataType.toUpperCase()} EXTRACTION ===`);

    const transceiverData = {}; // portNumber -> { timestamp -> dataValue }
    const fanData = {}; // fanNumber -> { timestamp -> percentage }
    const timestampSet = new Set();

    // Get data type configuration
    const dataTypeConfig = DATA_TYPES[dataType];
    if (!dataTypeConfig) {
        throw new Error(`Unknown data type: ${dataType}`);
    }

    const timeSeriesConfig = dataTypeConfig.timeSeries;
    console.log(`Pattern: ${timeSeriesConfig.metricPattern}`);

    const lines = content.split('\n');
    let processedLines = 0;
    let skippedLines = 0;
    let dataTypeMatches = 0;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) {
            skippedLines++;
            continue;
        }

        // Parse CSV line: metric,value,timestamp_string,timestamp_unix
        const parts = [];
        let current = '';
        let inQuotes = false;

        for (let j = 0; j < line.length; j++) {
            const char = line[j];
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

        if (parts.length < 4) {
            skippedLines++;
            continue;
        }

        const metric = parts[0].trim();
        let value = parseFloat(parts[1]);
        const timestampUnix = parseInt(parts[3].trim());

        if (isNaN(value) || isNaN(timestampUnix) || timestampUnix <= 0) {
            skippedLines++;
            continue;
        }

        // Check if this line contains the data type we're looking for
        if (metric.includes(timeSeriesConfig.metricSuffix)) {
            dataTypeMatches++;
        }

        // Extract transceiver data using configurable pattern
        const regex = new RegExp(timeSeriesConfig.metricPattern);
        const dataMatch = metric.match(regex);

        if (dataMatch) {
            const portNumber = parseInt(dataMatch[2]);

            // Apply conversion if specified (e.g., millivolts to volts)
            if (timeSeriesConfig.conversion) {
                value = value * timeSeriesConfig.conversion.factor;
            }

            // Validate data value
            const isValid = value >= timeSeriesConfig.validationMin &&
                value <= timeSeriesConfig.validationMax;

            if (isValid) {
                if (!transceiverData[portNumber]) {
                    transceiverData[portNumber] = {};
                }

                // Convert timestamp to string for consistent object key handling
                const timestampKey = timestampUnix.toString();
                transceiverData[portNumber][timestampKey] = value;
                timestampSet.add(timestampUnix);
                processedLines++;

                // Debug storage for port 1
                if (portNumber === 1) {
                    if (processedLines <= 3) {
                        console.log(`✅ STORED: port ${portNumber}, timestamp "${timestampKey}", value ${value} (type: ${typeof value})`);
                        console.log(`   transceiverData[${portNumber}]["${timestampKey}"] = ${transceiverData[portNumber][timestampKey]}`);
                    }

                    // Check for zero values being stored
                    if (value === 0) {
                        console.log(`⚠️  ZERO VALUE: port ${portNumber}, timestamp "${timestampKey}", raw parts:`, parts);
                        console.log(`   Parsed value: ${value}, Original string: "${parts[1]}"`);
                    }

                    // Check for overwrites
                    if (transceiverData[portNumber][timestampKey] !== undefined && transceiverData[portNumber][timestampKey] !== value) {
                        console.log(`🔄 OVERWRITE: port ${portNumber}, timestamp "${timestampKey}"`);
                        console.log(`   Old value: ${transceiverData[portNumber][timestampKey]} → New value: ${value}`);
                    }
                }
            }
        }
    }

    // Convert timestamps to sorted array
    const timestamps = Array.from(timestampSet).sort((a, b) => a - b);

    console.log(`\n📊 EXTRACTION SUMMARY:`);
    console.log(`- Total lines processed: ${processedLines}`);
    console.log(`- Lines skipped: ${skippedLines}`);
    console.log(`- ${dataType} metrics found: ${dataTypeMatches}`);
    console.log(`- Unique timestamps: ${timestamps.length}`);
    console.log(`- Ports with ${dataType} data: ${Object.keys(transceiverData).length}`);

    // Debug final data state
    if (transceiverData[1]) {
        console.log(`\n🔍 FINAL DATA CHECK:`);
        console.log(`Port 1 data:`, transceiverData[1]);
        console.log(`Port 1 first value: ${Object.values(transceiverData[1])[0]}`);
        console.log(`Port 1 keys:`, Object.keys(transceiverData[1]));
        console.log(`Port 1 values:`, Object.values(transceiverData[1]));
    }

    return { transceiverData, fanData, timestamps };
}

// Test with actual large file
console.log('🧪 TESTING EXTRACTION LOGIC WITH LARGE FILE');
console.log('=============================================');

let testContent;
try {
    testContent = fs.readFileSync('./fdsw035.n001.c081.nao5-all-qsfp-data.csv', 'utf8');
    console.log(`Loaded file with ${testContent.split('\n').length} lines`);
} catch (error) {
    console.log('Large file not found, using sample data');
    testContent = testLines.join('\n');
    console.log('Test data:');
    testLines.forEach((line, i) => console.log(`${i + 1}: ${line}`));
}

// Test temperature extraction
const tempResult = extractTimeSeriesData(testContent, 'temperature');

console.log('\n🔍 RETURN VALUE CHECK:');
console.log('tempResult.transceiverData[1]:', tempResult.transceiverData[1]);
console.log('First value from return:', tempResult.transceiverData[1] ? Object.values(tempResult.transceiverData[1])[0] : 'undefined');

// Test voltage extraction
const voltResult = extractTimeSeriesData(testContent, 'voltage');

console.log('\n🔍 VOLTAGE RETURN VALUE CHECK:');
console.log('voltResult.transceiverData[1]:', voltResult.transceiverData[1]);
console.log('First value from return:', voltResult.transceiverData[1] ? Object.values(voltResult.transceiverData[1])[0] : 'undefined');
