#!/bin/sh

KMOD_DRIVERS=(
    amax5970
    aslg4f4527
    blackhawk_cpld
    bp4a_lm90
    bp4a_max1363
    decker_cpld
    dsf_fan_cpld
    rook_fan_cpld
    scd
    scd_leds
    scd_smbus
    scd_spi
    scd_watchdog_darwin
    scd_xcvr
)

KMOD_SHARED=(
    scd
)

kmod_is_loaded() {
    kmod="$1"

    if lsmod | grep "$kmod" > /dev/null 2>&1; then
        return 0
    fi

    return 1
}

kmod_remove_all() {
    for kmod in "${KMOD_DRIVERS[@]}"; do
        if kmod_is_loaded "$kmod"; then
            echo "rmmod $kmod.."
            rmmod "$kmod"
        fi
    done

    for kmod in "${KMOD_SHARED[@]}"; do
        if kmod_is_loaded "$kmod"; then
            echo "rmmod $kmod.."
            rmmod "$kmod"
        fi
    done
}

warn_and_confirm() {
    if [ "$1" = "-f" ] || [ "$1" = "--force" ]; then
        return 0
    fi

    echo "Warning: all the BSP kernel modules will be unloaded!"
    read -r -t 10 -p "Do you wish to continue? [y/N]: " user_input
    if [ "$user_input" != "y" ] && [ "$user_input" != "Y" ] ; then
        echo ""
        echo "Task cancelled. Exiting now."
        exit 0
    fi
}

#
# Main entry
#

warn_and_confirm "$1"
kmod_remove_all
