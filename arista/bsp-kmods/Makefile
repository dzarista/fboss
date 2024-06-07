#!/bin/make -f
# SPDX-License-Identifier: GPL-2.0+
# Copyright (c) Meta Platforms, Inc. and affiliates.

ccflags-y += -I${M}/lib

scd-objs := scd-pci.o lib/fbiob-auxdev.o lib/fbiob-cdev.o
obj-m += scd.o
obj-m += scd-smbus.o
obj-m += scd-leds.o
obj-m += scd-xcvr.o
obj-m += scd-spi.o

obj-m += i2c_dev_sysfs.o
obj-m += decker-cpld.o
obj-m += dsf-fan-cpld.o

KDIR ?= /lib/modules/${BUILD_KERNEL}/build

PWD := $(shell pwd)

kmods:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

install: kmods
	$(MAKE) INSTALL_MOD_DIR=fboss-kmods -C $(KDIR) M=$(PWD) modules_install

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean