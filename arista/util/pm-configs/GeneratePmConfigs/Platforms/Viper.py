# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from BaseConfigs import (
   enumerateFANSlotConfigs,
   FANUnit,
   FANCpld,
   Flash,
   GpioChip,
   InitRegSettings,
   LedConfig,
   PciDeviceConfig,
   PlatformConfig,
   PSUUnit,
   SCMFairywren,
   Sensor,
   SlotConfig,
   SMBUnit,
   SpiMasterConfig
)


class ViperSCM( SCMFairywren ):
   def __init__( self ):
      super().__init__()

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="SMB_SLOT@0",
            outgoingI2cBuses=[
               self.scmI2cMaster1.buses[ 0 ],
               self.scmI2cMaster1.buses[ 2 ],
               self.scmI2cMaster1.buses[ 3 ]
            ]
         )
      ] )


class ViperSMB( SMBUnit ):
   def __init__( self ):
      super().__init__()

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=3,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )

      '''
      Initial I2c register values are implicitly cast to 8-bit unsigned integer
      values when creating a device, but Python uses two's complement.
      -121 in 8-bit two's complement has the same binary representation as
      135 in 8-bit unsigned. Register values represent temperature in Celsius and
      are used to overwrite the default temperature settings.
      '''
      smbPca = GpioChip( "0x74", "pca9539", "SMB_PCA", incomingBusIndex=0 )
      smbTmp75Front = Sensor( "0x49", "tmp75", "SMB_TMP75_FRONT", incomingBusIndex=1,
                              initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) )
      smbTmp75Back = Sensor( "0x4A", "tmp75", "SMB_TMP75_REAR",
                             incomingBusIndex=1,
                             initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) )
      smbMax = Sensor( "0x4D", "max6581", "SMB_MAX6581", incomingBusIndex=1,
                       initRegSettings=InitRegSettings( [
                           ( 32, 110 ),
                           ( 33, -121 ),
                           ( 34, -121 ),
                           ( 35, -121 ),
                           ( 36, -121 ),
                           ( 37, -121 ),
                           ( 38, -121 ),
                           ( 39, -121 )
                        ] )
                     )
      smbFanTmp = Sensor( "0x48", "tmp75", "FAN_TMP75", incomingBusIndex=2,
                          initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) )
      smbFanCpld = FANCpld( "0x60", "pali2_cpld", "FAN_CPLD", incomingBusIndex=2 )
      smbRaa = Sensor( "0x45", "raa228228", "SMB_RAA228926_J3" )
      smbIsl = Sensor( "0x54", "isl68226", "SMB_ISL68226_J3" )
      smbIslOptics = Sensor( "0x55", "isl68226", "SMB_ISL68226_OPTICS" )
      smbMgmtTemp = Sensor( "0x48", "tmp75", "SMB_MGMT_TMP75" )

      self.addI2cDeviceConfigs( [
         smbPca,
         smbTmp75Front,
         smbTmp75Back,
         smbMax,
         smbFanTmp,
         smbFanCpld,
         smbRaa,
         smbIsl,
         smbIslOptics,
         smbMgmtTemp
      ] )

      self.addPciDeviceConfigs( [
         PciDeviceConfig( "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0003" )
      ] )

      smbFpga = self.pciDeviceConfigs[ 0 ]
      smbFpga.addI2cAdapterConfigs( 6, "SMB_I2C_MASTER{}", "0x8000" )
      smbFpga.addSpiMasterConfigs( [
         SpiMasterConfig( "SMB_SPI_MASTER0", "spi_master", -1,
                           "0x7900",
                           spiDeviceConfigs=[ Flash(
                              pmUnitScopedName="SMB_SPI_MASTER0_DEVICE1",
                              chipSelect=0,
                              modalias="spidev",
                              maxSpeedHz=25000000
                           ) ]
                        )
      ] )
      smbFpga.addXcvrCtrlConfigs( numConfigs=38, basePortNumber=1 )
      smbFpga.addXcvrCtrlConfigs( numConfigs=1, basePortNumber=39,
                                    portType="qsfp", xcvrBaseOffset="0xA290",
                                    ledBaseOffset="0x65C0", ledsPerXcvr=4 )
      smbFpga.addLedCtrlConfigs( [
         LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
         LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
         LedConfig( ledName="PSU_STATUS_LED", offset="0x6070" ),
         LedConfig( ledName="SMB_STATUS_LED", offset="0x6090" )
      ] )

      smbI2cMaster0 = self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 0 ]
      smbI2cMaster0.buses[ 0 ].addI2cDevices( [ smbRaa, smbIsl, smbIslOptics ] )
      smbI2cMaster0.buses[ 2 ].addI2cDevices( [ smbMgmtTemp ] )

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="psu1_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ smbI2cMaster0.buses[ 5 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@1",
            presenceFileName="psu2_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ smbI2cMaster0.buses[ 6 ] ]
         ),
         *enumerateFANSlotConfigs( 4, "/SMB_SLOT@0/[FAN_CPLD]" )
      ] )


class Viper( PlatformConfig ):
   def __init__( self ):
      super().__init__( "meru800bia" )

      self.addPmUnitConfigs( [
         ViperSCM(),
         ViperSMB(),
         PSUUnit(),
         FANUnit()
      ] )

      self.addI2cAdaptersFromCpu( [ "SMBus I801 adapter at 1000" ] )

      self.addKmodsSettings(
         {
            "bspKmodsToReload" : [
               "scd-xcvr",
               "scd-spi",
               "scd-leds",
               "scd-smbus",
               "dsf-fan-cpld"
            ],
            "sharedKmodsToReload": [ "scd" ],
            "upstreamKmodsToLoad": [ "spidev", "i2c-i801" ]
         }
      )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()


def main():
   platform = Viper()
   print( platform.asJson() )


if __name__ == '__main__':
   main()


