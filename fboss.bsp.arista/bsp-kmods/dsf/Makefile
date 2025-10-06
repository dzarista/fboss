#!/bin/make -f
# SPDX-License-Identifier: GPL-2.0+
# Copyright (c) Meta Platforms, Inc. and affiliates.

obj-m += dsf-fan-cpld.o
obj-m += decker-cpld.o
obj-m += scd-vcpld.o
obj-m += scd-adc.o
dsf-fan-cpld-objs := dsf-fan-cpld-i2c.o ../lib/fan-cpld-i2c.o
decker-cpld-objs := decker-cpld-i2c.o ../lib/regbit-sysfs.o
scd-vcpld-objs := scd-vcpld-i2c.o
