#!/bin/bash

# PCI addresses associated with FPGAs
scm_cpld_pci_addr="0000:07:00.0"
smb_fpga0_pci_addr="0000:02:00.0"
smb_fpga1_pci_addr="0000:01:00.0"
smb_fpga2_pci_addr="0000:03:00.0"
smb_fpga3_pci_addr="0000:04:00.0"

# Check the presence of vendor sysfs entry for devices bound to scd driver
check_vendor_sysfs_entry() {
  local pci_address="$1"
  local vendor_file="/sys/bus/pci/drivers/scd/$pci_address/vendor"

  if cat "$vendor_file" > /dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

chmod +x xapp
chmod +x jam

systemctl stop qsfp_service
systemctl stop sensor_service
systemctl stop led_service
systemctl stop platform_manager

modprobe scd
if ! check_vendor_sysfs_entry "$scm_cpld_pci_addr"; then
  echo "Vendor file does not exist for $scm_cpld_pci_addr, updating SCM CPLD"
  ./jam -aprogram -fmeru_cpu_cpld -v fairywrenCpld.astp
fi

platform_manager -config-file pm_minimal_smbus.json -noenable_pkg_mgmnt -run_once=true -reload_kmods=true

modprobe decker_cpld
decker_i2cdetect_output=$(i2cdetect -l | grep "$scm_cpld_pci_addr.*SMBus master 1 bus 0")
decker_i2c_bus=$(echo "$decker_i2cdetect_output" | awk '{print $1}')
echo "decker_cpld 0x23" > "/sys/bus/i2c/devices/$decker_i2c_bus/new_device"
decker_i2c_bus_num=$(echo "$decker_i2c_bus" | sed 's/i2c-//') # Remove "i2c-"
decker_i2c_dir="${decker_i2c_bus_num}-0023"
cpld_ver_path="/sys/bus/i2c/drivers/decker-cpld/$decker_i2c_dir/cpld_ver"
if ! cat "$cpld_ver_path" > /dev/null 2>&1; then
  echo "Path $cpld_ver_path does not exist, updating SMB CPLD"
  echo 1 > /sys/bus/pci/drivers/scd/$scm_cpld_pci_addr/switch_jtag_enable
  ./jam -aprogram -fmeru_switch_cpld -v deckerCpld.astp
  systemctl stop platform_manager
  platform_manager -config-file pm_minimal_smbus.json -noenable_pkg_mgmnt -run_once=true -reload_kmods=true
  modprobe decker_cpld
  echo "decker_cpld 0x23" > "/sys/bus/i2c/devices/$decker_i2c_bus/new_device"
fi

if ! check_vendor_sysfs_entry "$smb_fpga0_pci_addr"; then
  program_smb_fpga0=true
else
  program_smb_fpga0=false
fi
if ! check_vendor_sysfs_entry "$smb_fpga1_pci_addr"; then
  program_smb_fpga1=true
else
  program_smb_fpga1=false
fi
if ! check_vendor_sysfs_entry "$smb_fpga2_pci_addr"; then
  program_smb_fpga2=true
else
  program_smb_fpga2=false
fi
if ! check_vendor_sysfs_entry "$smb_fpga3_pci_addr"; then
  program_smb_fpga3=true
else
  program_smb_fpga3=false
fi

if [[ "$program_smb_fpga0" == true ]]; then
  echo "Updating SMB FPGA0"
  echo 1 > /sys/bus/pci/drivers/scd/$scm_cpld_pci_addr/switch_jtag_enable
  echo 1 > /sys/bus/i2c/drivers/decker-cpld/$decker_i2c_dir/jtag_mux_sel
  ./xapp -f meru_scd blackcomb0_scd_latest_fpga_only.xsvf
fi
if [[ "$program_smb_fpga1" == true ]]; then
  echo "Updating SMB FPGA1"
  echo 1 > /sys/bus/pci/drivers/scd/$scm_cpld_pci_addr/switch_jtag_enable
  echo 2 > /sys/bus/i2c/drivers/decker-cpld/$decker_i2c_dir/jtag_mux_sel
  ./xapp -f meru_scd blackcomb1_scd_latest_fpga_only.xsvf
fi
if [[ "$program_smb_fpga2" == true ]]; then
  echo "Updating SMB FPGA2"
  echo 1 > /sys/bus/pci/drivers/scd/$scm_cpld_pci_addr/switch_jtag_enable
  echo 3 > /sys/bus/i2c/drivers/decker-cpld/$decker_i2c_dir/jtag_mux_sel
  ./xapp -f meru_scd blackcomb2_scd_latest_fpga_only.xsvf
fi
if [[ "$program_smb_fpga3" == true ]]; then
  echo "Updating SMB FPGA3"
  echo 1 > /sys/bus/pci/drivers/scd/$scm_cpld_pci_addr/switch_jtag_enable
  echo 4 > /sys/bus/i2c/drivers/decker-cpld/$decker_i2c_dir/jtag_mux_sel
  ./xapp -f meru_scd blackcomb3_scd_latest_fpga_only.xsvf
fi

if [[ "$program_smb_fpga0" == true || "$program_smb_fpga1" == true || "$program_smb_fpga2" == true || "$program_smb_fpga3" == true ]]; then
  platform_manager -config-file pm_minimal_spi.json -noenable_pkg_mgmnt -run_once=true -reload_kmods=true
fi

if [[ "$program_smb_fpga0" == true ]]; then
  echo "Continuing SMB FPGA0 upgrade"
  fw_util --fw_target_name=smb_fpga0 --fw_action=program --fw_binary_file=blackcomb0_scd_latest_stripped.abit
fi
if [[ "$program_smb_fpga1" == true ]]; then
  echo "Continuing SMB FPGA1 upgrade"
  fw_util --fw_target_name=smb_fpga1 --fw_action=program --fw_binary_file=blackcomb1_scd_latest_stripped.abit
fi
if [[ "$program_smb_fpga2" == true ]]; then
  echo "Continuing SMB FPGA2 upgrade"
  fw_util --fw_target_name=smb_fpga2 --fw_action=program --fw_binary_file=blackcomb2_scd_latest_stripped.abit
fi
if [[ "$program_smb_fpga3" == true ]]; then
  echo "Continuing SMB FPGA3 upgrade"
  fw_util --fw_target_name=smb_fpga3 --fw_action=program --fw_binary_file=blackcomb3_scd_latest_stripped.abit
fi
