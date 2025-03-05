# These utilities are meant to help collect some raw fan data for analysis and use for FBOSS tuning

# Usage
Set up a unit (e.g) Viper with the right port configuration and optics modules
Make sure PSU count matches the customer configuration
Put as many snakes as possible, and a few MPC ports
Sanitize the dut first.
CollectFanSweepData.py can be modified with a new class added to support running the data collection


e.g: Viper
./CollectFanSweepData.py -d vpr114 --soak-time 60 --rpms 100 90 80 70 60 50 40 30 20


e.g: Whistler System Zone
./CollectFanSweepData.py --soak-time 10 -d wlr211 -z system --rpms 100 80 79 78 77 76 75 74 73 72 71 70 69 68 67 66 65 64 63 62 61 60 59 58 57 56 55 54 53 52 51 50 49 48 47 46 45 44 43 42 41 40 39 38 37 36 35 34 33 32 31 30

# NOTE
Make sure to have the dut grabbed throughout the duration of the test. The test does NOT update the grab duration.