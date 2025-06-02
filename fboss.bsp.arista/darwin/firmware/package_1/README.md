# Firmware Package #1

| Programmable Name                                                 | Description                               |
|-------------------------------------------------------------------|-------------------------------------------|
| P_darwin_F_BIOS_V_Aboot-norcal7-7.5.3-cb411-rook-2x4-39223411.rom | Bootloader for x86                        |
| P_darwin_F_CPU_CPLD_V_22.37.astp                                  | CPU CPLD JTAG image                       |
| P_darwin_F_FAN_CPLD_V_4.0.adata                                   | FAN CPLD image                            |
| P_darwin_F_SC_CPLD_V_13.7.astp                                    | SC CPLD JTAG image                        |
| P_darwin_F_SC_SAT_CPLD_V_5.0.astp                                 | SC Satellite CPLD image                   |
| P_darwin_F_SC_SCD_V_14.6.abit                                     | SC SCD FPGA image (SPI w/header stripped) |
| darwin_ssd-fw_vU0316A_AF240GSTIA-AW1.bin                          | SSD firmware (ATP)                        |
| darwin_ssd-fw_v0710-000_VSFDM4CC240G-V11.bin                      | SSD firmware (Virtium)                    |


# Changelogs

The tables below show the released version history for each
programmable. The most recent version can be found in this
directory.

## Changes From Last Package
| Programmable Name                                                 | Description                                         |
|-------------------------------------------------------------------|-----------------------------------------------------|
| P_darwin_F_BIOS_V_Aboot-norcal7-7.5.3-cb411-rook-2x4-39223411.rom | Contains support for the UAPI boot loader spec (BLS)|

## BIOS

| Version        | Changelog                                                                                                                                                                                                    |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 7.2.0          | Initial release.                                                                                                                                                                                             |
| 7.5.0-24426054 | First release of 7.5.0.                                                                                                                                                                                      |
| 7.5.0-24588359 | Contains support for bootloader configuration.                                                                                                                                                               |
| 7.5.0-24671212 | Contains logic to automatically configure boot methods if none exist.                                                                                                                                        |
| 7.5.0-24725255 | Contains support for dmidecode/SMBIOS.                                                                                                                                                                       |
| 7.5.0-24831750 | Contains support for Aboot upgrade from removable USB device.                                                                                                                                                |
| 7.5.0-24903631 | Contains support for REBOOT boot method, watchdog set for IPV6_PXE and LOCAL boot methods. Fixes bug with URL parsing. Fixes bug where management MAC is reloaded into the NIC mailbox after pxeboot script. |
| 7.5.0-24967434 | Fixes bug where backslash in grub kernel argument is not properly unescaped.                                                                                                                                 |
| 7.5.0-25889663 | Contains support for bringing TH3 out of reset prior to local boot kexec. Fixes bug where bootfile-param handling was not compliant with RFC 5970.                                                           |
| 7.5.0-26125933 | Contains support for pre-allocating memory for PCI root port. Changes product name shown in dmidecode system to "Darwin". The definition of the normal SPI section is changed.                               |
| 7.5.1-26527831 | Fixes issue with AER uncorrected errors.                                                                                                                                                                     |
| 7.5.2-32180635 | Fixes issue with LOCAL boot parser preventing Centos 9 from booting. Fixes issue with REBOOT boot method that causes BMC to power cycle.                                                                     |
| 7.5.3-37934176 | Experimental bootloader with support for standard uapi booting. The watchdog is not enabled with this bootloader.                                                                                            |
| 7.5.3-38475208 | Bootloader with watchdog disabled by default and DARWIN48V in dmidecode board name.                                                                                            |
| 7.5.3-39223411 | Contains support for the UAPI boot loader spec (BLS)                                                                                                                                                         |

## CPU CPLD

| Version | Changelog                                                                                                                                                                                |
|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 19.0    | Initial version.                                                                                                                                                                         |
| 20.0    | Fixes SMBus block read mechanism for 32-byte reads.                                                                                                                                      |
| 22.33   | Adds support for resetting the x86 CPU via PWR_BTN signal. Changes response to CPU CAT_ERR from system powercycle to PWR_BTN CPU reset. Minimum version required for x86 reset from BMC. |
| 22.37   | Fixes dud reset issue.                                                                                                                                                                   |

## FAN CPLD

| Version | Changelog        |
|---------|------------------|
| 4.0     | Initial version. |

## Switchcard CPLD

| Version | Changelog                                                                                                            |
|---------|----------------------------------------------------------------------------------------------------------------------|
| 13.2    | Initial version.                                                                                                     |
| 13.3    | Changes hardware overheat action to be reboot instead of suicide.                                                    |
| 13.4    | Adds support for system powercycle from FanSpinnerMon2 BMC. Minimum version required for system powercycle from BMC. |
| 13.7    | Adds support for CPU reset via BMC_SYS_PWR_CYC_1 GPIO from the BMC. Minimum version required for x86 reset from BMC. |

## SWITCH CARD SATELITE CPLD

| Version | Changelog        |
|---------|------------------|
| 5.0     | Initial version. |

## SWITCH CARD SCD

| Version | Changelog                                                                                                                                                                                             |
|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 14.1    | Initial version.                                                                                                                                                                                      |
| 14.2    | Adds watchdog2 (0x0304) and watchdog2 debug (0x0308) registers for second-granularity watchdog (used instead of watchdog register by default).                                                        |
| 14.4    | Fixes SMBus4 response fifo race condition causing transaction ID mismatch.                                                                                                                            |
| 14.5    | Changes PCIE subsystem ID to 0x2. Adds .abit file which can be used to upgrade the switch card SCD SPI flash via the CPU PCIe. Minimum version required for FBOSS scd driver and spiReprogram update. |
| 14.6    | Increases transaction delay for transceivers. No expected issues for FBOSS with previous images.                                                                                                      |

## SSD FW (ATP)

| Version | Changelog        |
|---------|------------------|
| U0316A  | Initial version. |

## SSD FW (Virtium)

| Version  | Changelog        |
|----------|------------------|
| 0710-000 | Initial version. |
