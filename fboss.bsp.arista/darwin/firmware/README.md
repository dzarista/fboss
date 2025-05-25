# Firmware Structure Convention

## Naming
The firmware binary must follow the nomenclature `P_<supported_platform_names>_F_<firmware_binary_name>_V_<versionNumber>.img.` For example, the aboot image for darwin should be P_darwin_F_bios_V_Aboot-norcal7-7.5.3-cb411-rook-2x4-39223411. The version should always start with a V_ and then you can append whatever will be printed when fw_util version command is executed.

## Organization
Use a directory structure with numbered packages (e.g., package_0, package_1, etc.) where the highest number always represents the latest firmware drop. it should look something like the one below.

```
/ls -lah fboss.bsp.arista/darwin/firmware

total 12K
drwxr-xr-x. 1 deank deank  150 Jan 13 23:50 .
drwxr-xr-x. 1 deank deank  250 Jan  6 20:03 ..

drwxr-xr-x. 1 deank deank  762 Jan 13 23:50 package_0 # First drop
drwxr-xr-x. 1 deank deank  762 Jan 13 23:50 package_1 # Second drop

drwxr-xr-x. 1 deank deank  762 Jan  6 20:03 package_2 # highest one will always be latest firmware drop.  
```
