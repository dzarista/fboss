#!/bin/sh
#
# The script is designed to initialize platform devices on Darwin using
# the latest BSP drivers.
# NOTE: Ensure "fbiob-util" is installed on the dut before running this script

SYSFS_PCI_DRIVERS="/sys/bus/pci/drivers"
FBIOB_UTIL_CMD="fbiob-util"

SCD_PCIDRV="scd"

# SCD FPGA Info.
SCD_PCI_SBDF="0000:07:00.0"
SCD_PCI_DEVID="3475 0001 3475 0002"
SCD_CHARDEV="/dev/fbiob_3475.0001.3475.0002"

# ROOK CPLD Info.
ROOK_PCI_SBDF="0000:ff:0b.3"
ROOK_PCI_DEVID="8086 6f76"
ROOK_CHARDEV="/dev/fbiob_8086.6f76.0000.0000"

pci_add_new_id() {
    driver="$1"
    dev_id="$2"
    dev_sbdf="$3"
    sysfs_driver_dir="${SYSFS_PCI_DRIVERS}/${driver}"
    sysfs_device_dir="${sysfs_driver_dir}/${dev_sbdf}"

    if [ -e "${sysfs_device_dir}" ]; then
	echo "Device ID $dev_id is already supported by $driver driver."
	return
    fi

    echo "write device ID $dev_id to $driver.."
    echo "$dev_id" > "${sysfs_driver_dir}/new_id"

    sleep 1
    if [ ! -e "${sysfs_device_dir}" ]; then
	echo "Error: unable to attach $driver to $dev_sbdf! Exiting!"
	exit 1
    fi
}

probe_pci_devices() {
    echo "load $SCD_PCIDRV.."
    modprobe "$SCD_PCIDRV"

    sleep 1
    if [ ! -e "${SYSFS_PCI_DRIVERS}/${SCD_PCIDRV}" ]; then
        echo "Error: unable to load $SCD_PCIDRV driver! Exiting!"
        exit 1
    fi

    pci_add_new_id "$SCD_PCIDRV" "$SCD_PCI_DEVID" "$SCD_PCI_SBDF"

    pci_add_new_id "$SCD_PCIDRV" "$ROOK_PCI_DEVID" "$ROOK_PCI_SBDF"
}

auxdev_new() {
    cdev_path="$1"
    dev_name="$2"
    inst_id="$3"
    csr_offset="$4"
    shift 4

    "$FBIOB_UTIL_CMD" add "$dev_name" "$inst_id" --cdev-path "$cdev_path" \
	              -c "$csr_offset" $@
}

scd_auxdev_add() {
    dev_name="$1"
    inst_id="$2"
    csr_offset="$3"
    shift 3

    auxdev_new "$SCD_CHARDEV" "$dev_name" "$inst_id" "$csr_offset" $@
}

rook_auxdev_add() {
    dev_name="$1"
    inst_id="$2"
    csr_offset="$3"
    shift 3

    auxdev_new "$ROOK_CHARDEV" "$dev_name" "$inst_id" "$csr_offset" $@
}

scd_i2c_bus_init() {
    reg_base=0x8000
    reg_size=0x80
    num_channels=8

    scd_auxdev_add "i2c_master" 1 0x8080 --i2c-chan-num "$num_channels"
}

scd_wdt_init() {
    scd_auxdev_add "watchdog_darwin" 0 0x120
    scd_auxdev_add "watchdog_darwin" 1 0x304
}

rook_i2c_bus_init() {
    reg_base=0x8000
    reg_size=0x80
    num_channels=4

    rook_auxdev_add "i2c_master" 0 0x8000 --i2c-chan-num "$num_channels"
    rook_auxdev_add "i2c_master" 2 0x8100 --i2c-chan-num "$num_channels"
    rook_auxdev_add "i2c_master" 3 0x8180 --i2c-chan-num "$num_channels"
}

probe_pci_devices

scd_i2c_bus_init
scd_wdt_init

rook_i2c_bus_init