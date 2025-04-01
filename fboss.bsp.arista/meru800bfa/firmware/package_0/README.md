# Firmware Package #0

This directory contains the firmware programmable binaries for the
Meru800bfa platform. The table below shows the programmables:

| Programmable Name                                                       | Description          |
|-------------------------------------------------------------------------|----------------------|
| meru800bia-meru800bfa_bios_vAboot-norcal13-13.1.2-lcc-64m-38688619.rom  | Bootloader for x86   |
| meru800bia-meru800bfa_scm-cpld_v4.13.astp                               | SCM CPLD JTAG image  |
| meru800bfa_smb-cpld_v4.4.astp                                           | SMB CPLD JTAG image  |
| meru800bfa_smb-fpga0_v1.15.abit                                         | SMB FPGA0 SPI image  |
| meru800bfa_smb-fpga1_v1.15.abit                                         | SMB FPGA1 SPI image  |
| meru800bfa_smb-fpga2_v1.25.abit                                         | SMB FPGA2 SPI image  |
| meru800bfa_smb-fpga3_v1.22.abit                                         | SMB FPGA3 SPI image  |
| meru800bfa_fan-cpld_v1.7.astp                                           | Fan CPLDs JTAG image |
| meru800bfa_bcm53134image-p4_v1.2.bin                                    | Bcm53134 p4 image    |

# Changelogs

The tables below show the released version history for each
programmable. The most recent version can be found in this
directory.

## Changes From Last Package
N/A

## BIOS

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

## SCM CPLD

| Version | Changelog                                                          |
|---------|--------------------------------------------------------------------|
| 4.0     | Initial SCM CPLD image.                                            |
| 4.2     | Fixes 32-byte SMBus block read needed for UCD90320 driver support. |
| 4.13    | Increases MDIO drive strength for improved stability.              |

## SMB CPLD

| Version | Changelog                                                                                |
|---------|------------------------------------------------------------------------------------------|
| 4.1     | Initial P2 SMB CPLD image.                                                               |
| 4.3     | Change Ramon3 strapping for QSPI single lane, MHOST_0_BOOT_DEV=0 and MHOST_1_BOOT_DEV=0. |
| 4.4     | Adds push button holdtime of 5 seconds before triggering power cycle.                    |

## SMB FPGA0

| Version  | Changelog                           |
|----------|-------------------------------------|
| 1.14     | Initial SMB FPGA0 image.            |
| 1.15     | No software-visible change vs 1.14. |

## SMB FPGA1

| Version  | Changelog                           |
|----------|-------------------------------------|
| 1.14     | Initial SMB FPGA1 image.            |
| 1.15     | No software-visible change vs 1.14. |

## SMB FPGA2

| Version  | Changelog                           |
|----------|-------------------------------------|
| 1.15     | Initial SMB FPGA2 image.            |
| 1.25     | Improve link quality for R0 lanes.  |

## SMB FPGA3

| Version  | Changelog                           |
|----------|-------------------------------------|
| 1.13     | Initial SMB FPGA3 image.            |
| 1.22     | Improve link quality for R0 lanes.  |

## FAN CPLD

| Version | Changelog                                                               |
|---------|-------------------------------------------------------------------------|
| 1.2     | Initial FAN CPLD image.                                                 |
| 1.4     | FAN_CHANGE registers now clear on per-bit basis.                        |
| 1.7     | Adds fan ID register 0x4. Fixes Amber LED on P2.                        |

## BCM53134 IMAGE

| Version | Changelog                                        |
|---------|--------------------------------------------------|
| 1.1     | Initial Bcm53134 P4 image.                       |
| 1.2     | Fixes Whistler multicast forwarding issue.       |
