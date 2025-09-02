#!/bin/make -f
# SPDX-License-Identifier: GPL-2.0+
# Copyright (c) Meta Platforms, Inc. and affiliates.

PWD := $(shell pwd)

subdir-ccflags-y += -I${M}/lib -I${M}/backports
subdir-ccflags-y += -DBSP_VERSION=\"${BSP_VERSION}\"

obj-m += scd.o
scd-objs := scd-pci.o lib/fbiob-auxdev.o lib/fbiob-cdev.o lib/regbit-sysfs.o scd-reload-cause-pci.o
obj-m += scd-info.o
scd-info-objs := scd-info-aux.o lib/regbit-sysfs.o
obj-m += scd-smbus.o
obj-m += scd-leds.o
obj-m += scd-xcvr.o
obj-m += scd-spi.o
obj-m += aucd9000.o

# Backported drivers
obj-y += backports/

# Device drivers for Viper and Whistler
obj-y += dsf/

#Device drivers for Darwin.
obj-y += darwin/

#Device drivers for QuickSilver.
obj-y += glath05a-64o/

KDIR ?= /lib/modules/${BUILD_KERNEL}/build

kmods:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

install: kmods
	$(MAKE) INSTALL_MOD_DIR=fboss-kmods -C $(KDIR) M=$(PWD) modules_install

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean
