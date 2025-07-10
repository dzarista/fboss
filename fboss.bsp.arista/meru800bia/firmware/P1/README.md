# Meru800bia Firmware Programmables for P1 HW

This directory contains the firmware programmable binaries for the
Meru800bia P1 platforms. The table below shows the programmables:

| Programmable Name                | Description         |
|----------------------------------|---------------------|
| Aboot.rom                        | Bootloader for x86  |
| meru-scm-cpld-p1-only.astp       | SCM CPLD JTAG image |
| meru800bia-smb-fpga-p1-only.abit | SMB FPGA SPI image  |
| meru800bia-fan-cpld.astp         | Fan CPLD JTAG image |

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

## meru800bia-smb-fpga-p1-only.abit/meru800bia-smb-fpga-p1-only-stripped.abit

| Version | Changelog                                     |
|---------|-----------------------------------------------|
| 1.9     | Initial SMB FPGA image.                       |
| 1.11    | Fix flipped LEDs on bottom half of the ports. |

## meru800bia-fan-cpld.astp

| Version | Changelog                                                               |
|---------|-------------------------------------------------------------------------|
| 1.2     | Initial FAN CPLD image.                                                 |
| 1.3     | FAN_CHANGE registers now clear on per-bit basis.                        |
| 1.7     | No software-visible change vs 1.3.                                      |
| 1.8     | No software-visible change vs 1.7.                                      |
| 1.9     | Turn off FAN LED based on the CPLD register instead of remaining amber. |

## bcm53134image-p1.bin
| Version | Changelog                                        |
|---------|--------------------------------------------------|
| 0.6     | Initial Bcm53134 P1 image.                       |
