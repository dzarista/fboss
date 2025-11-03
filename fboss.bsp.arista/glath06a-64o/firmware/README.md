# Firmware Structure Convention

## Naming
The firmware binary must follow the nomenclature `P_<supported_platform_names>_F_<firmware_binary_name>_V_<versionNumber>.img.` For example, the aboot image for glath06a should be P_glath06a_F_bios_V_Aboot-norcal18-18.0.2-SODIMM-ENG-44064519. The version should always start with a V_ and then you can append whatever will be printed when fw_util version command is executed.

## Organization
Use a directory structure with numbered packages (e.g., package_0, package_1, etc.) where the highest number always represents the latest firmware drop. it should look something like the one below.

```
ls -lah fboss.bsp.arista/glath06a-64o/firmware/
total 4.0K
drwxr-xr-x. 1 adamc adamc  72 Oct 27 11:20 .
drwxr-xr-x. 1 adamc adamc  16 Oct 27 11:20 ..
drwxr-xr-x. 1 adamc adamc 288 Oct 27 11:20 firmware_downgrade
drwxr-xr-x. 1 adamc adamc 434 Oct 27 11:49 package_0
-rw-r--r--. 1 adamc adamc 926 Oct 27 11:20 README.md
```
