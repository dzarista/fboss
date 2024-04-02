# These utilities are meant to help collect some raw fan data for analysis and use for FBOSS tuning

# Usage
Set up a unit (e.g) Viper with the right port configuration and optics modules
Make sure PSU count matches the customer configuration
Put as many snakes as possible, and a few MPC ports
Sanitize the dut first. Make sure the fdl mix/max RPM is accurate
CollectFanSweepData.py can be modified with a new class added to support running the data collection


e.g: Viper
python3 CollectFanSweepData.py -d vpr114 --soak-time 60 --rpms 100 90 80 70 60 50 40 30 20


# NOTE
Make sure to have the dut grabbed throughout the duration of the test. The test does NOT update grab duration.