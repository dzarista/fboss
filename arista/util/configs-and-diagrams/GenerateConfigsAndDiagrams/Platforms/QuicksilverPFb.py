# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from ..BaseConfigs import (
   PciDeviceConfig,
   PlatformConfig,
   SCMFairywren,
   SlotConfig,
   SMBCpld,
   SMBUnit,
   LedConfig
)


class QuicksilverPFbSCM( SCMFairywren ):
   def __init__( self ):
      self.supportsP1 = False
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

class QuicksilverPFbSMB( SMBUnit ):
   prefixSymlink = 'MERU800BA'

   def __init__( self ):
      super().__init__( self.prefixSymlink )

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=3,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )
      smbCpld = SMBCpld( "0x23", "quicksilver_cpld", "SMB_CPLD", incomingBusIndex=0 )
      self.addI2cDeviceConfigs( [
         smbCpld
      ] )

      self.addPciDeviceConfigs( [
         PciDeviceConfig( "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0009",
                         symlinkDeviceName="MERU800BA_SMB_FPGA" )
      ] )

      smbFpga = self.pciDeviceConfigs[ 0 ]
      smbFpga.addInfoRomConfigs( "0x100" )
      smbFpga.addI2cAdapterConfigs( 11, "SMB_I2C_MASTER{}", "0x8080" )

      smbFpga.addXcvrCtrlConfigs( numConfigs=64, basePortNumber=1, ledsPerXcvr=2,
                                  smbusAccelStart=3, smbusName="SMB_I2C_MASTER",
                                  xcvrBaseOffset="0xA000", accelBusRange=( 0, 7 ) )

      smbFpga.addLedCtrlConfigs( [
         LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
         LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
         LedConfig( ledName="PSU1_STATUS_LED", offset="0x6070" ),
         LedConfig( ledName="PSU2_STATUS_LED", offset="0x6080" ),
      ] )


class QuicksilverPFb( PlatformConfig ):
   codename = 'meru800ba'

   def __init__( self ):
      super().__init__( self.codename )

      self.addPmUnitConfigs( [
         QuicksilverPFbSCM(),
         QuicksilverPFbSMB()
      ] )

      self.addI2cAdaptersFromCpu( [ "SMBus I801 adapter at 1000" ] )

      self.addKmodsSettings(
         {
            "requiredKmodsToLoad": [ "spidev", "i2c_i801", "scd" ]
         }
      )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()
