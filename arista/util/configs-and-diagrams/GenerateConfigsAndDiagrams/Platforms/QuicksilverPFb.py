# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from ..BaseConfigs import (
   PlatformConfig,
   SCMFairywren
)


class QuicksilverPFbSCM( SCMFairywren ):
   def __init__( self ):
      super().__init__()


class QuicksilverPFb( PlatformConfig ):
   codename = 'meru800ba'
   supportsP1 = True

   def __init__( self ):
      super().__init__( self.codename )

      self.addPmUnitConfigs( [
         QuicksilverPFbSCM(),
      ] )

      self.addI2cAdaptersFromCpu( [ "SMBus I801 adapter at 1000" ] )

      self.addKmodsSettings(
         {
            "requiredKmodsToLoad": [ "spidev", "i2c-i801", "scd" ]
         }
      )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()
