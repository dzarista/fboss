#!/bin/bash

# Script to upgrade Viper SCD image on a system running FBOSS without rebooting the system
# The script expects a stripped FPGA image matching the SCD SPI flash size
# SCD register values are not preserved during the upgrade

# PCA9539 GPIO expander is at address 0x74 on CPU_SMBus
readonly PCA_CHIP_ADDR=0x74
# Refer https://www.ti.com/lit/ds/symlink/pca9539.pdf for PCA9539 specification
readonly PCA_REG_INPUT_PORT_0=0x0
readonly PCA_REG_OUTPUT_PORT_1=0x3
readonly PCA_REG_CONFIG_REG_1=0x7
readonly BITMASK_PIN_0=0x1
readonly BITMASK_PIN_1=0x2
readonly BITMASK_PIN_6=0x40

# Check if FPGA image path was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <stripped_scd_image_file_path>"
    exit 1
fi
fw_binary_file="$1"
# Check if the FPGA image file exists
if [ ! -f "$fw_binary_file" ]; then
    echo "Error: cannot find the FPGA image '$fw_binary_file'."
    exit 1
fi

# Stop services before FPGA upgrade
# platform_manager needs to be run again after the upgrade to reload the scd driver
# sensor_service and qsfp_service are dependent on scd-smbus driver which will also be reloaded when platform_manager starts
systemctl stop sensor_service
systemctl stop qsfp_service
systemctl stop platform_manager
systemctl stop fboss_sw_agent
systemctl stop fboss_hw_agent@0

# PCA9539 GPIO expander is connected to accelerator 1 channel 0 of Fairywren CPLD (0000:07:00.0)
pca_bus=$(i2cdetect -l | grep '0000:07:00.0 SMBus master 1 bus 0' | awk -F' ' '{print $1}' | tr -d 'i2c-');

# Set the following PCA pins as output pins
# IO1_1 - HITLESS_LATCH_L
i2cset -f -y -m $BITMASK_PIN_1 $pca_bus $PCA_CHIP_ADDR $PCA_REG_CONFIG_REG_1 0x0
# IO1_6 - SCD_RESET_L
i2cset -f -y -m $BITMASK_PIN_6 $pca_bus $PCA_CHIP_ADDR $PCA_REG_CONFIG_REG_1 0x0
# IO1_0 - SCD_PRGM_L
i2cset -f -y -m $BITMASK_PIN_0 $pca_bus $PCA_CHIP_ADDR $PCA_REG_CONFIG_REG_1 0x0

# Assert HITLESS_LATCH_L. This preserves the J3 reset state information and other information controlled by the SCD
i2cset -f -y -m $BITMASK_PIN_1 $pca_bus $PCA_CHIP_ADDR $PCA_REG_OUTPUT_PORT_1 0x0
# Program the new SCD image into the Artix-7 SPI flash
fw_util --config_file=/opt/fboss/share/platform_configs/fw_util.json --fw_target_name=smb_fpga --fw_action=program --fw_binary_file=$fw_binary_file
# Ensure at least 5 ms has passed since asserting HITLESS_LATCH_L
sleep 1
# Assert SCD_RESET_L
i2cset -f -y -m $BITMASK_PIN_6 $pca_bus $PCA_CHIP_ADDR $PCA_REG_OUTPUT_PORT_1 0x0
# Assert SCD_PRGM_L for a minimum time 250ns then change it back to '1'. This forces the FPGA to load its new image from SPI flash
i2cset -f -y -m $BITMASK_PIN_0 $pca_bus $PCA_CHIP_ADDR $PCA_REG_OUTPUT_PORT_1 0x0
sleep 1
i2cset -f -y -m $BITMASK_PIN_0 $pca_bus $PCA_CHIP_ADDR $PCA_REG_OUTPUT_PORT_1 0xFF

# Poll SCD_DONE(IO0_0). The pin will transition from 0 to 1 when the new image is loaded
programming_done_reg=$(i2cget -f -y $pca_bus $PCA_CHIP_ADDR $PCA_REG_INPUT_PORT_0)
programming_done_bit=$(( programming_done_reg & $BITMASK_PIN_0 ))
regcheck_counter=0;
regcheck_counter_limit=60;
until [[ $programming_done_bit -eq 1 || $regcheck_counter -gt $regcheck_counter_limit ]];
do
  sleep 1;
  programming_done_reg=$(i2cget -f -y $pca_bus $PCA_CHIP_ADDR $PCA_REG_INPUT_PORT_0)
  programming_done_bit=$(( programming_done_reg & $BITMASK_PIN_0 ))
  (( regcheck_counter++ ));
done;

if [ $regcheck_counter -gt $regcheck_counter_limit ]; then
  echo "Error: timed-out waiting for SCD config done signal"
  exit 2
fi
# De-assert SCD_RESET_L
i2cset -f -y -m $BITMASK_PIN_6 $pca_bus $PCA_CHIP_ADDR $PCA_REG_OUTPUT_PORT_1 0xFF
# De-assert HITLESS_LATCH_L
i2cset -f -y -m $BITMASK_PIN_1 $pca_bus $PCA_CHIP_ADDR $PCA_REG_OUTPUT_PORT_1 0xFF

# Start services after FPGA upgrade
systemctl start fboss_hw_agent@0
systemctl start fboss_sw_agent
systemctl start platform_manager
systemctl start qsfp_service
systemctl start sensor_service
