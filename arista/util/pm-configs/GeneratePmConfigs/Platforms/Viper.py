# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from GeneratePmConfigs.BaseConfigs import (
   enumerateFANSlotConfigs, 
   enumeratePciDeviceConfigs,
   FANUnit,
   I2cDeviceConfig, 
   InitRegSettings,
   LedConfig,
   PlatformConfig,
   PSUUnit,
   SCMUnit, 
   SlotConfig, 
   SlotTypeConfig, 
   SMBUnit,
   SpiDeviceConfig, 
   SpiMasterConfig
)


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

      '''
      Initial I2c register values are implicitly cast to 8-bit unsigned integer
      values when creating a device, but Python uses two's complement.
      -121 in 8-bit two's complement has the same binary representation as
      135 in 8-bit unsigned. Register values represent temperature in Celsius and 
      are used to overwrite the default temperature settings.
      '''
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
         *enumeratePciDeviceConfigs( 1, "SMB_FPGA", "0x3475", "0x0001", "0x3475", 
                                     "0x0003" )
      ] )

      for pciConfig in self.pmUnitConfigs[ 1 ].pciDeviceConfigs:
         pciConfig.addI2cAdapterConfigs( 6, "SMB_I2C_MASTER{}", "0x8000" )
         pciConfig.addSpiMasterConfigs( [
            SpiMasterConfig( "SMB_SPI_MASTER0", "spi_master", -1, 
                             "0x7900",
                             spiDeviceConfigs=[ SpiDeviceConfig(
                             pmUnitScopedName="SMB_SPI_MASTER0_DEVICE1",
                             chipSelect=0,
                             modalias="spidev",
                             maxSpeedHz=25000000
                             ) ] 
                           )
         ] )
         pciConfig.addXcvrCtrlConfigs( numConfigs=38, basePortNumber=1 )
         pciConfig.addXcvrCtrlConfigs( numConfigs=1, basePortNumber=39, 
                                       portType="qsfp", xcvrBaseOffset="0xA290", 
                                       led1BaseOffset="0x65C0", 
                                       led2BaseOffset="0x65D0", 
                                       led3BaseOffset="0x65E0",
                                       led4BaseOffset="0x65F0" )
         pciConfig.addLedCtrlConfigs( [
            LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
            LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
            LedConfig( ledName="PSU_STATUS_LED", offset="0x6070" ),
            LedConfig( ledName="SMB_STATUS_LED", offset="0x6090" )
         ] )

      self.pmUnitConfigs[ 2 ].addI2cDeviceConfigs( [
         I2cDeviceConfig( "INCOMING@0", "0x58", "pmbus", "PSU_PMBUS" )
      ] )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths( self.platformName )


def main():
   platform = Viper()
   print( platform.asJson() )


if __name__ == '__main__':
   main()


