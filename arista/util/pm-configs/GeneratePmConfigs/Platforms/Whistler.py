# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from BaseConfigs import (
   enumerateFANSlotConfigs,
   enumeratePciDeviceConfigs,
   FANCpld,
   FANUnit,
   Flash,
   LedConfig,
   PlatformConfig,
   PSUUnit,
   SCMFairywren,
   Sensor,
   SlotConfig,
   SMBCpld,
   SMBUnit,
   SpiMasterConfig
)


class WhistlerSCM( SCMFairywren ):
   def __init__( self ):
      super().__init__()

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="SMB_SLOT@0",
            outgoingI2cBuses=[
               self.scmI2cMaster1.buses[ 0 ],
               self.scmI2cMaster1.buses[ 1 ],
               self.scmI2cMaster1.buses[ 2 ],
               self.scmI2cMaster1.buses[ 3 ]
            ]
         )
      ] )


class WhistlerSMB( SMBUnit ):
   def __init__( self ):
      super().__init__()

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=4,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x52",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )

      self.addI2cDeviceConfigs( [
         SMBCpld( "0x23", "decker_cpld", "SMB_CPLD", incomingBusIndex=0 ),
         Sensor( "0x4D", "max6581", "SMB_MAX6581", incomingBusIndex=0 ),
         Sensor( "0x48", "tmp75", "SMB_TMP75", incomingBusIndex=0 ),
         Sensor( "0x60", "raa228228", "SMB_RAA228926_R3R0_CORE",
                 incomingBusIndex=1 ),
         Sensor( "0x50", "isl68226", "SMB_ISL68226_R3R0_ANLG0",
                 incomingBusIndex=1 ),
         Sensor( "0x51", "isl68226", "SMB_ISL68226_R3R0_ANLG1",
                 incomingBusIndex=1 ),
         Sensor( "0x61", "raa228228", "SMB_RAA228926_R3R1_CORE",
                 incomingBusIndex=1 ),
         Sensor( "0x52", "isl68226", "SMB_ISL68226_R3R1_ANLG0",
                 incomingBusIndex=1 ),
         Sensor( "0x53", "isl68226", "SMB_ISL68226_R3R1_ANLG1",
                 incomingBusIndex=1 ),
         Sensor( "0x5A", "isl68226", "SMB_ISL68226_OSFP_TL",
                 incomingBusIndex=1 ),
         Sensor( "0x5B", "isl68226", "SMB_ISL68226_OSFP_TR",
                 incomingBusIndex=1 ),
         Sensor( "0x5C", "isl68226", "SMB_ISL68226_OSFP_BL",
                 incomingBusIndex=1 ),
         Sensor( "0x5D", "isl68226", "SMB_ISL68226_OSFP_BR",
                 incomingBusIndex=1 ),
         Sensor( "0x11", "ucd90320", "SMB_UCD90320", incomingBusIndex=2 ),
         Sensor( "0x48", "tmp75", "FAN0_TMP75", incomingBusIndex=3 ),
         FANCpld( "0x60", "oasis_cpld0", "FAN0_CPLD", incomingBusIndex=3 ),
         Sensor( "0x49", "tmp75", "FAN1_TMP75", incomingBusIndex=3 ),
         FANCpld( "0x61", "oasis_cpld1", "FAN1_CPLD", incomingBusIndex=3 ),
         Sensor( "0x4A", "tmp75", "FAN2_TMP75", incomingBusIndex=3 ),
         FANCpld( "0x62", "oasis_cpld2", "FAN2_CPLD", incomingBusIndex=3 )
      ] )

      self.addPciDeviceConfigs( [
         *enumeratePciDeviceConfigs( 4, "SMB_FPGA{}", "0x3475", "0x0001", "0x3475",
                                     "0x0004" )
      ] )
      smbFpga0 = self.pciDeviceConfigs[ 0 ]
      smbFpga1 = self.pciDeviceConfigs[ 1 ]
      smbFpga2 = self.pciDeviceConfigs[ 2 ]
      smbFpga3 = self.pciDeviceConfigs[ 3 ]

      for pciConfig in self.pciDeviceConfigs:
         pciConfig.addI2cAdapterConfigs( 5, "SMB_FPGA{}_I2C_MASTER{}", "0x8000" )
         pciConfig.addSpiMasterConfigs( [
            SpiMasterConfig(
               "SMB_SPI_MASTER0",
               "spi_master",
               -1,
               "0x7900",
               spiDeviceConfigs=[
                  Flash(
                     pmUnitScopedName="SMB_SPI_MASTER0_DEVICE1",
                     chipSelect=0,
                     modalias="spidev",
                     maxSpeedHz=25000000
                  )
               ]
            )
         ] )

      smbFpga0.addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=1, portNumberSkipStep=4
      )
      smbFpga1.addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=5, portNumberSkipStep=4
      )
      smbFpga2.addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=65, portNumberSkipStep=4
      )
      smbFpga3.addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=69, portNumberSkipStep=4
      )

      smbFpga2.addLedCtrlConfigs( [
         LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
         LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
         LedConfig( ledName="PSU_STATUS_LED", offset="0x6070" ),
         LedConfig( ledName="SMB_STATUS_LED", offset="0x60a0" )
      ] )

      smbFpga2Master4 = smbFpga2.i2cAdapterConfigs[ 4 ]
      smbFpga3Master4 = smbFpga3.i2cAdapterConfigs[ 4 ]
      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="psu1_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbFpga3Master4.buses[ 0 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@1",
            presenceFileName="psu2_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbFpga2Master4.buses[ 0 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@2",
            presenceFileName="psu3_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbFpga3Master4.buses[ 1 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@3",
            presenceFileName="psu4_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbFpga2Master4.buses[ 1 ] ]
         ),
         *enumerateFANSlotConfigs( 12, "/SMB_SLOT@0/[FAN{}_CPLD]" )
      ] )


class Whistler( PlatformConfig ):
   def __init__( self ):
      super().__init__( "meru800bfa" )

      self.addPmUnitConfigs( [
         WhistlerSCM(),
         WhistlerSMB(),
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
               "dsf-fan-cpld",
               "decker-cpld"
            ],
            "sharedKmodsToReload": [ "scd" ],
            "upstreamKmodsToLoad": [ "spidev", "i2c-i801" ]
         }
      )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()


def main():
   platform = Whistler()
   print( platform.asJson() )


if __name__ == '__main__':
   main()