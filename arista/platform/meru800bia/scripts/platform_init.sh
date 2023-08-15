#!/bin/bash

# Platform init script for Meru800bia.

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
                        "scd-watchdog"
                        "scd-xcvr"
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

# Meru800bia init.
load_kernel_modules
load_udev_rules

# TODO FIXME: if running kernel 5.19, skip setup.py because the BCM kernel
# modules will fail to load.
kernel=$(uname -r)
if [[ "${kernel}" == "5.19.0" ]]; then
   touch /tmp/.fboss_skip_setup
   depmod -A
fi
