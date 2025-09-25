# Firmware Package #3

| Programmable Name                                                           | Description          |
|-----------------------------------------------------------------------------|----------------------|
| P_elbert_F_bios_V_Aboot-norcal7-7.3.5-cb411-generic-8x1-43071231.rom        | Bootloader for x86   |
| P_elbert_F_scm_V_2.14.astp                                                  | SCM CPLD JTAG image  |
| P_elbert_F_smb_V_3.14.astp                                                  | SMB FPGA JTAG image  |
| P_elbert_F_smb_cpld_V_5.1.astp                                              | SMB CPLD JTAG image  |
| P_elbert_F_fan_V_1.15.astp                                                  | FAN CPLD JTAG image  |
| P_elbert_F_pim_base_V_1.3.abin                                              | PIM base SPI image   |
| P_elbert_F_pim16q_V_7.7.abin                                                | PIM16Q SPI image     |
| P_elbert_F_pim8ddm_V_8.7.abin                                               | PIM8DDM SPI image    |
| P_elbert_F_th4_qspi_V_53248.5.abin                                          | TH4 QSPI image       |

# Changelogs

The tables below show the released version history for each
programmable. The most recent version can be found in this
directory.

## Changes From Last Package
| Programmable Name                                      | Description                               |
|--------------------------------------------------------|-------------------------------------------|
| Aboot-norcal7-7.3.5-cb411-generic-8x1-43071231.rom     | Qualified image with fix for issue of     |
|                                                        | number of reported cores by dmidecode.    |

## BIOS

| Version        | Changelog                                                                                                                                                                                                    |
|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 7.3.3-33492597 | Experimental image with boot methods support. This does not include UAPI bootloader enhancements. Only GRUB is supported for LOCAL boot.                                                                     |
| 7.3.4-42641583 | Qualified image with boot methods support including UAPI bootloader enhancements.                                                                                                                            |
| 7.3.5-43066215 | Fix for issue with number of reported cores by dmidecode. Experimental image.                                                                                                                                |
| 7.3.5-43071231 | Fix for issue with number of reported cores by dmidecode. Qualified image.                                                                                                                                   |
## SCM

| Version        | Changelog                                                                                                             |
|----------------|-----------------------------------------------------------------------------------------------------------------------|
| 2.5            | Initial P2 SCM image.                                                                                                 |
| 2.8            | No SW-visible change.                                                                                                 |
| 2.12           | Added DPE image to be on SCM instead of PIM8DDM.                                                                      |
| 2.13           | SCM has a new CPLD register for DPE mode. Added register 0x7000: write 32-bit 0xDEAD0000 to issue a FBOSS self reset. |
| 2.14           | Improve reset timing.                                                                                                 |

## SMB

| Version        | Changelog                |
|----------------|--------------------------|
| 2.7            | Initial P2 SMB image.    |
| 2.16           | No SW-visible change.    |
| 3.6            | No SW-visible change.    |
| 3.7            | No SW-visible change.    |
| 3.14           | No SW-visible change.    |

## SMB CPLD

| Version        | Changelog                |
|----------------|--------------------------|
| 5.0            | Initial P2 SMB image.    |
| 5.1            | No SW-visible change.    |

## FAN

| Version        | Changelog                                     |
|----------------|-----------------------------------------------|
| 1.1            | Initial fan CPLD image.                       |
| 1.2            | No SW-visible change.                         |
| 1.8            | Fixed FAN3/FAN4 register swap.                |
| 1.11           | LED register definition change.               |
| 1.15           | Added SMBus timeout and improved reset logic. |

## PIM BASE

| Version        | Changelog                           |
|----------------|-------------------------------------|
| 1.1            | Initial PIM base image.             |
| 1.3            | Added debug LED during PIM loading. |

## PIM 16Q

| Version        | Changelog                                                                                                                                            |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| 6.4            | Initial P2 image.                                                                                                                                    |
| 6.5            | No SW-visible change.                                                                                                                                |
| 6.16           | Resolved one port LED not functional issue.                                                                                                          |
| 7.4            | Blue/Green/Red LED control bits moved to 29:27 respectively, in all LED control registers. Status LED register default value changed to 0x3800_6d91. |
| 7.7            | Added PIM16Q2 support.                                                                                                                               |

## PIM 8DDM

| Version        | Changelog                                                                                                                                                                          |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 7.3            | Initial P2 image.                                                                                                                                                                  |
| 7.4            | No SW-visible change.                                                                                                                                                              |
| 7.10           | Resolved PIM8DDM not loading in PIM 7/8/9.                                                                                                                                         |
| 8.4            | Fanshell image no longer DPE. Blue/Green/Red LED control bits moved to 29:27 respectively, in all LED control registers. Status LED register default value changed to 0x3800_6d91. |
| 8.5            | Fixed LED are dim red instead of off when PIM powered off. No SW impact.                                                                                                           |
| 8.7            | No SW-visible change.                                                                                                                                                              |

## THQ QSPI 

| Version        | Changelog                |
|----------------|--------------------------|
| 53248.5        | Initial TH4 QSPI image.  |

