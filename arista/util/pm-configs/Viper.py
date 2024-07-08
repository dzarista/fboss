# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from tools import SlotTypeConfig, I2cDeviceConfig, SlotConfig, PciDeviceConfig, \
   I2cAdapterConfig, SpiMasterConfig, XcvrConfig, LedConfig, EmbeddedSensorConfig, \
   enumerateXcvrConfigs, generateXcvrSymlinks, generateI2cAdapterSymlinks, \
   generateSensorSymlinks, InitRegSettings, SpiDeviceConfig


class PmUnit:

   I2C_DEVICE_CONFIGS = []
   OUTGOING_SLOT_CONFIGS = []
   PCI_DEVICE_CONFIGS = []
   I2C_ADAPTER_CONFIGS = []
   SPI_MASTER_CONFIGS = []
   XCVR_CONFIGS = []
   LED_CONFIGS = []
   EMBEDDED_SENSORS_CONFIGS = []
   SYMBOLIC_LINK_TO_DEVICE_PATH = []


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
      I2cAdapterConfig( "SCM_I2C_MASTER0", "i2c_master", -1, "0x8000", 8 ),
      I2cAdapterConfig( "SCM_I2C_MASTER1", "i2c_master", -1, "0x8080", 8 )
   ]
   
   EMBEDDED_SENSORS_CONFIGS = [
      EmbeddedSensorConfig( pmUnitScopedName="CPU_CORE_TEMP", 
                           sysfsPath="/sys/bus/platform/devices/coretemp.0" )
   ]

   SYMBOLIC_LINK_TO_DEVICE_PATH = {
      "/run/devmap/fpgas/MERU_SCM_CPLD": "/[SCM_FPGA]",
      **generateI2cAdapterSymlinks( I2C_ADAPTER_CONFIGS, "SCM" ),
      "/run/devmap/eeproms/MERU_SCM_EEPROM_P1": "/[SCM_IDPROM_P1]",
      "/run/devmap/eeproms/MERU_SCM_EEPROM": "/[IDPROM]",
      **generateSensorSymlinks( EMBEDDED_SENSORS_CONFIGS, \
                                 I2C_DEVICE_CONFIGS, "SCM" ),
   }


class SMBUnit( PmUnit ):
   
   PM_UNIT_NAME = "SMB"

   I2C_DEVICE_CONFIGS = [
      I2cDeviceConfig( "INCOMING@0", "0x50", "24c512", "SMB_IDPROM" ),
      I2cDeviceConfig( "INCOMING@0", "0x74", "pca9539", "SMB_PCA", 
                        isGpioChip=True ),
      I2cDeviceConfig( "INCOMING@1", "0x49", "tmp75", "SMB_TMP75_FRONT",
                        initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) ),
      I2cDeviceConfig( "INCOMING@1", "0x4A", "tmp75", "SMB_TMP75_REAR",
                        initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) ),
      I2cDeviceConfig( "INCOMING@1", "0x4D", "max6581", "SMB_MAX6581",
                        initRegSettings=InitRegSettings( [
                           ( 32, 110 ),
                           ( 33, -121 ),
                           ( 34, -121 ),
                           ( 35, -121 ),
                           ( 36, -121 ),
                           ( 37, -121 ),
                           ( 38, -121 ),
                           ( 39, -121 )
                        ] ) ),
      I2cDeviceConfig( "SMB_I2C_MASTER0@0", "0x45", "raa228228", 
                        "SMB_RAA228926_J3" ),
      I2cDeviceConfig( "SMB_I2C_MASTER0@0", "0x54", "isl68226", 
                        "SMB_ISL68226_J3" ),
      I2cDeviceConfig( "SMB_I2C_MASTER0@0", "0x55", "isl68226", 
                        "SMB_ISL68226_OPTICS" ),
      I2cDeviceConfig( "SMB_I2C_MASTER0@2", "0x48", "tmp75", "SMB_MGMT_TMP75" ),
      I2cDeviceConfig( "INCOMING@2", "0x48", "tmp75", "FAN_TMP75",
                        initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) ),
      I2cDeviceConfig( "INCOMING@2", "0x60", "pali2_cpld", "FAN_CPLD" )
   ]

   OUTGOING_SLOT_CONFIGS = [
      SlotConfig(
         slotName="PSU_SLOT@0",
         presenceFileName="psu1_present",
         presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
         outgoingI2cBusNames=[ "SMB_I2C_MASTER0@5" ]
      ),
      SlotConfig(
         slotName="PSU_SLOT@1",
         presenceFileName="psu2_present",
         presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
         outgoingI2cBusNames=[ "SMB_I2C_MASTER0@6" ]
      ),
      SlotConfig(
         slotName="FAN_SLOT@0",
         presenceFileName="fan1_present",
         presenceDevicePath="/SMB_SLOT@0/[FAN_CPLD]"
      ),
      SlotConfig(
         slotName="FAN_SLOT@1",
         presenceFileName="fan2_present",
         presenceDevicePath="/SMB_SLOT@0/[FAN_CPLD]"
      ),
      SlotConfig(
         slotName="FAN_SLOT@2",
         presenceFileName="fan3_present",
         presenceDevicePath="/SMB_SLOT@0/[FAN_CPLD]"
      ),
      SlotConfig(
         slotName="FAN_SLOT@3",
         presenceFileName="fan4_present",
         presenceDevicePath="/SMB_SLOT@0/[FAN_CPLD]"
      )
   ]

   PCI_DEVICE_CONFIGS = [
      PciDeviceConfig( "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0003" )
   ]

   I2C_ADAPTER_CONFIGS = [
      I2cAdapterConfig( "SMB_I2C_MASTER0", "i2c_master", -1, "0x8000", 8),
      I2cAdapterConfig( "SMB_I2C_MASTER1", "i2c_master", -1, "0x8080", 8),
      I2cAdapterConfig( "SMB_I2C_MASTER2", "i2c_master", -1, "0x8100", 8),
      I2cAdapterConfig( "SMB_I2C_MASTER3", "i2c_master", -1, "0x8180", 8),
      I2cAdapterConfig( "SMB_I2C_MASTER4", "i2c_master", -1, "0x8200", 8),
      I2cAdapterConfig( "SMB_I2C_MASTER5", "i2c_master", -1, "0x8280", 8),
   ]

   SPI_MASTER_CONFIGS = [
      SpiMasterConfig( "SMB_SPI_MASTER0", "spi_master", -1, "0x7900",
                        spiDeviceConfigs=[ SpiDeviceConfig(
                           pmUnitScopedName="SMB_SPI_MASTER0_DEVICE1",
                           chipSelect=0,
                           modalias="spidev",
                           maxSpeedHz=25000000
                        ) ] )
   ]
   
   XCVR_CONFIGS = [
      *enumerateXcvrConfigs( numConfigs=38, basePortNumber=1, portType="osfp", 
                              xcvrBaseOffset="0xA010", led1BaseOffset="0x6100", 
                              led2BaseOffset="0x6110" ),
      XcvrConfig( portNumber=39, portType="qsfp", xcvrCtrlOffset="0xA290",
                  led1Offset="0x65C0", led2Offset="0x65D0", led3Offset="0x65E0",
                  led4Offset="0x65F0" )
   ]

   LED_CONFIGS = [
      LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
      LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
      LedConfig( ledName="PSU_STATUS_LED", offset="0x6070" ),
      LedConfig( ledName="SMB_STATUS_LED", offset="0x6090" )
   ]

   SYMBOLIC_LINK_TO_DEVICE_PATH = {
      "/run/devmap/eeproms/MERU800BIA_SMB_EEPROM": "/SMB_SLOT@0/[SMB_IDPROM]",
      "/run/devmap/fpgas/MERU800BIA_SMB_FPGA": "/SMB_SLOT@0/[SMB_FPGA]",
      **generateI2cAdapterSymlinks( I2C_ADAPTER_CONFIGS, "SMB" ),
      "/run/devmap/gpiochips/SMB_PCA": "/SMB_SLOT@0/[SMB_PCA]",
      **generateSensorSymlinks( PmUnit.EMBEDDED_SENSORS_CONFIGS, \
                                 I2C_DEVICE_CONFIGS, "SMB" ),
      **generateXcvrSymlinks( XCVR_CONFIGS ),
      "/run/devmap/flashes/SMB_SPI_MASTER0_DEVICE1": \
         "/SMB_SLOT@0/[SMB_SPI_MASTER0_DEVICE1]"
   }


