# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from ..BaseConfigs import (
   FANCpld,
   PciDeviceConfig,
   PlatformConfig,
   SCMFairywren,
   SlotConfig,
   SMBCpld,
   SMBUnit,
   PSUUnit,
   LedConfig,
   Sensor,
   SensorConfig,
   SensorType,
   Thresholds
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

      smbFanCpld = FANCpld( "0x60", "meru800ba_fan_cpld", "FAN_CPLD",
                            incomingBusIndex=2 )
      smbFanCpld.addFANRpms( 4, upperCriticalVal=14900.0, lowerCriticalVal=1100.0 )

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=3,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )

      smbCpld = SMBCpld( "0x23", "meru800ba_cpld", "SMB_CPLD", incomingBusIndex=0 )

      smbFanTmp = Sensor( "0x48", "lm75", "FAN_TMP75", incomingBusIndex=2 )
      smbMgmtTemp = Sensor( "0x48", "lm75", "SMB_MGMT_TMP75" )
      smbMax = Sensor( "0x4D", "max6581", "SMB_MAX6581" )
      smbRaa = Sensor( "0x45", "raa228228", "SMB_RAA228926_TH5_CORE" )
      smbIsl0V9 = Sensor( "0x46", "isl68226", "SMB_ISL68226_TH5_0V9_ANALOG" )
      smbIsl0V75 = Sensor( "0x47", "isl68226", "SMB_ISL68226_TH5_0V75_ANALOG" )
      smbIslOpticsA = Sensor( "0x4D", "isl68226", "SMB_ISL68226_OPTICS_A" )
      smbIslOpticsB = Sensor( "0x4C", "isl68226", "SMB_ISL68226_OPTICS_B" )

      self.addI2cDeviceConfigs( [
         smbCpld,
         smbFanCpld,
         smbFanTmp,
         smbMgmtTemp,
         smbMax,
         smbRaa,
         smbIsl0V9,
         smbIsl0V75,
         smbIslOpticsA,
         smbIslOpticsB
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
      ] )

      smbI2cMaster0 = self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 0 ]
      smbI2cMaster1 = self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 1 ]

      smbI2cMaster0.buses[ 5 ].addI2cDevices( [ smbMgmtTemp ] )
      smbI2cMaster0.buses[ 0 ].addI2cDevices( [ smbMax ] )
      smbI2cMaster1.buses[ 0 ].addI2cDevices( [ smbRaa ] )
      smbI2cMaster1.buses[ 1 ].addI2cDevices( [ smbIsl0V9 ] )
      smbI2cMaster1.buses[ 2 ].addI2cDevices( [ smbIsl0V75 ] )
      smbI2cMaster1.buses[ 3 ].addI2cDevices( [ smbIslOpticsA ] )
      smbI2cMaster1.buses[ 4 ].addI2cDevices( [ smbIslOpticsB ] )

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="meru800ba_psu1_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ smbI2cMaster0.buses[ 3 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@1",
            presenceFileName="meru800ba_psu2_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ smbI2cMaster0.buses[ 4 ] ]
         ),
      ] )



class QuicksilverPFb( PlatformConfig ):
   codename = 'meru800ba'

   def __init__( self ):
      super().__init__( self.codename )

      self.addPmUnitConfigs( [
         QuicksilverPFbSCM(),
         QuicksilverPFbSMB(),
         PSUUnit()
      ] )

      self.addI2cAdaptersFromCpu( [ "SMBus I801 adapter at 1000" ] )

      self.addKmodsSettings(
         {
            "requiredKmodsToLoad": [ "spidev", "i2c_i801", "scd" ]
         }
      )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()
