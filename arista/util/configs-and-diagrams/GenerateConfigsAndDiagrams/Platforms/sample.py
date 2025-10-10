# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from GenerateConfigsAndDiagrams.BaseConfigs import (
   enumerateFANSlotConfigs,
   FANUnit,
   FANCpld,
   FanServiceConfig,
   Flash,
   GpioChip,
   I2cDeviceConfig,
   InitRegSettings,
   LedConfig,
   MiscConfig,
   OpticConfig,
   PciDeviceConfig,
   PlatformConfig,
   PSUUnit,
   Sensor,
   SensorConfig,
   SensorType,
   SCMUnit,
   SlotConfig,
   SMBUnit,
   SpiMasterConfig,
   Thresholds,
)


class _PLATFORM_NAME_SCM( SCMUnit ):
   def __init__( self ):
      super().__init__()

      self.setSlotTypeConfig(
         idPromConfigBusName="SMBus I801 adapter at 1000",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )


class _PLATFORM_NAME_SMB( SMBUnit ):
   prefixSymlink = '_PLATFORM_NAME_'

   def __init__( self ):
      super().__init__( self.prefixSymlink )
      self.fanServiceSensorConfigs = {}

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=1,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=0
      )


class _PLATFORM_NAME_( PlatformConfig ):
   codename = '_codename_'

   def __init__( self ):
      super().__init__( self.codename )
      self.addPmUnitConfigs( [
         _PLATFORM_NAME_SCM(),
         _PLATFORM_NAME_SMB(),
         PSUUnit(),
         FANUnit()
      ] )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()
      
      fanServiceConfig = FanServiceConfig()
      self.PlatformFanServiceConfig = fanServiceConfig
