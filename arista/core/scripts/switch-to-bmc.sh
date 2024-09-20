#!/bin/bash

# Switch the system to BMC mode.

IGNORE_OUT="2>/dev/null > /dev/null"

no_reboot=0
check_usb_connectivity=0

usage() {
   program=$(basename "$0")
   echo "Usage:"
   echo "$program [--no-reboot|--check-usb-connectivity]"
   echo "      --no-reboot : Set next boot to BMC but do not reboot"
   echo "      --check-usb-connectivity : Check USB connection to BMC"
   exit 1
}

switch_to_bmc_fairywren() {
   REV="$1"

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
   if [ $no_reboot -eq 0 ]; then
      echo 0xdead > "$CPLD/chassis_power_cycle"
   fi
}

switch_to_bmc() {
   platform="$1"
   if [[ "$platform" == "fairywren" ]]; then
      REV=$(dmidecode -t 2 | grep "Version" | awk '{print $2}')
      switch_to_bmc_fairywren "${REV}"
   fi
}

wait_for_cmd() {
   cmd="$1"
   timeout="$2"
   while [ $timeout -gt 0 ]; do
      if eval "$cmd"; then
         return 0
      fi
      sleep 5
      timeout=$(( $timeout - 5 ))
   done
   return 1
}

re_enumerate_usb0() {
   usb_path="/sys/bus/usb/devices/usb1/$USB"
   echo "Attempting to re-enumerate usb0"
   for v in $(seq 0 1); do
      echo "$v" > "$usb_path/authorized"
      wait_for_cmd "cat $usb_path/authorized | grep $v"
      sleep 1
   done
   return 0
}

check_usb_connectivity() {
   MAX_RETRIES=3

   bmc_not_reset="$CPLD/bmc_not_reset"
   usb_path="/sys/bus/usb/devices/usb1/$USB"

   for i in $(seq 1 $MAX_RETRIES); do
      echo "Turning off BMC"
      echo 0 > "$bmc_not_reset"
      sleep 0.25
      echo "Turning on BMC"
      echo 1 > "$bmc_not_reset"
      sleep 0.25

      for retries in $(seq 1 3); do
         echo "Waiting for BMC usb Hub to show up..."
         if ! wait_for_cmd "ls $usb_path/ $IGNORE_OUT" 300; then
            break
         fi
         echo "Waiting for BMC usb0 interface to show up..."
         if wait_for_cmd "ls $usb_path/$USB_DEV/ $IGNORE_OUT" 150; then
            echo "Waiting for usb ipv6 config to exist..."
            if wait_for_cmd "ls /proc/sys/net/ipv6/conf/usb0/disable_ipv6 $IGNORE_OUT" 100; then
               sysctl --quiet --write net.ipv6.conf.usb0.disable_ipv6=0 > /dev/null
               sleep 0.25
               echo "ip link set dev usb0 up"
               ip link set dev usb0 up > /dev/null
               sleep 0.25
               echo "Waiting for ping6 usb0 default IP fe80::1..."
               if ! wait_for_cmd "ping6 fe80::1%usb0 -c 1 $IGNORE_OUT" 30; then
                  break
               fi
               return 0
            fi
         fi
         re_enumerate_usb0
      done
      echo "Timed out on attempt $i"
   done
   echo "Timed out waiting for usb interface after $MAX_RETRIES attempts"
   return 1
}

if [ $# -eq 1 ]; then
   case "$1" in
      "--no-reboot")
         no_reboot=1
         ;;
      "--check-usb-connectivity")
         check_usb_connectivity=1
         ;;
      *)
         usage
         ;;
   esac
elif [ $# -gt 1 ]; then
   usage
fi

PRODUCT=$(dmidecode -t 2 | grep "Product" | awk '{print $3}')
if [[ "${PRODUCT}" =~ MERU800B(I|F)A ]]; then
   platform="fairywren"
   CPLD="/run/devmap/fpgas/MERU_SCM_CPLD"
   USB="1-2"
   USB_DEV="1-2:1.0"
else
   echo "Product not supported!"
fi

if [ $check_usb_connectivity -eq 0 ]; then
   switch_to_bmc "$platform"
else
   check_usb_connectivity "$platform"
fi
