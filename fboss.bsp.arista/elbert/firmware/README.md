# Firmware Structure Convention

## Naming
The firmware binary must follow the nomenclature `P_<supported_platform_names>_F_<firmware_binary_name>_V_<versionNumber>.img.` For example, the aboot image for elbert should be P_elbert_F_bios_V_Aboot-norcal7-7.3.4-cb411-generic-8x1-42641583. The version should always start with a V_ and then you can append whatever which will be printed when fw_util version command is executed.

## Organization
Use a directory structure with numbered packages (e.g., package_0, package_1, etc.) where the highest number always represents the latest firmware drop. it should look something like the one below.

```
ls -lah fboss.bsp.arista/elbert/firmware

total 4.0K
drwxr-xr-x. 1 tharish tharish   70 Aug 13 16:49 .
drwxr-xr-x. 1 tharish tharish   34 Aug 11 17:15 ..
-rw-r--r--. 1 tharish tharish 1.1K Aug 13 16:52 README.md
drwxr-xr-x. 1 tharish tharish  704 Aug 13 16:47 firmware_dowgrade
drwxr-xr-x. 1 tharish tharish  952 Aug 12 16:05 package_0
```
