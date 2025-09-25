// Test the regex patterns from the config file
const testData = [
    'fdsw035.n001.c081.nao5::qsfp_service.qsfp.interface.fab1/1/1.temp,56,"Thu, 08 May 25 00:00:00 -0700",1746687600',
    'fdsw035.n001.c081.nao5::qsfp_service.qsfp.interface.fab1/10/1.vcc.mv,3299.33,"Thu, 08 May 25 00:00:00 -0700",1746687600'
];

const patterns = {
    temperature: '.*::qsfp_service\\.qsfp\\.interface\\.(fab1|eth1)\\/(\\d+)\\/\\d+\\.temp',
    voltage: '.*::qsfp_service\\.qsfp\\.interface\\.(fab1|eth1)\\/(\\d+)\\/\\d+\\.vcc\\.mv'
};

console.log('Testing regex patterns:');
console.log('');

Object.entries(patterns).forEach(([dataType, pattern]) => {
    console.log(`=== ${dataType.toUpperCase()} PATTERN ===`);
    console.log(`Pattern: ${pattern}`);

    const regex = new RegExp(pattern);

    testData.forEach((line, index) => {
        const metric = line.split(',')[0];
        const match = metric.match(regex);

        console.log(`Test ${index + 1}: ${metric}`);
        console.log(`Match: ${match ? `YES - Port ${match[2]}` : 'NO'}`);
        console.log('');
    });

    console.log('');
});
