#!/bin/bash

# Platform init script for Darwin48V. Basically we just need to load a single
# udev rule to account for PM currently not supporting the Rook CPLD because
# the hijacked PCI device isn't in the deviceId table.

set -e

load_udev_rules() {
   printf "\nLoading udev rules\n"
   udevadm control -R
   udevadm trigger
}

# Darwin init.
load_udev_rules
