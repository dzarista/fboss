This is a utility for upgrading PSU firmware.

The arguments required are the PSU number, a PSU firmware file, and the vendor name.

A couple assumptions are currently made in the code:

  The PSU files storing the power status and present status are in:

  Viper: "/run/devmap/fpgas/MERU800BIA_SMB_FPGA"
         The file name for present status is psu#_present
         The file names for power status are psu#_in_ok / psu#_out_ok
         
  Whistler: "/run/devmap/fpgas/MERU800FBA_SMG_FPGA0"
           The file name for present status is psu#_prsnt
           The file names for power status are psu#_in_ok / psu#_out_ok
           

  The PSU symlink entries are stored in /run/devmap/sensors/PSU#_PMBUS

  The PSU PMBus device address is 0x58

  