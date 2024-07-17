# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import importlib
import unittest

from BaseConfigs import (
   PciDeviceConfig,
   PlatformConfig,
   PmUnitConfig
)
generator = importlib.import_module( "generate-pm-configs" )

 
class TestEmptyConfigs( unittest.TestCase ):

   def testDefaultPlatform( self ):
      platform = PlatformConfig( "test_platform" )
      pmconfigs = generator.PlatformConfig( platform )
      self.assertEqual( pmconfigs.platformName, "test_platform" )
      self.assertEqual( pmconfigs.rootPmUnitName, "SCM" )
      self.assertEqual( pmconfigs.slotTypeConfigs.getDict(), {} ) 
      self.assertEqual( pmconfigs.pmUnitConfigs.getDict(), {} )
      self.assertEqual( 
         pmconfigs.i2cAdaptersFromCpu.getList(), 
         [ "SMBus I801 adapter at 1000" ]
      )
      self.assertEqual( 
         pmconfigs.kmodsSettings[ "bspKmodsRpmName" ],
         "arista_bsp_kmods"
      )
      self.assertEqual(
         str( pmconfigs.kmodsSettings[ "bspKmodsRpmVersion" ] ), 
         "0.7.2-1"
      )
      self.assertEqual(
         pmconfigs.kmodsSettings[ "bspKmodsToReload" ].split( ", " ),
         [ "scd-xcvr", "scd-spi", "scd-leds", "scd-smbus", "dsf-fan-cpld" ]
      )
      self.assertEqual(
         pmconfigs.kmodsSettings[ "sharedKmodsToReload" ].split( ", " ),
         [ "scd" ]
      )
      self.assertEqual(
         pmconfigs.kmodsSettings[ "upstreamKmodsToLoad" ].split( ", " ),
         [ "spidev", "i2c-i801" ] 
      )

   def testEmptyPmUnitConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [
         PmUnitConfig( "TEST_UNIT" )
      ] )
      pmconfigs = generator.PlatformConfig( platform )
      pmUnitDict = pmconfigs.pmUnitConfigs.getDict()
      self.assertTrue( "TEST_UNIT" in pmUnitDict.keys() )
      testUnitConfig = pmUnitDict[ "TEST_UNIT" ]
      self.assertEqual( testUnitConfig[ "pluggedInSlotType" ], "TEST_UNIT_SLOT" )
      self.assertEqual( testUnitConfig[ "i2cDeviceConfigs" ], [] )
      self.assertEqual( testUnitConfig[ "outgoingSlotConfigs" ], {} )
      self.assertEqual( testUnitConfig[ "pciDeviceConfigs" ], [] )

   def testEmptyPciDeviceConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [
         PmUnitConfig( "TEST_UNIT" )
      ] )
      platform.pmUnitConfigs[ 0 ].addPciDeviceConfigs( [
         PciDeviceConfig(
            pmUnitScopedName="TEST_FPGA",
            vendorId="0x3475",
            deviceId="0x0001",
            subSystemVendorId="0x3475",
            subSystemDeviceId="0x0003"
         )
      ] )
      pmconfigs = generator.PlatformConfig( platform )
      pmUnitDict = pmconfigs.pmUnitConfigs.getDict()
      testUnitConfig = pmUnitDict[ "TEST_UNIT" ]
      self.assertEqual( len( testUnitConfig[ "pciDeviceConfigs" ] ), 1 )
      testPciConfig = testUnitConfig[ "pciDeviceConfigs" ][ 0 ]
      self.assertEqual( testPciConfig[ "pmUnitScopedName" ], "TEST_FPGA" )
      self.assertEqual( testPciConfig[ "vendorId" ], "0x3475" )
      self.assertEqual( testPciConfig[ "deviceId" ], "0x0001" )
      self.assertEqual( testPciConfig[ "subSystemVendorId" ], "0x3475" )
      self.assertEqual( testPciConfig[ "subSystemDeviceId" ], "0x0003" )
      self.assertEqual( testPciConfig[ "i2cAdapterConfigs" ], [] )
      self.assertEqual( testPciConfig[ "spiMasterConfigs" ], [] )
      self.assertEqual( testPciConfig[ "ledCtrlConfigs" ], [] )
      self.assertEqual( testPciConfig[ "xcvrCtrlConfigs" ], [] ) 


