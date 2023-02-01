#!/bin/bash

# Init script for FBOSS OSS.
# Based on instructions from:
# https://github.com/facebook/fboss/blob/main/installer/centos-7-x86_64/README.md

FBOSS_DIR="/opt/fboss"
SYSTEMD_DIR="/etc/systemd/system"

# We need to cd into the FBOSS home directory because some of the setup scripts
# have a dependency on the working dir.
cd "${FBOSS_DIR}"

# Install dependencies.
printf "\nInstalling dependencies\n"
declare -a deps=("epel-release"
                 "flashrom"
                 "lm_sensors"
                 "i2c-tools"
                 "usbutils"
                 "pciutils"
                 "libgpiod"
                 "libgpiod-utils"
                )
for dep in "${deps[@]}"
do
   rpm -q "${dep}" || yum install -y "${dep}"
done

# Check to see if a platform-specfic init script is installed. If so, run that first.
if [ -f "./bin/platform_init.sh" ]; then
   printf "\nRunning platform init\n"
   ./bin/platform_init.sh
fi

# Now run the core setup scripts.
printf "\nRunning fboss setup\n"
source ./bin/setup_fboss_env
./bin/setup.py

# Create links for services.
printf "\nInstalling services\n"
for service in /opt/fboss/share/systemd/*; do
   name=$(basename "${service}")
   if [ -f "${SYSTEMD_DIR}"/"${name}" ]; then
      unlink "${SYSTEMD_DIR}"/"${name}"
   fi
   ln -s "${service}" "${SYSTEMD_DIR}"/"${name}"
done
