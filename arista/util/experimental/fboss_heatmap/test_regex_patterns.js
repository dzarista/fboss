#!/usr/bin/env node

// Test utility for regex patterns
const fs = require('fs');
const path = require('path');

// Load regex patterns
const regexConfig = JSON.parse(fs.readFileSync('regex_patterns.json', 'utf8'));

console.log('='.repeat(60));
console.log('REGEX PATTERN TESTING UTILITY');
console.log('='.repeat(60));
console.log('');

let totalTests = 0;
let passedTests = 0;

Object.entries(regexConfig.patterns).forEach(([patternName, config]) => {
    console.log(`Testing ${config.name} Pattern:`);
    console.log(`Pattern: ${config.pattern}`);
    console.log(`Description: ${config.description}`);
    console.log('');

    const regex = new RegExp(config.pattern);

    config.testCases.forEach((testCase, index) => {
        totalTests++;
        const match = testCase.input.match(regex);
        const actualMatch = !!match;
        const actualPort = match ? match[patternName === 'fan' ? 1 : 2] : null;

        const passed = actualMatch === testCase.shouldMatch &&
                      (!testCase.expectedPort || actualPort === testCase.expectedPort);

        if (passed) passedTests++;

        console.log(`  Test ${index + 1}: ${passed ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`    Input: ${testCase.input}`);
        console.log(`    Expected Match: ${testCase.shouldMatch}`);
        console.log(`    Actual Match: ${actualMatch}`);
        if (testCase.expectedPort) {
            console.log(`    Expected Port: ${testCase.expectedPort}`);
            console.log(`    Actual Port: ${actualPort}`);
        }
        console.log('');
    });

    console.log('-'.repeat(40));
    console.log('');
});

console.log('='.repeat(60));
console.log(`SUMMARY: ${passedTests}/${totalTests} tests passed`);
if (passedTests === totalTests) {
    console.log('🎉 All tests passed!');
} else {
    console.log('⚠️  Some tests failed. Check patterns above.');
}
console.log('='.repeat(60));
