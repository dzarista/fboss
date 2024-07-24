# FBOSS OSS Platform Manager Config Generation Tool

Copyright (C) 2024 Arista Networks, Inc.

## Purpose

This directory contains code for defining a Python-based hardware description of 
a specific platform and automatically generating the contents of 
`platform_manager.json` config files living in 
`arista-fboss/fboss/platform/configs/<platform_name>`.

## How to build

All Python objects necessary to build an internal representation of a platform are
defined in `BaseConfigs.py`. In order to define hardware description for a platform
not yet supported, create a new file Python file in `Platforms` directory with the
platform name. 

## Overview of major building blocks

### Platform Config

The `PlatformConfig` object represents the highest level of abstraction and provides
full hardware description of a given platform. All platform-specific classes
(e.g. `Viper` and `Whistler`) must inherit from `PlatformConfig`, because it also 
pre-defines some features common to all platforms supported so far. If a new platform
does not share these features, they have to be overwritten in the child class.

Every platform-specific file should define a `main` function that simply instantiates
an object of the given class (child of `PlatformConfig`)and generates the JSON config
by calling the overloaded `.asJson()` method.

### PM Unit Config

Vast majority of the config is PM unit focused. This provides higher dedgree of code
reusability in case multiple platforms share similar PM unit configurations;
the overarching idea is that the PlatformConfig can be created by "glueing together"
multiple standalone PM units (by using the `addPmUnitConfigs` function) with minimal
work required to specify how to connect these units.

When defining a new platform, standard approach is to take existing base classes
(`SCMUnit`, `SMBUnit`, `PSUUnit`, `FANUnit`) and define platform-specific PM unit
config classes on top of them (e.g. `ViperSCM`). If a platform's does not have any
additional configurations, one can simply use the base class definition.

### I2C Device Config

Below are some of the more specific device types defined on top of the base 
`I2cAdapterConfig` class. The purpose of having a more granular definition of some
of the devices is mostly to automate symbolic link to device path generation.

`FANCpld`: Specific definition for any FAN CPLD. The reason for such a distinction is
that there are two different symbolic links defined for each FAN CPLD, unlike for any
other device.

`SMBCpld`: Specific definition for any CPLD in the SMB unit. Different rules apply
compared to FAN CPLD, only one symbolic link is defined.

`SCMIdProm`: Specific definition for IdProm in the SCM unit. Symbolic link naming
convention is different from all the other devices.

`GpioChip`: Any device that is of the GpioChip type. Different symbolic link naming
applies.

`Sensor`: If a device does not fit any of the previous categories, it should most
likely be classified as sensor, which will apply the more generic naming conventions.

## How to generate

To generate a PM config for a specific platform, run
```
python3 -m Platforms.<platform_name> > platform_manager.json
```
from the `GeneratePmConfigs` directory.