# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from tools import SlotTypeConfig, I2cDeviceConfig, SlotConfig, XcvrConfig, LedConfig, \
   enumerateXcvrConfigsViper, generateXcvrSymlinks, generateI2cAdapterSymlinks, \
   generateSensorSymlinks, InitRegSettings, enumerateFANSlotConfigs, \
   enumeratePciDeviceConfigs, enumerateI2cAdapterConfigs, enumerateSpiMasterConfigs

from BaseConfigs import SCMUnit, SMBUnit, PSUUnit, FANUnit, Platform


class ViperSCM( SCMUnit ):

   SYMBOLIC_LINK_TO_DEVICE_PATH = {
      "/run/devmap/fpgas/MERU_SCM_CPLD": "/[SCM_FPGA]",
      **generateI2cAdapterSymlinks( SCMUnit.I2C_ADAPTER_CONFIGS, "SCM" ),
      "/run/devmap/eeproms/MERU_SCM_EEPROM_P1": "/[SCM_IDPROM_P1]",
      "/run/devmap/eeproms/MERU_SCM_EEPROM": "/[IDPROM]",
      **generateSensorSymlinks( SCMUnit.EMBEDDED_SENSORS_CONFIGS, \
                                 SCMUnit.I2C_DEVICE_CONFIGS, "SCM" ),
   }


class ViperSMB( SMBUnit ):
   
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
      I2cDeviceConfig( "INCOMING@2", "0x48", "tmp75", "FAN_TMP75",
                        initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) ),
      I2cDeviceConfig( "INCOMING@2", "0x60", "pali2_cpld", "FAN_CPLD" ),
      I2cDeviceConfig( "SMB_I2C_MASTER0@0", "0x45", "raa228228", 
                        "SMB_RAA228926_J3" ),
      I2cDeviceConfig( "SMB_I2C_MASTER0@0", "0x54", "isl68226", 
                        "SMB_ISL68226_J3" ),
      I2cDeviceConfig( "SMB_I2C_MASTER0@0", "0x55", "isl68226", 
                        "SMB_ISL68226_OPTICS" ),
      I2cDeviceConfig( "SMB_I2C_MASTER0@2", "0x48", "tmp75", "SMB_MGMT_TMP75" )
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
      *enumerateFANSlotConfigs( 4, "/SMB_SLOT@0/[FAN_CPLD]" )
   ]

   PCI_DEVICE_CONFIGS = [
      *enumeratePciDeviceConfigs( 1, "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0003" )
   ]

   I2C_ADAPTER_CONFIGS = [
      *enumerateI2cAdapterConfigs( 1, 6, "SMB_FPGA", "SMB_I2C_MASTER*", "0x8000" )
   ]

   SPI_MASTER_CONFIGS = [
      *enumerateSpiMasterConfigs( PCI_DEVICE_CONFIGS )
   ]
   
   XCVR_CONFIGS = [
      *enumerateXcvrConfigsViper( numConfigs=38, name="SMB_FPGA", basePortNumber=1, 
                              portType="osfp", xcvrBaseOffset="0xA010", 
                              led1BaseOffset="0x6100", led2BaseOffset="0x6110" ),
      XcvrConfig( "SMB_FPGA", portNumber=39, portType="qsfp", xcvrCtrlOffset="0xA290",
                  led1Offset="0x65C0", led2Offset="0x65D0", led3Offset="0x65E0",
                  led4Offset="0x65F0" )
   ]

   LED_CONFIGS = [
      LedConfig( "SMB_FPGA", ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
      LedConfig( "SMB_FPGA", ledName="FAN_STATUS_LED", offset="0x6060" ),
      LedConfig( "SMB_FPGA", ledName="PSU_STATUS_LED", offset="0x6070" ),
      LedConfig( "SMB_FPGA", ledName="SMB_STATUS_LED", offset="0x6090" )
   ]

   SYMBOLIC_LINK_TO_DEVICE_PATH = {
      "/run/devmap/eeproms/MERU800BIA_SMB_EEPROM": "/SMB_SLOT@0/[SMB_IDPROM]",
      "/run/devmap/fpgas/MERU800BIA_SMB_FPGA": "/SMB_SLOT@0/[SMB_FPGA]",
      **generateI2cAdapterSymlinks( I2C_ADAPTER_CONFIGS, "SMB" ),
      "/run/devmap/gpiochips/SMB_PCA": "/SMB_SLOT@0/[SMB_PCA]",
      **generateSensorSymlinks( SMBUnit.EMBEDDED_SENSORS_CONFIGS, \
                                 I2C_DEVICE_CONFIGS, "SMB" ),
      **generateXcvrSymlinks( XCVR_CONFIGS ),
      "/run/devmap/flashes/SMB_SPI_MASTER0_DEVICE1": \
         "/SMB_SLOT@0/[SMB_SPI_MASTER0_DEVICE1]"
   }


class ViperPSU( PSUUnit ):

   I2C_DEVICE_CONFIGS = [
      I2cDeviceConfig( "INCOMING@0", "0x58", "pmbus", "PSU_PMBUS" )
   ]

   SYMBOLIC_LINK_TO_DEVICE_PATH = {
      "/run/devmap/sensors/PSU1_PMBUS": "/SMB_SLOT@0/PSU_SLOT@0/[PSU_PMBUS]",
      "/run/devmap/sensors/PSU2_PMBUS": "/SMB_SLOT@0/PSU_SLOT@1/[PSU_PMBUS]",
   }


class ViperFAN( FANUnit ):

   SYMBOLIC_LINK_TO_DEVICE_PATH = {
      "/run/devmap/cplds/FAN_CPLD": "/SMB_SLOT@0/[FAN_CPLD]",
   }


class Viper( Platform ):

   PLATFORM_NAME = "meru800bia"

   SLOT_TYPE_CONFIGS = [
      SlotTypeConfig( 
         slotName="SCM_SLOT", 
         idPromConfigBusName="SMBus I801 adapter at 1000",
         idPromConfigAddress="0x50",
         idpromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      ),
      SlotTypeConfig(
         slotName="SMB_SLOT",
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

   PM_UNIT_CONFIGS = [ ViperSCM, ViperSMB, ViperPSU, ViperFAN ]