class PSUUnit( PmUnit ):

   PM_UNIT_NAME = "PSU"

   I2C_DEVICE_CONFIGS = [
      I2cDeviceConfig( "INCOMING@0", "0x58", "pmbus", "PSU_PMBUS" )
   ]

   SYMBOLIC_LINK_TO_DEVICE_PATH = {
      "/run/devmap/sensors/PSU1_PMBUS": "/SMB_SLOT@0/PSU_SLOT@0/[PSU_PMBUS]",
      "/run/devmap/sensors/PSU2_PMBUS": "/SMB_SLOT@0/PSU_SLOT@1/[PSU_PMBUS]",
   }


class FANUnit( PmUnit ):

   PM_UNIT_NAME = "FAN"

   SYMBOLIC_LINK_TO_DEVICE_PATH = {
      "/run/devmap/cplds/FAN_CPLD": "/SMB_SLOT@0/[FAN_CPLD]",
   }


class Viper:

   PLATFORM_NAME = "meru800bia"
   ROOT_PM_UNIT_NAME = "SCM"

   SLOT_TYPE_CONFIGS = [
      SlotTypeConfig( 
         slotName="SCM_SLOT", 
         idPromConfigBusName="SMBus I801 adapter at 1000",
         idPromConfigAddress="0x50",
         idpromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      ),
      SlotTypeConfig(
         slotName='SMB_SLOT',
         numOutgoingI2cBuses=3,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x50",
         idpromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      ),
      SlotTypeConfig(
         slotName="PSU_SLOT",
         numOutgoingI2cBuses=1
      ),
      SlotTypeConfig(
         slotName="FAN_SLOT"
      )
   ]

   PM_UNIT_CONFIGS = [ SCMUnit, SMBUnit, PSUUnit, FANUnit ]

   I2C_ADAPTERS_FROM_CPU = [
      { "adapter" : "SMBus I801 adapter at 1000" }
   ]

   KMODS_SETTINGS_DICT = {
      "bspKmodsRpmName": "arista_bsp_kmods",
      "bspKmodsRpmVersion": "0.7.2-1",
      "bspKmodsToReload" : 
         "scd-xcvr, scd-spi, scd-leds, scd-smbus, dsf-fan-cpld",
      "sharedKmodsToReload": "scd",
      "upstreamKmodsToLoad": "spidev, i2c-i801"
   }
