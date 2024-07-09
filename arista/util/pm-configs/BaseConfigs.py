# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from tools import I2cDeviceConfig, SlotConfig, PciDeviceConfig, I2cAdapterConfig, \
   EmbeddedSensorConfig

class Platform:
   
   ROOT_PM_UNIT_NAME = "SCM"

   I2C_ADAPTERS_FROM_CPU = [
      { "adapter" : "SMBus I801 adapter at 1000" }
   ]

   KMODS_SETTINGS_DICT = {
      "bspKmodsRpmName": "arista_bsp_kmods",
      "bspKmodsRpmVersion": "0.7.2-1",
      "bspKmodsToReload" : 
         "scd-xcvr, scd-spi, scd-leds, scd-smbus, dsf-fan-cpld, decker-cpld",
      "sharedKmodsToReload": "scd",
      "upstreamKmodsToLoad": "spidev, i2c-i801"
   }


class PmUnit:

   I2C_DEVICE_CONFIGS = []
   OUTGOING_SLOT_CONFIGS = []
   PCI_DEVICE_CONFIGS = []
   I2C_ADAPTER_CONFIGS = []
   SPI_MASTER_CONFIGS = []
   XCVR_CONFIGS = []
   LED_CONFIGS = []
   EMBEDDED_SENSORS_CONFIGS = []
   SYMBOLIC_LINK_TO_DEVICE_PATH = {}


class SCMUnit( PmUnit ):

   PM_UNIT_NAME = "SCM"

   I2C_DEVICE_CONFIGS = [
      I2cDeviceConfig( "SCM_I2C_MASTER0@0", "0x40", "pmbus", "SCM_MPS_PMBUS" ),
      I2cDeviceConfig( "SCM_I2C_MASTER0@1", "0x50", "24c512", "SCM_IDPROM_P1", 
                     hasCpuMac=True ),
      I2cDeviceConfig( "SCM_I2C_MASTER0@2", "0x30", "pxm1310", "SCM_PXM1310_1" ),
      I2cDeviceConfig( "SCM_I2C_MASTER0@2", "0x3e", "pxe1610", "SCM_PXE1211" ),
      I2cDeviceConfig( "SCM_I2C_MASTER0@2", "0x40", "pxm1310", "SCM_PXM1310_2" )
   ]

   OUTGOING_SLOT_CONFIGS = [
      SlotConfig(
         slotName="SMB_SLOT@0",
         outgoingI2cBusNames=[ "SCM_I2C_MASTER1@0", 
                                 "SCM_I2C_MASTER1@2",
                                 "SCM_I2C_MASTER1@3" ]
      )
   ]

   PCI_DEVICE_CONFIGS = [
      PciDeviceConfig( "SCM_FPGA", "0x3475", "0x0001", "0x3475", "0x0008" )
   ]

   I2C_ADAPTER_CONFIGS = [
      I2cAdapterConfig( "SCM_FPGA", "SCM_I2C_MASTER0", "i2c_master", -1, "0x8000", 8 ),
      I2cAdapterConfig( "SCM_FPGA", "SCM_I2C_MASTER1", "i2c_master", -1, "0x8080", 8 )
   ]
   
   EMBEDDED_SENSORS_CONFIGS = [
      EmbeddedSensorConfig( pmUnitScopedName="CPU_CORE_TEMP", 
                           sysfsPath="/sys/bus/platform/devices/coretemp.0" )
   ]


class SMBUnit( PmUnit ):
   
   PM_UNIT_NAME = "SMB"


class PSUUnit( PmUnit ):

   PM_UNIT_NAME = "PSU"


class FANUnit( PmUnit ):

   PM_UNIT_NAME = "FAN"