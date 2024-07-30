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
- If the I2c device is within a different PM unit (e.g. SMB IdProm connected to the
SCM FPGA), you must specify an optional argument `incomingBusIndex` in the config 
initialization, which will then create the PM unit scoped bus name in the form
`INCOMING@<incomingBusIndex>`.
- If both devices are within the same PM unit, there is no need to specify this
argument. Instead, the device should be mapped to a specific bus using the 
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
FPGA. However, unlike some other adder methods, this one abstracts away the actual
initialization of `I2cAdapterConfig` classes from the user. The user must simply
specify the following:
    - `numAdapters`: How many adapters to create
    - `adapterBaseName`: There are two different options here. 
    1. If we're defining adapters for a PM unit with a single FPGA, (e.g. Viper 
    SMB), the base name will contain one format specifier for the master index as so:
    `SMB_I2C_MASTER{}`.
    2. If we have multiple FPGAs within a single PM unit
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
containing `I2cBus` objects. As mentioned above, `I2cDeviceConfig` objects can
therefore be mapped to specific `I2cBus` objects.

### Other config classes

- `EmbeddedSensorConfig`: Config class for devices such as the core temperature 
sensor on the CPU.
- `I2cBus`: Defines a specific bus of an I2c adapter. Supports the use of `addI2cDevices`
method to map to I2c devices on the same PM unit.
- `InitRegSettings`: Config class for initial register settings of an I2c device. Used 
for example to overwrite default max temperature values on several sensors.
- `SlotConfig`: Config class for defining outgoing slot configs. In general, the largest
number of outgoing slot configs is of type FAN. Hence, there is also a helper function
called `enumerateFANSlotConfigs` for defining these efficiently.
- `SlotTypeConfig`: Although this object belongs within `PlatformConfig` in the original
[thrift file](https://github.com/aristanetworks/arista-fboss/blob/5fd2a0a0a4165937cb174a1ff5d5bb23c394d1cb/fboss/platform/platform_manager/platform_manager_config.thrift#L463), we define it as a property of `PmUnitConfig`, since
every PM unit generally has just one type of slot type config associated with it.
- `SpiMasterConfig`: Config class for Spi master associated with a specific FPGA.
- `SpiDeviceConfig`: Config class for Spi device connected to a specific Spi master.
For the purpose of symbolic link to device path generation, we also define a more 
specific child class called `Flash`.
- `XcvrConfig`: Config class for transceivers mapped to a spefific FPGA. Process of
defining these configs is more closelly described above.
- `LedConfig`: Apart from LEDs on transceivers, there are also several special
purpose status LEDs, which are defined by this class.

### Symbolic Link to Device Path Generation

While symbolic link naming conventions have to be hardcoded to a certain extent, the
device path of virtually any device (I2c, Pci, Embedded Sensor, Xcvr, etc.) 
or I2c bus can be generated using the helper functions `constructDevicePaths` 
and `constructBusPaths`, respectively. These functions return a list that generally
only contains one item, unless a given device is found in multiple physical PM units
across the platform (for example, `Whistler` has 4 PSU slots, so the function will
return a list of 4 different device paths when passed the PSUBus device as a
parameter).

In order to actually generate all symbolic links to device paths, after defining all
necessary devices in your platform file, remember to include this code block:
```python
for pmConfig in self.pmUnitConfigs:
    pmConfig.populateSymlinkToDevicePaths()
```
## Additional technicalities

- So far, the PM config generation tool assumes existence of platforms with
a single SCM unit and SMB unit only. Although the device path generation functions
would correctly return multiple paths if there were (for example) 2 SMB units, there
is no precedent established for symbolic link naming conventions in such a case.
- Notice that most config classes in `BaseConfigs.py` do not allow the user to specify
child configs directly in the class constructor (for example, during `PmUnitConfig`
initialization we only specify the PM unit name but none of the other configs such as
associated `PciDeviceConfigs`). Instead, there is a dedicaded adder method for each
of the child configs. This is a design choice, and has to do
with the fact that the adder methods create pointers from the child configs back
to its parent config, which are necessary during symbolic link to device path 
generation.

## Testing suite

In order to test whether the config classes and functions defined in `BaseConfigs.py`
behave as expected, there is a breadth test suite `ConfigTests.py` available.
We are using the [Coverage.py](https://coverage.readthedocs.io/en/7.6.0/) tool to
validate that our test suite achieves 100% coverage on the `BaseConfigs.py` file. In
the future, if new features are added to the config generation tool, please also include
corresponding tests to make sure the test coverage stays up to date.

After pip installing the `coverage` module, the test suite can be typically invoked
using the command `coverage run -m ConfigTests`, and subsequently running 
`coverage report -m` to display the coverage statistics. For more sophisticated use
cases, please refer to the package documentation.

## Practical example

Below, see a relatively simple example supposed to illustrate the general approach to
defining a new config for a fictional platform called `Eagle`. We will first define
our PM units separately and later connect them together in the main platform class.

### Step-by-step

Let's start with the SCM unit. We will define a class `EagleSCM` that inherits from
`SCMUnit`.

```python
class EagleSCM( SCMUnit ):
    def __init__( self ):
        super().__init__()
```
Specify the SCM slot type config, filling in information about the SCM IdProm.
```python
        self.setSlotTypeConfig(
            idPromConfigBusName="SMBus I801 adapter at 1000",
            idPromConfigAddress="0x50",
            idPromConfigKernelDeviceName="24c512",
            idPromConfigOffset=15360
        ) 
```
Our SCM unit will have just one I2c device and that is the SCM IdProm. Add it to the
list of i2cDeviceConfigs by using the `addI2cDevices` adder method.
```python
        scmIdProm = SCMIdProm( "0x50", "24c512", "SCM_IDPROM_P1", hasCpuMac=True )
        self.addI2cDevices( [ scmIdProm ] )
```
Let's add one FPGA device by using the `addPciDeviceConfigs` method.
```python
        scmFpga = PciDeviceConfig( "SCM_FPGA", "0x3475", "0x0001", "0x3475", "0x0008" )
        self.addPciDeviceConfigs( [ scmFpga ] )
```
Next, add an I2c adapter on our FPGA and connect the SCM IdProm device defined above
to I2c bus `SCM_I2C_MASTER0@1`.
```python
        scmFpga.addI2cAdapterConfigs( 1, "SCM_I2C_MASTER{}", "0x8000" )
        
        scmI2cMaster0 = scmFpga.i2cAdapterConfigs[ 0 ]
        scmI2cMaster0.buses[ 1 ].addI2cDevices( [ scmIdProm ] )
```
Finally, define outgoing slot that will specify how the SCM and SMB units are connected.
We will have two outgoing buses, `SCM_I2C_MASTER0@3` and `SCM_I2C_MASTER0@4`. Notice that
instead of specifying the names, we simply reference the bus objects created as part of
the I2c adapter config.
```python
        self.addOutgoingSlotConfigs( [
            SlotConfig(
                slotName="SMB_SLOT@0",
                outgoingI2cBuses=[ 
                    scmI2cMaster0.buses[ 3 ],
                    scmI2cMaster0.buses[ 4 ]
                ]
            )
        ] )
```
Now, let's move on to the SMB unit. Similarly, we define a `EagleSMB` class that inherits
from `SMBUnit`.
```python
class EagleSMB( SMBUnit ):
    def __init__( self ):
        super().__init__()
```
Specify the SMB slot type config. Notice that the number of outgoing I2c buses should
be equal to the number of buses specified within the `SMB_SLOT@0` config in `EagleSCM`.
```python
        self.setSlotTypeConfig(
            numOutgoingI2cBuses=2,
            idPromConfigBusName="INCOMING@0",
            idPromConfigAddress="0x50",
            idPromConfigKernelDeviceName="24c512",
            idPromConfigOffset=15360
        )
```
Our SMB unit will have two I2c devices, one of type `GpioChip` and one of the more
generic type `Sensor`.
```python
        smbPca = GpioChip( "0x74", "pca9539", "SMB_PCA", incomingBusIndex=0 )
        smbTmp75 = Sensor( "0x49", "tmp75", "SMB_TMP75", incomingBusIndex=1,
                            initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) )
        self.addI2cDeviceConfigs( [ smbPca, smbTmp75 ] )
```
Let's add two FPGAs to demonstrate how to use `enumeratePciDeviceConfigs`.
```python
        self.addPciDeviceConfigs( [
            *enumeratePciDeviceConfigs( 2, "SMB_FPGA{}", "0x3475", "0x0001", 
                                        "0x3475", "0x0003" )
        ] )
        smbFpga0 = self.pciDeviceConfigs[ 0 ]
        smbFpga1 = self.pciDeviceConfigs[ 1 ]
```
On each FPGA, we will add two adapters, demonstrating how the adder method parses
the base adapter name format string.
```python
        smbFpga0.addI2cAdapterConfigs( 2, "SMB_FPGA{}_I2C_MASTER{}", "0x8000" )
        smbFpga1.addI2cAdapterConfigs( 2, "SMB_FPGA{}_I2C_MASTER{}", "0x8000" )
```
Now, let's add transceiver configs. Here, we assume that our platform uses the
more sophisticated port number layout with jumps. Hence, we expect `SMB_FPGA0` to map
to port numbers 1, 2, 3, 4, 9, 10, 11, 12, while `SMB_FPGA1` should map to 5, 6, 7, 8,
13, 14, 15, 16. You can verify that by generating the PM config later.
```python 
        smbFpga0.addXcvrCtrlConfigs( numConfigs=8, basePortNumber=1, portNumberSkipStep=4 )
        smbFpga1.addXcvrCtrlConfigs( numConfigs=8, basePortNumber=5, portNumberSkipStep=4 )
```
Finally, let's add two PSU slots and map them to buses `SMB_FPGA0_I2C_MASTER1@5` and
`SMB_FPGA1_I2C_MASTER1@5`, respectively.
```python
        smbFpga0Master1 = smbFpga0.i2cAdapterConfigs[ 1 ]
        smbFpga1Master1 = smbFpga1.i2cAdapterConfigs[ 1 ]
        self.addOutgoingSlotConfigs( [
            SlotConfig(
                slotName="PSU_SLOT@0",
                presenceFileName="psu1_prsnt",
                presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
                outgoingI2cBuses=[ smbFpga0Master1.buses[ 5 ] ]
            ),
            SlotConfig(
                slotName="PSU_SLOT@1",
                presenceFileName="psu2_prsnt",
                presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
                outgoingI2cBuses=[ smbFpga1Master1.buses[ 5 ] ]
            )
        ] )
```
As our last step, we must define the main platform class.
```python
class Eagle( PlatformConfig ):
    def __init__( self ):
        super().__init__( "eagle" )
```
Add the SCM and SMB units defined above, along with generic PSU and FAN units. Note
that the generic PSU unit definition already includes a `PSUBus` device definition.
```python
        self.addPmUnitConfigs( [
            EagleSCM(),
            EagleSMB(),
            PSUUnit(),
            FANUnit()
        ] )
```
Use the corresponding adder method to specify I2c adapters leading from the CPU.
```python
        self.addI2cAdaptersFromCpu( [ "SMBus I801 adapter at 1000" ] )
```
Don't forget to invoke the `populateSymlinkToDevicePaths` method for all added PM units
to make sure that symbolic link to device paths are created.
```python
        for pmConfig in self.pmUnitConfigs:
            pmConfig.populateSymlinkToDevicePaths()
```
To generate the PM config file, we will add the following main function.
```python
def main():
   platform = Eagle()
   print( platform.asJson() )

if __name__ == '__main__':
   main()
```

### Resulting config file

By putting all pieces together, we obtain the following config file `Eagle.py`. Notice that we also
added all necessary imports from `BaseConfigs.py`.

```python
from BaseConfigs import (
   enumeratePciDeviceConfigs,
   FANUnit,
   GpioChip,
   InitRegSettings,
   PciDeviceConfig,
   PlatformConfig,
   PSUUnit,
   SCMIdProm,
   SCMUnit,
   Sensor,
   SMBUnit,
   SlotConfig
)


class EagleSCM( SCMUnit ):
    def __init__( self ):
        super().__init__()

        self.setSlotTypeConfig(
            idPromConfigBusName="SMBus I801 adapter at 1000",
            idPromConfigAddress="0x50",
            idPromConfigKernelDeviceName="24c512",
            idPromConfigOffset=15360
        ) 

        scmIdProm = SCMIdProm( "0x50", "24c512", "SCM_IDPROM_P1", hasCpuMac=True )
        self.addI2cDeviceConfigs( [ scmIdProm ] )

        scmFpga = PciDeviceConfig( "SCM_FPGA", "0x3475", "0x0001", "0x3475", "0x0008" )
        self.addPciDeviceConfigs( [ scmFpga ] )

        scmFpga.addI2cAdapterConfigs( 1, "SCM_I2C_MASTER{}", "0x8000" )
        
        scmI2cMaster0 = scmFpga.i2cAdapterConfigs[ 0 ]
        scmI2cMaster0.buses[ 1 ].addI2cDevices( [ scmIdProm ] )

        self.addOutgoingSlotConfigs( [
            SlotConfig(
                slotName="SMB_SLOT@0",
                outgoingI2cBuses=[ 
                    scmI2cMaster0.buses[ 3 ],
                    scmI2cMaster0.buses[ 4 ]
                ]
            )
        ] )


class EagleSMB( SMBUnit ):
    def __init__( self ):
        super().__init__()

        self.setSlotTypeConfig(
            numOutgoingI2cBuses=2,
            idPromConfigBusName="INCOMING@0",
            idPromConfigAddress="0x50",
            idPromConfigKernelDeviceName="24c512",
            idPromConfigOffset=15360
        )

        smbPca = GpioChip( "0x74", "pca9539", "SMB_PCA", incomingBusIndex=0 )
        smbTmp75 = Sensor( "0x49", "tmp75", "SMB_TMP75", incomingBusIndex=1,
                            initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) )
        self.addI2cDeviceConfigs( [ smbPca, smbTmp75 ] )

        self.addPciDeviceConfigs( [
            *enumeratePciDeviceConfigs( 2, "SMB_FPGA{}", "0x3475", "0x0001", 
                                        "0x3475", "0x0003" )
        ] )
        smbFpga0 = self.pciDeviceConfigs[ 0 ]
        smbFpga1 = self.pciDeviceConfigs[ 1 ]

        smbFpga0.addI2cAdapterConfigs( 2, "SMB_FPGA{}_I2C_MASTER{}", "0x8000" )
        smbFpga1.addI2cAdapterConfigs( 2, "SMB_FPGA{}_I2C_MASTER{}", "0x8000" )

        smbFpga0.addXcvrCtrlConfigs( numConfigs=8, basePortNumber=1, portNumberSkipStep=4 )
        smbFpga1.addXcvrCtrlConfigs( numConfigs=8, basePortNumber=5, portNumberSkipStep=4 )

        smbFpga0Master1 = smbFpga0.i2cAdapterConfigs[ 1 ]
        smbFpga1Master1 = smbFpga1.i2cAdapterConfigs[ 1 ]
        self.addOutgoingSlotConfigs( [
            SlotConfig(
                slotName="PSU_SLOT@0",
                presenceFileName="psu1_prsnt",
                presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
                outgoingI2cBuses=[ smbFpga0Master1.buses[ 5 ] ]
            ),
            SlotConfig(
                slotName="PSU_SLOT@1",
                presenceFileName="psu2_prsnt",
                presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
                outgoingI2cBuses=[ smbFpga1Master1.buses[ 5 ] ]
            )
        ] )


class Eagle( PlatformConfig ):
    def __init__( self ):
        super().__init__( "eagle" )

        self.addPmUnitConfigs( [
            EagleSCM(),
            EagleSMB(),
            PSUUnit(),
            FANUnit()
        ] )

        self.addI2cAdaptersFromCpu( [ "SMBus I801 adapter at 1000" ] )

        for pmConfig in self.pmUnitConfigs:
            pmConfig.populateSymlinkToDevicePaths()


def main():
   platform = Eagle()
   print( platform.asJson() )

if __name__ == '__main__':
   main()
```
Note that in general, we use variable names to reference config objects rather than
indexing through multiple lists to grab the object we need. This makes the code less
prone to errors in case configs need to be modified in the future. However, when adding
objects that have no reference in further code, it is acceptable to omit creating
a variable and to simply initialize the object within the corresponding adder method.

## How to generate

To generate a PM config for a specific platform, run
```
python3 -m Platforms.<platform_name> > platform_manager.json
```
So for the practical example above you can generate a config file by executing
```
python3 -m Platforms.Eagle > platform_manager.json
```
from the `GeneratePmConfigs` directory, assuming you saved the config file as `Platforms/Eagle.py`.