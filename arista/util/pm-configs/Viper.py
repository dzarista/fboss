# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from BaseConfigs import (
   PlatformConfig,
   SlotTypeConfig, 
   I2cDeviceConfig, 
   SlotConfig, 
   LedConfig,
   SpiMasterConfig, 
   SpiDeviceConfig,
   InitRegSettings,
   enumerateFANSlotConfigs, 
   enumeratePciDeviceConfigs
)

from BaseConfigs import SCMUnit, SMBUnit, PSUUnit, FANUnit


class Viper( PlatformConfig ):

   def __init__( self ):
      super().__init__( "meru800bia" )

      self.addSlotTypeConfigs( [
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
      ] )

      self.addPmUnitConfigs( [
         SCMUnit(),
         SMBUnit(),
         PSUUnit(),
         FANUnit()
      ] )

      '''SCM Unit Configs Below'''

      self.pmUnitConfigs[ 0 ].populateSymlinkToDevicePaths( self.platformName )
      self.pmUnitConfigs[ 0 ].addSymlinkToDevicePaths( {
         "/run/devmap/fpgas/MERU_SCM_CPLD": "/[SCM_FPGA]",
         "/run/devmap/eeproms/MERU_SCM_EEPROM_P1": "/[SCM_IDPROM_P1]",
         "/run/devmap/eeproms/MERU_SCM_EEPROM": "/[IDPROM]"
      } )

      '''SMB Unit Configs Below'''

      self.pmUnitConfigs[ 1 ].addI2cDeviceConfigs( [
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
      ] )

      self.pmUnitConfigs[ 1 ].addOutgoingSlotConfigs( [
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
      ] )

      self.pmUnitConfigs[ 1 ].addPciDeviceConfigs( [
         *enumeratePciDeviceConfigs( 1, "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0003" )
      ] )

      for pciConfig in self.pmUnitConfigs[ 1 ].pciDeviceConfigs:
         pciConfig.addI2cAdapterConfigs( 6, "SMB_I2C_MASTER*", "0x8000" )
         pciConfig.addSpiMasterConfigs( [
            SpiMasterConfig( "SMB_SPI_MASTER0", "spi_master", -1, 
                           "0x7900",
                           spiDeviceConfigs=[ SpiDeviceConfig(
                              pmUnitScopedName="SMB_SPI_MASTER0_DEVICE1",
                              chipSelect=0,
                              modalias="spidev",
                              maxSpeedHz=25000000
                           ) ] )
         ] )
         pciConfig.addXcvrCtrlConfigs( numConfigs=38, basePortNumber=1 )
         pciConfig.addXcvrCtrlConfigs( numConfigs=1, basePortNumber=39, portType="qsfp", 
                                 xcvrBaseOffset="0xA290", led1BaseOffset="0x65C0", 
                                 led2BaseOffset="0x65D0", led3BaseOffset="0x65E0",
                                 led4BaseOffset="0x65F0")
         pciConfig.addLedCtrlConfigs( [
            LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
            LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
            LedConfig( ledName="PSU_STATUS_LED", offset="0x6070" ),
            LedConfig( ledName="SMB_STATUS_LED", offset="0x6090" )
         ] )

      self.pmUnitConfigs[ 1 ].populateSymlinkToDevicePaths( self.platformName )
      self.pmUnitConfigs[ 1 ].addSymlinkToDevicePaths( {
         "/run/devmap/eeproms/MERU800BIA_SMB_EEPROM": "/SMB_SLOT@0/[SMB_IDPROM]",
         "/run/devmap/fpgas/MERU800BIA_SMB_FPGA": "/SMB_SLOT@0/[SMB_FPGA]",
         "/run/devmap/gpiochips/SMB_PCA": "/SMB_SLOT@0/[SMB_PCA]",
         "/run/devmap/flashes/SMB_SPI_MASTER0_DEVICE1": \
            "/SMB_SLOT@0/[SMB_SPI_MASTER0_DEVICE1]"
      } )

      '''PSU Unit Configs Below'''

      self.pmUnitConfigs[ 2 ].addI2cDeviceConfigs( [
         I2cDeviceConfig( "INCOMING@0", "0x58", "pmbus", "PSU_PMBUS" )
      ] )

      self.pmUnitConfigs[ 2 ].addSymlinkToDevicePaths( {
         "/run/devmap/sensors/PSU1_PMBUS": "/SMB_SLOT@0/PSU_SLOT@0/[PSU_PMBUS]",
         "/run/devmap/sensors/PSU2_PMBUS": "/SMB_SLOT@0/PSU_SLOT@1/[PSU_PMBUS]"
      } )

      '''FAN Unit Configs Below'''

      self.pmUnitConfigs[ 3 ].addSymlinkToDevicePaths( {
         "/run/devmap/cplds/FAN_CPLD": "/SMB_SLOT@0/[FAN_CPLD]"
      } )

