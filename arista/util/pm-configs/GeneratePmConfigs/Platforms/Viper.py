# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from BaseConfigs import (
   enumerateFANSlotConfigs, 
   enumeratePciDeviceConfigs,
   EmbeddedSensorConfig,
   FANUnit,
   FANCpld,
   Flash, 
   GpioChip,
   InitRegSettings,
   LedConfig,
   PlatformConfig,
   PSUUnit,
   SCMIdProm,
   SCMUnit, 
   Sensor,
   SlotConfig, 
   SMBUnit,
   SpiMasterConfig
)


class ViperSCM( SCMUnit ):
   def __init__( self ):
      super().__init__()

      self.setSlotTypeConfig(
         idPromConfigBusName="SMBus I801 adapter at 1000",
         idPromConfigAddress="0x50",
         idpromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )

      self.addI2cDeviceConfigs( [
         Sensor( "0x40", "pmbus", "SCM_MPS_PMBUS" ),
         SCMIdProm( "0x50", "24c512", "SCM_IDPROM_P1", hasCpuMac=True ),
         Sensor( "0x30", "pxm1310", "SCM_PXM1310_1" ),
         Sensor( "0x3e", "pxe1610", "SCM_PXE1211" ),
         Sensor( "0x40", "pxm1310", "SCM_PXM1310_2" )
      ] )

      self.addPciDeviceConfigs( [
         *enumeratePciDeviceConfigs( 1, "SCM_FPGA", "0x3475", "0x0001", "0x3475", 
                                     "0x0008" )
      ] )

      self.pciDeviceConfigs[ 0 ].addI2cAdapterConfigs( 2, "SCM_I2C_MASTER{}", 
                                                       "0x8000" )
      
      self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 0 ].addDevicesOnAdapters(
         {
            0 : [ self.i2cDeviceConfigs[ 0 ] ],
            1 : [ self.i2cDeviceConfigs[ 1 ] ],
            2 : [ 
                  self.i2cDeviceConfigs[ 2 ], 
                  self.i2cDeviceConfigs[ 3 ],
                  self.i2cDeviceConfigs[ 4 ] 
                ]
         }
      )

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="SMB_SLOT@0",
            outgoingI2cBuses=[ 
               self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 1 ].buses[ 0 ],
               self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 1 ].buses[ 2 ],
               self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 1 ].buses[ 3 ]
            ]
         )
      ] )

      self.addEmbeddedSensorConfigs( [
         EmbeddedSensorConfig( 
            pmUnitScopedName="CPU_CORE_TEMP", 
            sysfsPath="/sys/bus/platform/devices/coretemp.0" 
         )
      ] )


class ViperSMB( SMBUnit ):
   def __init__( self ):
      super().__init__()

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=3,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x50",
         idpromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )

      '''
      Initial I2c register values are implicitly cast to 8-bit unsigned integer
      values when creating a device, but Python uses two's complement.
      -121 in 8-bit two's complement has the same binary representation as
      135 in 8-bit unsigned. Register values represent temperature in Celsius and 
      are used to overwrite the default temperature settings.
      '''
      self.addI2cDeviceConfigs( [
         GpioChip( "0x74", "pca9539", "SMB_PCA", incomingBusIndex=0 ),
         Sensor( "0x49", "tmp75", "SMB_TMP75_FRONT", incomingBusIndex=1,
                           initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) ),
         Sensor( "0x4A", "tmp75", "SMB_TMP75_REAR", incomingBusIndex=1,
                           initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) ),
         Sensor( "0x4D", "max6581", "SMB_MAX6581", incomingBusIndex=1,
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
         Sensor( "0x48", "tmp75", "FAN_TMP75", incomingBusIndex=2,
                           initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) ),
         FANCpld( "0x60", "pali2_cpld", "FAN_CPLD", incomingBusIndex=2 ),
         Sensor( "0x45", "raa228228", "SMB_RAA228926_J3" ),
         Sensor( "0x54", "isl68226", "SMB_ISL68226_J3" ),
         Sensor( "0x55", "isl68226", "SMB_ISL68226_OPTICS" ),
         Sensor( "0x48", "tmp75", "SMB_MGMT_TMP75" )
      ] )

      self.addPciDeviceConfigs( [
         *enumeratePciDeviceConfigs( 1, "SMB_FPGA", "0x3475", "0x0001", "0x3475", 
                                     "0x0003" )
      ] )

      for pciConfig in self.pciDeviceConfigs:
         pciConfig.addI2cAdapterConfigs( 6, "SMB_I2C_MASTER{}", "0x8000" )
         pciConfig.addSpiMasterConfigs( [
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

      self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 0 ].addDevicesOnAdapters(
         {
            0: [
                  self.i2cDeviceConfigs[ 6 ],
                  self.i2cDeviceConfigs[ 7 ],
                  self.i2cDeviceConfigs[ 8 ]
               ],
            2: [ self.i2cDeviceConfigs[ 9 ] ]
         }
      )

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="psu1_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ 
               ( self.pciDeviceConfigs[ 0 ]
                 .i2cAdapterConfigs[ 0 ].buses[ 5 ] )
            ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@1",
            presenceFileName="psu2_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[
               ( self.pciDeviceConfigs[ 0 ]
                 .i2cAdapterConfigs[ 0 ].buses[ 6 ] ),
            ]
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

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()


def main():
   platform = Viper()
   print( platform.asJson() )


if __name__ == '__main__':
   main()


