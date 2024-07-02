# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from tools import *

class Viper:

   PLATFORM_NAME = "meru800bia"
   ROOT_PM_UNIT_NAME = "SCM"

   SLOT_TYPE_CONFIGS = [
      SlotTypeConfig( 
         slotName="SCM_SLOT", 
         numOutgoingI2cBuses=0,
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
         slotName="FAN_SLOT",
         numOutgoingI2cBuses=0
      )
   ]

   PM_UNIT_CONFIGS = [ "SCM", "SMB", "PSU", "FAN" ]

   I2C_DEVICE_CONFIGS = {
      "SCM" : [
         I2cDeviceConfig( "SCM_I2C_MASTER0@0", "0x40", "pmbus", "SCM_MPS_PMBUS" ),
         I2cDeviceConfig( "SCM_I2C_MASTER0@1", "0x50", "24c512", "SCM_IDPROM", 
                        hasCpuMac=True ),
         I2cDeviceConfig( "SCM_I2C_MASTER0@2", "0x30", "pxm1310", "SCM_PXM1310_1" ),
         I2cDeviceConfig( "SCM_I2C_MASTER0@2", "0x3e", "pxe1610", "SCM_PXE1211" ),
         I2cDeviceConfig( "SCM_I2C_MASTER0@2", "0x40", "pxm1310", "SCM_PXM1310_2" )
      ],
      "SMB" : [
         I2cDeviceConfig( "INCOMING@0", "0x50", "24c512", "SMB_IDPROM" ),
         I2cDeviceConfig( "INCOMING@0", "0x74", "pca9539", "SMB_PCA", 
                         isGpioChip=True ),
         I2cDeviceConfig( "INCOMING@1", "0x49", "tmp75", "SMB_TMP75_FRONT" ),
         I2cDeviceConfig( "INCOMING@1", "0x4A", "tmp75", "SMB_TMP75_REAR" ),
         I2cDeviceConfig( "INCOMING@2", "0x48", "tmp75", "FAN_TMP75" ),
         I2cDeviceConfig( "INCOMING@2", "0x60", "pali2_cpld", "FAN_CPLD" ),
         I2cDeviceConfig( "SMB_I2C_MASTER0@0", "0x45", "raa228228", 
                         "SMB_RAA228926_J3" ),
         I2cDeviceConfig( "SMB_I2C_MASTER0@0", "0x54", "isl68226", 
                         "SMB_ISL68226_J3" ),
         I2cDeviceConfig( "SMB_I2C_MASTER0@0", "0x55", "isl68226", 
                         "SMB_ISL68226_OPTICS" )
      ],
      "PSU" : [
         I2cDeviceConfig( "INCOMING@0", "0x58", "pmbus", "PSU_PMBUS" )
      ]
   }

   OUTGOING_SLOT_CONFIGS = {
      "SCM" : [
         SlotConfig(
            slotName="SMB_SLOT@0",
            presenceFileName=None,
            presenceDevicePath=None,
            outgoingI2cBusNames=[ "SCM_I2C_MASTER1@0", 
                                  "SCM_I2C_MASTER1@2",
                                  "SCM_I2C_MASTER1@3" ]
         )
      ],
      "SMB" : [
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
            presenceFileName="hwmon/hwmon*/fan1_present",
            presenceDevicePath="/SMB_SLOT@0/[FAN_CPLD]"
         ),
         SlotConfig(
            slotName="FAN_SLOT@1",
            presenceFileName="hwmon/hwmon*/fan2_present",
            presenceDevicePath="/SMB_SLOT@0/[FAN_CPLD]"
         ),
         SlotConfig(
            slotName="FAN_SLOT@2",
            presenceFileName="hwmon/hwmon*/fan3_present",
            presenceDevicePath="/SMB_SLOT@0/[FAN_CPLD]"
         ),
         SlotConfig(
            slotName="FAN_SLOT@3",
            presenceFileName="hwmon/hwmon*/fan4_present",
            presenceDevicePath="/SMB_SLOT@0/[FAN_CPLD]"
         )
      ]
   }

   PCI_DEVICE_CONFIGS = {
      "SCM" : [
         PciDeviceConfig( "SCM_FPGA", "0x3475", "0x0001", "0x3475", "0x0008" )
      ],
      "SMB" : [
         PciDeviceConfig( "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0003" )
      ]
   }

   I2C_ADAPTER_CONFIGS = {
      "SCM_FPGA" : [
         I2cAdapterConfig( "SCM_I2C_MASTER0", "i2c_master", -1, "0x8000", 8 ),
         I2cAdapterConfig( "SCM_I2C_MASTER1", "i2c_master", -1, "0x8080", 8 )
      ],
      "SMB_FPGA" : [
         I2cAdapterConfig( "SMB_I2C_MASTER0", "i2c_master", -1, "0x8000", 8),
         I2cAdapterConfig( "SMB_I2C_MASTER1", "i2c_master", -1, "0x8080", 8),
         I2cAdapterConfig( "SMB_I2C_MASTER2", "i2c_master", -1, "0x8100", 8),
         I2cAdapterConfig( "SMB_I2C_MASTER3", "i2c_master", -1, "0x8180", 8),
         I2cAdapterConfig( "SMB_I2C_MASTER4", "i2c_master", -1, "0x8200", 8),
         I2cAdapterConfig( "SMB_I2C_MASTER5", "i2c_master", -1, "0x8280", 8),
      ]
   }

   SPI_MASTER_CONFIGS = {
      "SCM_FPGA" : [
         SpiMasterConfig( "SCM_SPI_MASTER0", "spi_master", -1, "0x7900", 0 )
      ]
   }

   XCVR_CONFIGS = {
      "SMB_FPGA" : [
         *enumerateXcvrConfigs( basePortNumber=1, portType="osfp", 
                                xcvrBaseOffset="0xA010", led1BaseOffset="0x6100", 
                                led2BaseOffset="0x6110", led3BaseOffset=None,
                                led4BaseOffset=None, numConfigs=38 ),
         XcvrConfig( portNumber=39, portType="qsfp", xcvrCtrlOffset="0xA290",
                    led1Offset="0x65C0", led2Offset="0x65D0", led3Offset="0x65E0",
                    led4Offset="0x65F0" )
      ]
   }

   LED_CONFIGS = {
      "SMB_FPGA" : [
         LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
         LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
         LedConfig( ledName="PSU_STATUS_LED", offset="0x6070" ),
         LedConfig( ledName="SMB_STATUS_LED", offset="0x6090" )
      ]
   }

   I2C_ADAPTERS_FROM_CPU = [
      { "adapter" : "SMBus I801 adapter at 1000" }
   ]


   KMODS_SETTINGS_DICT = {
      "bspKmodsRpmName" : "kernel-arista",
      "bspKmodsRpmVersion" : 1,
      "kmodsToReload" : "scd, scd-spi, scd-leds, scd-xcvr, scd-smbus, dsf-fan-cpld"
   }