class TestEnumerationFunctions( unittest.TestCase ):

   def testXcvrConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [
         PmUnitConfig( "TEST_UNIT" )
      ] )
      platform.pmUnitConfigs[ 0 ].addPciDeviceConfigs( [
         PciDeviceConfig(
            pmUnitScopedName="TEST_FPGA",
            vendorId="0x3475",
            deviceId="0x0001",
            subSystemVendorId="0x3475",
            subSystemDeviceId="0x0003"
         )
      ] )
      platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addXcvrCtrlConfigs( 
         numConfigs=32, 
         basePortNumber=1,
         portType="test",
         xcvrBaseOffset="0x0000", 
         led1BaseOffset="0x1000", 
         led2BaseOffset="0x1010"
      )
      pmconfigs = generator.PlatformConfig( platform )
      pmUnitDict = pmconfigs.pmUnitConfigs.getDict()
      testUnitConfig = pmUnitDict[ "TEST_UNIT" ]
      testXcvrConfig = testUnitConfig[ "pciDeviceConfigs" ][ 0 ][ "xcvrCtrlConfigs" ]
      testLedConfig = testUnitConfig[ "pciDeviceConfigs" ][ 0 ][ "ledCtrlConfigs" ]
      self.assertEqual( len( testXcvrConfig ), 32 )
      self.assertEqual(
         testXcvrConfig[ 0 ][ "fpgaIpBlockConfig" ][ "pmUnitScopedName" ],
         "TEST_PORT1_XCVR"
      )
      for i in range( 32 ):
         self.assertEqual(
            testXcvrConfig[ i ][ "fpgaIpBlockConfig" ][ "csrOffset" ], 
            hex( 0x0000 + i * 0x10 )
         )
         self.assertEqual( testXcvrConfig[ i ][ "portNumber" ], i+1 )
      self.assertEqual( len( testLedConfig ), 64 )
      self.assertEqual(
         testLedConfig[ 0 ][ "fpgaIpBlockConfig" ][ "pmUnitScopedName" ],
         "TEST_PORT1_LED1"
      )
      for i in range( 64 ):
         self.assertEqual(
            testLedConfig[ i ][ "fpgaIpBlockConfig" ][ "csrOffset" ],
            hex( 0x1000 + i * 0x10 )
         )
         if i % 2 == 0:
            self.assertEqual( testLedConfig[ i ][ "ledId" ], 1 )
         else:
            self.assertEqual( testLedConfig[ i ][ "ledId" ], 2 )

   def testI2cAdapterConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [
         PmUnitConfig( "TEST_UNIT" )
      ] )
      platform.pmUnitConfigs[ 0 ].addPciDeviceConfigs( [
         PciDeviceConfig(
            pmUnitScopedName="TEST_FPGA8",
            vendorId="0x3475",
            deviceId="0x0001",
            subSystemVendorId="0x3475",
            subSystemDeviceId="0x0003"
         )
      ] )
      platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addI2cAdapterConfigs(
         numAdapters=20, 
         adapterBaseName="SMB_FPGA{}_I2C_MASTER{}", 
         baseCsrOffset="0x4000"
      )
      pmconfigs = generator.PlatformConfig( platform )
      pmUnitDict = pmconfigs.pmUnitConfigs.getDict()
      testUnitConfig = pmUnitDict[ "TEST_UNIT" ]
      config = testUnitConfig[ "pciDeviceConfigs" ][ 0 ][ "i2cAdapterConfigs" ]
      self.assertEqual( len( config ), 20 )
      for i in range( 20 ):
         self.assertEqual(
            config[ i ][ "fpgaIpBlockConfig" ][ "pmUnitScopedName" ],
            f"SMB_FPGA8_I2C_MASTER{ i }"
         )
         self.assertEqual(
            config[ i ][ "fpgaIpBlockConfig" ][ "csrOffset" ],
            hex( 0x4000 + i * 0x80 )
         )


if __name__ == '__main__':
   unittest.main()
