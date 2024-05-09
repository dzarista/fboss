#!/bin/bash

# Switch the system to BMC mode.

switch_to_bmc_fairywren() {
   REV=$1
   DEV_ADDR=0x52

   # P1 systems have DS4520 at 0x50
   if [[ "${REV}" == "1.0" ]]; then
      DEV_ADDR=0x50
   fi

   set -x
   i2cset -f -y 1 "$DEV_ADDR" 0xf4 0x0
   sleep 0.1
   i2cset -f -y 1 "$DEV_ADDR" 0xf1 0x0
   sleep 0.1
   i2cset -f -y 1 "$DEV_ADDR" 0xf0 0x41
   sleep 0.1
   i2cset -f -y 1 "$DEV_ADDR" 0xf3 0x0
   sleep 0.1
   i2cset -f -y 1 "$DEV_ADDR" 0xf2 0x41
   sleep 0.1
   i2cset -f -y 1 "$DEV_ADDR" 0xf4 0x1
   sleep 0.1
   echo 0xdead > /run/devmap/fpgas/MERU_SCM_CPLD/chassis_power_cycle
}

PRODUCT=$(dmidecode -t 2 | grep "Product" | awk '{print $3}')
VERSION=$(dmidecode -t 2 | grep "Version" | awk '{print $2}')
if [[ "${PRODUCT}" =~ MERU800B(I|F)A ]]; then
   switch_to_bmc_fairywren "${VERSION}"
else
   echo "Product not supported!"
fi
