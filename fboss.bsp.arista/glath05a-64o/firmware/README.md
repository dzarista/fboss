# Firmware Structure Convention

## Naming
The firmware binary must follow the nomenclature `P_<supported_platform_names>_F_<firmware_binary_name>_V_<versionNumber>.img.` For example, the aboot image for glath05a should be P_glath05a_F_bios_V_Aboot-norcal13-13.1.4-lcc-64m-40551478. The version should always start with a V_ and then you can append whatever will be printed when fw_util version command is executed.

## Organization
Use a directory structure with numbered packages (e.g., package_0, package_1, etc.) where the highest number always represents the latest firmware drop. it should look something like the one below.

```
/ls -lah fboss.bsp.arista/glath05a/firmware/
total 4.0K
drwxr-xr-x. 1 arajeev arajeev   36 May 12 07:22 .
drwxr-xr-x. 1 arajeev arajeev   16 Apr 30 01:36 ..
drwxr-xr-x. 1 arajeev arajeev  400 May 12 07:21 package_0 # First drop
-rw-r--r--. 1 arajeev arajeev 1.1K May 12 07:22 README.md
```
