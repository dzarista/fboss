# Meru800bfa Firmware Programmables for P1 HW

This directory contains the firmware programmable binaries for the
Meru800bfa platform. The table below shows the programmables:

| Programmable Name                | Description          |
|----------------------------------|----------------------|
| Aboot.rom                        | Bootloader for x86   |
| meru-scm-cpld-p1-only.astp       | SCM CPLD JTAG image  |
| meru800bfa-smb-cpld-p1-only.astp | SMB CPLD JTAG image  |
| meru800bfa-smb-fpga0.abit        | SMB FPGA0 SPI image  |
| meru800bfa-smb-fpga1.abit        | SMB FPGA1 SPI image  |
| meru800bfa-smb-fpga2.abit        | SMB FPGA2 SPI image  |
| meru800bfa-smb-fpga3.abit        | SMB FPGA3 SPI image  |
| meru800bfa-fan-cpld.astp         | Fan CPLDs JTAG image |

The tables below show the released version history for each
programmable. The most recent version can be found in this
directory.

## Aboot.rom

| Version                                    | Changelog                                                                          |
|--------------------------------------------|------------------------------------------------------------------------------------|
| Aboot-norcal13-13.1.0-32240247             | Initial Aboot image.                                                               |
| Aboot-norcal13-13.1.0-lcc-32m-ENG-33260098 | Supports DMI_BOARD_NAME and DMI_BOARD_VERSION.                                     |
| Aboot-norcal13-13.1.0-lcc-64m-ENG-33522315 | Supports 64MB Aboot SPI flash (compatibility ends with initial standalone boards). |
| Aboot-norcal13-13.1.0-lcc-64m-ENG-33784852 | Vendor-specific information removed from DHCP request for PXE boot.                |
| Aboot-norcal13-13.1.0-lcc-64m-ENG-34439569 | Adds support for i2c-tools. Add DNS support for PXE boot.                          |
| Aboot-norcal13-13.1.0-lcc-64m-ENG-35681420 | Presents product name in uppercase in dmidecode output.                            |
| Aboot-norcal13-13.1.0-lcc-64m-ENG-36730386 | BMC KCS interface resources are exposed in SMBIOS when the system is in BMC-mode.  |
| Aboot-norcal13-13.1.1-lcc-64m-37911221     | Adds support for BTRFS and non-EOS partition labels.                               |
| Aboot-norcal13-13.1.2-lcc-64m-38688619     | Adds support for MERU800BIAB systems.                                              |

## meru-scm-cpld-p1-only.astp

| Version | Changelog                                                                                                                |
|---------|--------------------------------------------------------------------------------------------------------------------------|
| 0.15    | Initial SCM CPLD image (no PCIe support).                                                                                |
| 0.19    | Supports PCIe interface.                                                                                                 |
| 0.22    | Allows wedge_power.sh reset -s to powercycle entire system instead of just SCM.                                          |
| 0.23    | No software-visible change vs 0.22.                                                                                      |
| 1.1     | No software-visible change vs 0.23.                                                                                      |
| 1.15    | Fixes 32-byte SMBus block read needed for UCD90320 driver support, increases MDIO drive strength for improved stability. |

## meru800bfa-smb-cpld-p1-only.astp

| Version | Changelog                                                                                                                                         |
|---------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| 1.7     | Initial SMB CPLD image.                                                                                                                           |
| 1.9     | Adds support for resets from SMB FPGA0. Adds support for PSU presence status in SMB FPGA0. Changes Ramon3 PCIe strapping to Gen3 instead of Gen4. |
| 1.11    | Resolves RC32312A clock issue preventing config from loading at powerup.                                                                          |
| 1.13    | Changes Ramon3 strapping to QSPI single lane, enable PCIe Gen4, MHOST_0_BOOT_DEV=0 and MHOST_1_BOOT_DEV=0.                                        |

## meru800bfa-smb-fpga0.abit/meru800bfa-smb-fpga0-stripped.abit

| Version  | Changelog                           |
|----------|-------------------------------------|
| 1.14     | Initial SMB FPGA0 image.            |
| 1.15     | No software-visible change vs 1.14. |
| 1.19     | No software-visible change vs 1.15. |

## meru800bfa-smb-fpga1.abit/meru800bfa-smb-fpga1-stripped.abit

| Version  | Changelog                           |
|----------|-------------------------------------|
| 1.14     | Initial SMB FPGA1 image.            |
| 1.15     | No software-visible change vs 1.14. |
| 1.19     | No software-visible change vs 1.15. |

## meru800bfa-smb-fpga2.abit/meru800bfa-smb-fpga2-stripped.abit

| Version  | Changelog                                                       |
|----------|-----------------------------------------------------------------|
| 1.15     | Initial SMB FPGA2 image.                                        |
| 1.25     | Update R3 voltage control to improve link quality for R0 lanes. |
| 1.26     | No software-visible change vs 1.25.                             |

## meru800bfa-smb-fpga3.abit/meru800bfa-smb-fpga3-stripped.abit

| Version  | Changelog                                                       |
|----------|-----------------------------------------------------------------|
| 1.13     | Initial SMB FPGA3 image.                                        |
| 1.22     | Update R3 voltage control to improve link quality for R0 lanes. |
| 1.23     | No software-visible change vs 1.22.                             |


## meru800bfa-fan-cpld.astp

| Version | Changelog                                                               |
|---------|-------------------------------------------------------------------------|
| 1.2     | Initial FAN CPLD image.                                                 |
| 1.4     | FAN_CHANGE registers now clear on per-bit basis.                        |
| 1.7     | Adds fan ID register 0x4. Fixes Amber LED on P2.                        |
| 1.9     | Changed FAN LED to be OFF when fan is not installed (instead of Amber). |

## bcm53134image-p1.bin
| Version | Changelog                                        |
|---------|--------------------------------------------------|
| 0.6     | Initial Bcm53134 P1 image.                       |
