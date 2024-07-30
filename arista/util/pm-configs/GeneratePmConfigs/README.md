# FBOSS OSS Platform Manager Config Generation Tool

Copyright (C) 2024 Arista Networks, Inc.

## Purpose

This directory contains code for defining a Python-based hardware description of 
a specific platform and automatically generating the contents of 
`platform_manager.json` config files living [here](https://github.com/aristanetworks/arista-fboss/tree/main/fboss/platform/configs). 

Structure of the PM config file is defined by Meta in the following [thrift file](https://github.com/aristanetworks/arista-fboss/blob/5fd2a0a0a4165937cb174a1ff5d5bb23c394d1cb/fboss/platform/platform_manager/platform_manager_config.thrift).

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
an object of the given class (child of `PlatformConfig`) and generates the JSON config
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

Additionally, if multiple platforms share the same specifications of a single
PM unit, that can also be defined in `BaseConfigs.py` to allow for more code
reusability. For example, both `Viper` and `Whistler` platforms share the FairyWren
CPU card, so we define a `SCMFairyWren` class that inherits from `SCMUnit`, and later
we only have to configure the specific outgoing slot configs in `ViperSCM` and
`WhistlerSCM`.

### I2c Device Config

`I2cDeviceConfig` defines devices connected to FPGAs (Pci devices) through I2c buses.
The `busName` is a key attribute of this config, and there are generally two ways of
defining it based on whether the source FPGA and the I2c device are within the same
PM unit or not.
- If the I2c device is within a different PM unit (e.g. SMB Idprom connected to the
SCM FPGA), you must specify an optional argument `incomingBusIndex` in the config 
initialization, which will then create the PM unit scoped bus name in the form
`INCOMING@<incomingBusIndex>`.
- If both devices are within the same PM unit, there is no need to specify this
argument. Instead, the device should be mapped to a specific buses using the 
`addI2cDevices` method of the `I2cBus` class. This will automatically infer the 
`busName` attribute from the bus object, since they are within the same scope.

For the purpose of symbolic link to device path generation, we define some more 
specific device types on top of the base `I2cAdapterConfig` class:

- `FANCpld`: Specific definition for any FAN CPLD. The reason for such a distinction is
that there are two different symbolic links defined for each FAN CPLD, unlike for any
other device.
- `SMBCpld`: Specific definition for any CPLD in the SMB unit. Different rules apply
compared to FAN CPLD, only one symbolic link is defined.
- `SCMIdProm`: Specific definition for IdProm in the SCM unit. Symbolic link naming
convention is different from all the other devices.
- `GpioChip`: Any device that is of the GpioChip type. Different symbolic link naming
applies.
- `PSUBus`: Specific definition for any PSU bus. This is a special case since there can
be multiple physical PSU buses connected to another PM unit, even though we would
only have one such definition in the PSU PM unit config.
- `Sensor`: If a device does not fit any of the previous categories, it should most
likely be classified as sensor, which will apply a more generic naming convention.

### Pci Device Config

`PciDeviceConfig` is used to define FPGAs on the platform. This class has a few 
methods that are worth exploring in more detail:

- `addI2cAdapterConfigs`: This method adds corresponding I2c adapter configs to the
FPGA. However, unlike some adder methods, this one abstracts away the actual
initialization of `I2cAdapterConfig` classes from the user. The user must simply
specify the following:
    - `numAdapters`: How many adapters to create
    - `adapterBaseName`: There are three different options here. 
    1. If we're defining a single master for a PM unit with just one FPGA, the name
    can simply reflect the name of that adapter, such as `SCM_I2C_MASTER`.
    2. If we're defining multiple masters for a PM unit with one FPGA, (e.g. Viper 
    SMB), the base name will contain one format specifier for the master index as so:
    `SMB_I2C_MASTER{}`.
    3. If we have multiple masters and also multiple FPGAs within a single PM unit
    (e.g. Whistler SMB), we need to include two format specifiers for the FPGA index
    as well as the master index, respectively: `SMB_FPGA{}_I2C_MASTER{}`.
    - `baseCsrOffset`: Base offset of the first adapter. Subsequent adapters are
    created with 0x80 spacing.
- `addXcvrCtrlConfigs`: This method adds corresponding transceiver configs to the 
FPGA. Since there can be potentially hundreds of transceiver configs needed for one
platform, the process of defining these is highly automated. The user needs to 
specify the following:
    - `numConfigs`: How many configs to create
    - `basePortNumber`: Port number from which to start numbering configs
    - `portType`: Usually OSFP or QSFP
    - `xcvrBaseOffset`: Base xcvr offset of the first config. Subsequent configs are
    created with 0x10 spacing.
    - `ledBaseOffset`: Each transceiver has up to 4 LEDs, created with 0x10 spacing.
    - `ledsPerXcvr`: How many LEDs should be created per transceiver. Default is 2,
    which works for Viper and Whistler so far.
    - `portNumberSkipStep`: Most tricky parameter to specify. For some systems like
    Whistler, the port numbers controlled by a specific FPGA devices are not all
    sequential but include certain jumps (e.g. `SMB_FPGA0` controls ports 1, 2, 3, 4,
    9, 10, 11, 12, 17, 18, 19, 20, etc). This parameter specifies how big the "jump"
    is, and consequently, how many port numbers in a row to create. Default is 1, which
    means fully sequential numbering.

In addition, there is a helper function called `enumeratePciDeviceConfigs`, which
automates the definition of multiple FPGAs within one PM unit by only specifying the
general device name with an optional format specifier for the FPGA numbering.

### I2c Adapter Config

`I2cAdapterConfig` is used to define adapters connecting Pci devices and I2c devices
through buses. Each adapter config has an attribute `buses`, which is a list
containing `I2cBus` objects. As mentioned before, `I2cDeviceConfig` objects can
therefore be mapped to specific `I2cBus` objects.

### Other config classes

- `EmbeddedSensorConfig`: Config class for devices such as the core temperature 
sensor on the CPU.
- `I2cBus`: Defines a specific bus of an I2c adapter. Supports the use of `addI2cDevices`
method to map to I2c devices on the same PM unit.
- `InitRegSettings`: Config class for initial register settings of an I2c device. Used 
for example to overwrite default max temperature values on several sensors.
- `SlotConfig`: Config class for defining outgoing slot configs. In general, the largest
number of outgoing slot configs is of type FAN. Hence, there is a helper function
called `enumerateFANSlotConfigs` for defining these efficiently.
- `SlotTypeConfig`: Although this class is defined within `PlatformConfig` in the original
[thrift file](https://github.com/aristanetworks/arista-fboss/blob/5fd2a0a0a4165937cb174a1ff5d5bb23c394d1cb/fboss/platform/platform_manager/platform_manager_config.thrift#L463), we define it as a property of `PmUnitConfig`, since
every PM unit generally has just one type of slot type config associated with it.
- `SpiMasterConfig`: Config class for Spi master associated with a specific FPGA.
- `SpiDeviceConfig`: Config class for Spi device connected to a specific Spi master.
For the purpose of symbolic link to device path generation, we also define a more 
specific child class called `Flash.`
- `XcvrConfig`: Config class for transceivers mapped to a spefific FPGA. Process of
defining these configs is more closelly described above.
- `LedConfig`: Apart from LEDs on transceivers, there are also several special
purpose status LEDs. This config class defines these.

### Symbolic Link to Device Path Generation

The device path of virtually any device (I2C, PCI, Embedded Sensor, Xcvr, etc.) 
or I2C bus can be generated using the helper functions `constructDevicePaths` 
and `constructBusPaths`, respectively. These functions return a list that generally
only contains one item, unless a given device is found in multiple physical PM units
across the platform (for example, `Whistler` has 4 PSU slots, so the function will
return a list of 4 different device paths when passed the PSUBus device as a
parameter).

## Technicalities

So far, the PM config generation tool assumes existence of platforms with
a single SCM unit and SMB unit only. Although the device path generation functions
would correctly return multiple paths if there were (for example) 2 SMB units, there
is no precedent established for symbolic link naming conventions in such a case.

Notice that most config classes in `BaseConfigs.py` do not allow the user to specify
child configs directly in the class constructor (for example, during `PmUnitConfig`
initialization we only specify the PM unit name but none of the other configs such as
associated `PciDeviceConfigs`). Instead, there is a dedicaded adder method for each
of the children configs. This is a design choice rather than a bug, and has to do
with the fact that the adder methods create pointers from the child configs back
to its parent config, which are necessary during symbolic link to device path 
generation.

## Testing suite

## Practical example

## How to generate

To generate a PM config for a specific platform, run
```
python3 -m Platforms.<platform_name> > platform_manager.json
```
from the `GeneratePmConfigs` directory.