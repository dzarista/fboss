This is a utility for upgrading PSU firmware.

The arguments required are the PSU number and the PSU firmware file. The script checks to make sure that the models match.

A couple assumptions are currently made in the code:

  The PSU files storing the power status and present status are in:

  Viper: "/run/devmap/fpgas/MERU800BIA_SMB_FPGA"
  Whistler: "/run/devmap/fpgas/MERU800FBA_SMG_FPGA0"
  
  The file name for present status is psu#_present
  The file name for input/output status is psu#_input_ok, psu#_output_ok           

  The PSU symlink entries are stored in /run/devmap/sensors/PSU#_PMBUS

  The PSU PMBus device address is 0x58
