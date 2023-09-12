#!/bin/bash

# Platform init script for Meru800bfa.

set -e

load_kernel_modules() {
   # Load required kernel modules. The udev rules depend on these.
   printf "\nLoading kernel modules\n"
   kernel="$(uname -r)"
   kernel_lib_dir="/lib/modules/${kernel}"
   declare -a kmodules=("kernel/drivers/mfd/mfd-core"
                        "kernel/drivers/leds/led-class"
                        "scd"
                        "scd-leds"
                        "scd-smbus"
                        "scd-xcvr"
                        "i2c_dev_sysfs"
                        "decker-cpld"
                        "dsf-fan-cpld"
                       )

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

load_udev_rules() {
   printf "\nLoading udev rules\n"
   udevadm control -R
   udevadm trigger
}

# Meru800bfa init.
load_kernel_modules
load_udev_rules
