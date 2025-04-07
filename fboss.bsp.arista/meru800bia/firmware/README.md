# Firmware Structure Convention

## Naming
The firmware binary must follow the nomenclature `<supported_platform_names>_<firmware_binary_name>_v<versionNumber>.img.` For example, the aboot image to support meru800bia and meru800bfa should be meru800bia-meru800bfa_bios_vAboot-norcal13-13.1.2-lcc-64m-38688619. The version should always start with a v and then you can append whatever will be printed when fw_util version command is executed.

## Organization
Use a directory structure with numbered packages (e.g., package_0, package_1, etc.) where the highest number always represents the latest firmware drop. it should look something like the one below.

```
/ls -lah fboss.bsp.arista/meru800bia/firmware

total 12K
drwxr-xr-x. 1 deank deank  150 Jan 13 23:50 .
drwxr-xr-x. 1 deank deank  250 Jan  6 20:03 ..

drwxr-xr-x. 1 deank deank  762 Jan 13 23:50 package_0 # First drop
drwxr-xr-x. 1 deank deank  762 Jan 13 23:50 package_1 # Second drop

drwxr-xr-x. 1 deank deank  762 Jan  6 20:03 package_2 # highest one will always be latest firmware drop.  
```