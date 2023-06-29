#!/bin/bash

# Init script for FBOSS OSS.
# Based on instructions from:
# https://github.com/facebook/fboss/blob/main/installer/centos-7-x86_64/README.md

FBOSS_DIR="/opt/fboss"
SYSTEMD_DIR="/etc/systemd/system"

set -e

# We need to cd into the FBOSS home directory because some of the setup scripts
# have a dependency on the working dir.
cd "${FBOSS_DIR}"

# Install dependencies.
echo -ne "\nInstalling dependencies\n"
declare -a deps=("python36-devel"
                 "epel-release"
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
   echo -ne "\nRunning platform init\n"
   ./bin/platform_init.sh
fi

# Now run the core setup scripts.
echo -ne "\nRunning fboss setup\n"
source ./bin/setup_fboss_env
./bin/setup.py

# Link binaries.
echo -ne "\nLinking FBOSS binaries\n"
ln -sf /opt/fboss/bin/* /usr/bin/

# Link libraries.
echo -ne "\nLinking FBOSS libraries\n"
ln -sf /opt/fboss/lib/lib* /usr/lib/
ln -sf /opt/fboss/lib64/* /usr/lib64/
ldconfig

# Create links for services.
echo -ne "\nInstalling services\n"
for service in /opt/fboss/share/systemd/*; do
   name=$(basename "${service}")
   ln -sf "${service}" "${SYSTEMD_DIR}"/"${name}"
done

# Link configs to correct locations. We do this by reading the model name from the fru.json file then using that model
# name to grab the correct service configuration files.
echo -ne  "\nLinking service configuration files\n"
FRU="/var/facebook/fboss/fruid.json"
MODEL_NAME=$(cat "${FRU}" | python3 -c "import sys, json; print(json.load(sys.stdin)['Information']['Product Name'].lower())")
echo "Found model name ${MODEL_NAME} in ${FRU}"
mkdir -p /etc/coop

FBOSS_SHARE_DIR="/opt/fboss/share"
WEDGE_AGENT_PLATFORM_CONFIG="${FBOSS_SHARE_DIR}/hw_test_configs/${MODEL_NAME}.agent.materialized_JSON"
WEDGE_AGENT_DEFAULT_CONFIG="/etc/coop/agent.conf"
if [ -f "${WEDGE_AGENT_PLATFORM_CONFIG}" ]; then
   echo "Linking ${WEDGE_AGENT_PLATFORM_CONFIG} to ${WEDGE_AGENT_DEFAULT_CONFIG}"
   ln -sf "${WEDGE_AGENT_PLATFORM_CONFIG}" "${WEDGE_AGENT_DEFAULT_CONFIG}"
else
   echo "No platform wedge_agent config found for model name ${MODEL_NAME}"
fi

QSFP_PLATFORM_CONFIG="$FBOSS_SHARE_DIR/qsfp_test_configs/$MODEL_NAME.materialized_JSON"
QSFP_DEFAULT_CONFIG="/etc/coop/qsfp.conf"
if [ -f "$QSFP_PLATFORM_CONFIG" ]; then
   echo "Linking $QSFP_PLATFORM_CONFIG to $QSFP_DEFAULT_CONFIG"
   ln -sf "${QSFP_PLATFORM_CONFIG}" "${QSFP_DEFAULT_CONFIG}"
else
   echo "No platform qsfp_service config found for model name ${MODEL_NAME}"
fi

LINK_PLATFORM_CONFIG="$FBOSS_SHARE_DIR/link_test_configs/$MODEL_NAME.materialized_JSON"
LINK_DEFAULT_CONFIG="/etc/coop/link.conf"
if [ -f "$LINK_PLATFORM_CONFIG" ]; then
   echo "Linking $LINK_PLATFORM_CONFIG to $LINK_DEFAULT_CONFIG"
   ln -sf "${LINK_PLATFORM_CONFIG}" "${LINK_DEFAULT_CONFIG}"
else
   echo "No platform hw_link_test config found for model name ${MODEL_NAME}"
fi
