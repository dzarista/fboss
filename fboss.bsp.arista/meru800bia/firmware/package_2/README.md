# Firmware Package #2

This directory contains the firmware programmable binaries for the
Meru800bia platform. The table below shows the programmables:

| Programmable Name                                                            | Description          |
|------------------------------------------------------------------------------|----------------------|
| P_meru800bia_meru800bfa_F_bios_V_Aboot-norcal13-13.1.4-lcc-64m-40551478.rom  | Bootloader for x86   |
| P_meru800bia_meru800bfa_F_scm_cpld_V_4.16.astp                               | SCM CPLD JTAG image  |
| P_meru800bia_F_smb_fpga_V_4.16.abit                                          | SMB FPGA SPI image   |
| P_meru800bia_F_fan_cpld_V_1.9.astp                                           | Fan CPLDs JTAG image |
| P_meru800bia_F_bcm53134image-p4_V_1.2.bin                                    | Bcm53134 p4 image    |


# Changelogs

The tables below show the released version history for each
programmable. The most recent version can be found in this
directory.

## Changes From Last Package
| Programmable Name                                                            | Description                                                            |
|------------------------------------------------------------------------------|------------------------------------------------------------------------|
| P_meru800bia_meru800bfa_F_bios_V_Aboot-norcal13-13.1.4-lcc-64m-40551478.rom  | Fix Fairywren extra reset on boot.                                     |
| P_meru800bia_F_smb_fpga_V_4.16.abit                                          | No software-visible change vs 4.14.                                    |

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
| Aboot-norcal13-13.1.3-lcc-64m-38965988     | Contains support for the UAPI boot loader spec (BLS).                              |
| Aboot-norcal13-13.1.4-lcc-64m-40551478     | Fix Fairywren extra reset on boot.                                                 |

## SCM CPLD

| Version | Changelog                                                          |
|---------|--------------------------------------------------------------------|
| 4.0     | Initial SCM CPLD image                                             |
| 4.2     | Fixes 32-byte SMBus block read needed for UCD90320 driver support. |
| 4.13    | Increases MDIO drive strength for improved stability.              |
| 4.16    | Treats non persistant (<1us) as a correctable error.               |

## SMB FPGA

| Version | Changelog                                                          |
|---------|--------------------------------------------------------------------|
| 4.3     | Initial SMB FPGA image.                                            |
| 4.6     | Use PUC serial interface to configure J3 PUC for QSPI single lane. |
| 4.8     | No software-visible change vs 4.6.                                 |
| 4.13    | Adds support for power cycle through push-button.                  |
| 4.14    | No software-visible change vs 4.13.                                |
| 4.16    | No software-visible change vs 4.14.                                |

## FAN CPLD

| Version | Changelog                                                               |
|---------|-------------------------------------------------------------------------|
| 1.2     | Initial FAN CPLD image.                                                 |
| 1.3     | FAN_CHANGE registers now clear on per-bit basis.                        |
| 1.7     | No software-visible change vs 1.3.                                      |
| 1.8     | No software-visible change vs 1.7.                                      |
| 1.9     | Turn off FAN LED based on the CPLD register instead of remaining amber. |

## BCM53134 IMAGE

| Version | Changelog                                        |
|---------|--------------------------------------------------|
| 1.1     | Initial Bcm53134 P4 image.                       |
| 1.2     | Fixes Whistler multicast forwarding issue.       |
