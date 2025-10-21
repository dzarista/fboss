# Firmware Structure Convention

## Naming
The firmware binary must follow the nomenclature `P_<supported_platform_names>_F_<firmware_binary_name>_V_<versionNumber>.img.` For example, the aboot image for yamp should be P_yamp_F_bios_V_Aboot-norcal7-7.3.6-cb411-generic-2x4-44270425.rom. The version should always start with a V_ and then you can append whatever which will be printed when fw_util version command is executed.

## Organization
Use a directory structure with numbered packages (e.g., package_0, package_1, etc.) where the highest number always represents the latest firmware drop. it should look something like the one below.

```bash
bash-5.1$ ls -lah fboss.bsp.arista/yamp/firmware
total 4.0K
drwxr-xr-x. 1 mparker mparker  54 Oct 20 21:58 .
drwxr-xr-x. 1 mparker mparker  34 Oct 20 21:54 ..
drwxr-xr-x. 1 mparker mparker 138 Oct 20 21:59 package_0
drwxr-xr-x. 1 mparker mparker 150 Oct 20 21:59 package_1
-rw-r--r--. 1 mparker mparker 989 Oct 20 21:58 README.md
```
