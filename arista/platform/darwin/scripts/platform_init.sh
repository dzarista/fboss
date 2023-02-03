#!/bin/bash

# Platform init script for Darwin.

load_kernel_modules() {
   # Load required kernel modules. The udev rules depend on these.
   printf "\nLoading kernel modules\n"
   kernel="$(uname -r)"
   kernel_lib_dir="/lib/modules/${kernel}"
   declare -a kmodules=("i2c_dev_sysfs"
                        "amax5970"
                        "aslg4f4527"
                        "blackhawk-cpld"
                        "scd"
                        "scd-leds"
                        "scd-smbus"
                        "scd-watchdog"
                        "rook-fan-cpld"
                       )

   # In 5.x kernels, the scd-leds driver has a dependency on the led-class module.
   if [[ "${kernel}" != *"4.18"* ]]; then
      kmodules=("kernel/drivers/leds/led-class" "${kmodules[@]}")
   fi

   for mod in "${kmodules[@]}"
   do
      if $(lsmod | grep "$(basename ${mod//-/_})" >& /dev/null); then
         echo "${mod} already installed"
      else
         echo "Installing ${mod}"
         insmod "${kernel_lib_dir}"/"${mod}".ko
      fi
   done
}

enumerate_rook_pci() {
   # Add Rook CPLD PCI device; this is needed so that scd driver discovers Rook CPLD.
   printf "\nEnumerating Rook CPLD on PCI\n"
   echo "8086 6f76" > /sys/bus/pci/drivers/scd/new_id
}

load_udev_rules() {
   printf "\nLoading udev rules\n"
   udevadm control -R
   udevadm trigger
}

load_prefdl() {
   printf "\nLoading prefdl\n"
   FLASH_DIR=/mnt/flash
   if [[ ! -d "${FLASH_DIR}" ]]; then
      echo "Mounting /mnt/flash"
      mkdir -p /mnt/flash
      mount /dev/sda1 /mnt/flash
   fi

   FLASH_PREFDL=/mnt/flash/.system-prefdl-bin
   if [[ ! -f "${FLASH_PREFDL}" ]]; then
      layout=/tmp/layout
      tmpfile=/tmp/bios
      prefdl_dir=/tmp/WeutilDarwin
      prefdl_bin="${prefdl_dir}"/system-prefdl-bin
   
      mkdir -p "${prefdl_dir}"
      echo "Reading prefdl from SPI flash to ${prefdl_bin}"

      echo "00001000:0001efff prefdl" > "${layout}"
      flashrom -p internal -c "MX25L12805D" -l "${layout}" -i prefdl -r "${tmpfile}" || \
         flashrom -p internal -c "N25Q128..3E" -l "${layout}" -i prefdl -r "${tmpfile}" || \
         flashrom -p internal -l "${layout}" -i prefdl -r "${tmpfile}"
      dd if="${tmpfile}" of="${prefdl_bin}" bs=1 skip=8192 count=61440
   fi
}

# Darwin init.
load_kernel_modules
enumerate_rook_pci
load_udev_rules
load_prefdl
