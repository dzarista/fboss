# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import unittest

from BaseConfigs import (
   EmbeddedSensorConfig,
   Flash,
   GpioChip,
   InitRegSettings,
   I2cDeviceConfig,
   LedConfig,
   PciDeviceConfig,
   PlatformConfig,
   PmUnitConfig,
   SlotConfig,
   SpiMasterConfig
)


class PlatformConfigTest( unittest.TestCase ):

   def testEmptyPlatform( self ):
      platform = PlatformConfig( "test_platform" )
      self.assertEqual( platform.platformName, "test_platform" )
      self.assertEqual( platform.rootPmUnitName, "SCM" )
      self.assertEqual( platform.getSlotTypeConfigsDict(), {} ) 
      self.assertEqual( platform.getPmUnitConfigsDict(), {} )
      self.assertEqual( 
         platform.i2cAdaptersFromCpu, 
         [ "SMBus I801 adapter at 1000" ]
      )
      self.assertEqual( 
         platform.kmodsSettings[ "bspKmodsRpmName" ],
         "arista_bsp_kmods"
      )
      self.assertEqual(
         str( platform.kmodsSettings[ "bspKmodsRpmVersion" ] ), 
         "0.7.2-1"
      )
      self.assertEqual(
         platform.kmodsSettings[ "bspKmodsToReload" ],
         [ "scd-xcvr", "scd-spi", "scd-leds", "scd-smbus", "dsf-fan-cpld" ]
      )
      self.assertEqual(
         platform.kmodsSettings[ "sharedKmodsToReload" ],
         [ "scd" ]
      )
      self.assertEqual(
         platform.kmodsSettings[ "upstreamKmodsToLoad" ],
         [ "spidev", "i2c-i801" ] 
      )

   def testAddPmUnitConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs(
         [ PmUnitConfig( pmUnitName="SCM" ), PmUnitConfig( pmUnitName="SMB" ) ]
      )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertEqual( len( pmUnitDict ), 2 )
      self.assertTrue( "SCM" in pmUnitDict )
      self.assertTrue( "SMB" in pmUnitDict )


class SlotTypeConfigTest( unittest.TestCase ):

   def testDefaultSlot( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SCM" ) ] )
      platform.pmUnitConfigs[ 0 ].setSlotTypeConfig()
      jsonDict = platform.getSlotTypeConfigsDict()
      self.assertTrue( "SCM_SLOT" in jsonDict )
      self.assertTrue( "numOutgoingI2cBuses" in jsonDict[ "SCM_SLOT" ] )
      self.assertTrue( "pmUnitName" in jsonDict[ "SCM_SLOT" ] )
      self.assertTrue( "idpromConfig" not in jsonDict[ "SCM_SLOT" ] )

   def testWithIdPromConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SMB" ) ] )
      platform.pmUnitConfigs[ 0 ].setSlotTypeConfig(
         numOutgoingI2cBuses=4,
         idPromConfigBusName="INCOMING@42",
         idPromConfigAddress="0x52",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=12000
      )
      jsonDict = platform.getSlotTypeConfigsDict()
      self.assertTrue( "SMB_SLOT" in jsonDict )
      self.assertTrue( "idpromConfig" in jsonDict[ "SMB_SLOT" ] )
      self.assertEqual( 
         jsonDict[ "SMB_SLOT" ][ "idpromConfig" ][ "busName" ], 
         "INCOMING@42" 
      )
      self.assertEqual( 
         jsonDict[ "SMB_SLOT" ][ "idpromConfig" ][ "address" ],
         "0x52"
      )
      self.assertEqual( 
         jsonDict[ "SMB_SLOT" ][ "idpromConfig" ][ "kernelDeviceName" ], 
         "24c512" 
      )
      self.assertEqual( jsonDict[ "SMB_SLOT" ][ "idpromConfig" ][ "offset" ], 12000 )

   def testWithInvalidIdPromConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="PSU" ) ] )
      platform.pmUnitConfigs[ 0 ].setSlotTypeConfig(
         numOutgoingI2cBuses=1,
         idPromConfigBusName="INCOMING@7",
         idPromConfigAddress="0x42",
         idPromConfigOffset=13500
      )
      with self.assertRaises( AssertionError ):
         platform.getSlotTypeConfigsDict()


class PmUnitConfigTest( unittest.TestCase ):

   def testEmptyPmUnitConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( "TEST_UNIT" ) ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertTrue( "TEST_UNIT" in pmUnitDict.keys() )
      testUnitConfig = pmUnitDict[ "TEST_UNIT" ]
      self.assertEqual( testUnitConfig[ "pluggedInSlotType" ], "TEST_UNIT_SLOT" )
      self.assertEqual( testUnitConfig[ "i2cDeviceConfigs" ], [] )
      self.assertEqual( testUnitConfig[ "outgoingSlotConfigs" ], {} )
      self.assertEqual( testUnitConfig[ "pciDeviceConfigs" ], [] )

   def testAddI2cDeviceConfigs( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SCM" ) ] )
      platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         I2cDeviceConfig("0x23", "decker_cpld", "SMB_CPLD", incomingBusIndex=0 ),
         I2cDeviceConfig("0x4D", "max6581", "SMB_MAX6581", incomingBusIndex=13 )
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertTrue( "i2cDeviceConfigs" in pmUnitDict[ "SCM" ] )
      self.assertEqual( len( pmUnitDict[ "SCM" ][ "i2cDeviceConfigs" ] ), 2 )
      self.assertEqual(
         pmUnitDict[ "SCM" ][ "i2cDeviceConfigs" ][ 0 ][ "busName" ],
         "INCOMING@0"
      )
      self.assertEqual(
         pmUnitDict[ "SCM" ][ "i2cDeviceConfigs" ][ 1 ][ "busName" ],
         "INCOMING@13"
      )

   def testAddOutgoingSlotConfigs( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SMB" ) ] )
      platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs( [
         SlotConfig( slotName="FAN_SLOT@0" ),
         SlotConfig( slotName="FAN_SLOT@1" )
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertTrue( "outgoingSlotConfigs" in pmUnitDict[ "SMB" ] )
      self.assertEqual( len( pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ] ), 2 )
      self.assertTrue( "FAN_SLOT@0" in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ] )
      self.assertTrue( "FAN_SLOT@1" in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ] )

   def testAddPciDeviceConfigs( self ):
      platform = PlatformConfig( "test_platform" ) 
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SMB" ) ] )
      platform.pmUnitConfigs[ 0 ].addPciDeviceConfigs( [
         PciDeviceConfig( "SMB_FPGA13", "0x3475", "0x0001", "0x3475", "0x0003" ),
         PciDeviceConfig( "SMB_FPGA7", "0x1500", "0x0002", "0x1500", "0x0004" )
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertTrue( "pciDeviceConfigs" in pmUnitDict[ "SMB" ] )
      self.assertEqual( len( pmUnitDict[ "SMB" ][ "pciDeviceConfigs" ] ), 2 )
      self.assertEqual( 
         pmUnitDict[ "SMB" ][ "pciDeviceConfigs" ][ 0 ][ "pmUnitScopedName" ],
         "SMB_FPGA13"
      )
      self.assertEqual( 
         pmUnitDict[ "SMB" ][ "pciDeviceConfigs" ][ 1 ][ "pmUnitScopedName" ],
         "SMB_FPGA7"
      )

   def testAddEmbeddedSensorConfigs( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SCM" ) ] )
      platform.pmUnitConfigs[ 0 ].addEmbeddedSensorConfigs( [
         EmbeddedSensorConfig( 
            pmUnitScopedName="CPU_CORE_TEMP0", 
            sysfsPath="/sys/bus/platform/devices/coretemp.0" 
         ),
         EmbeddedSensorConfig( 
            pmUnitScopedName="CPU_CORE_TEMP1", 
            sysfsPath="/sys/bus/platform/devices/coretemp.1" 
         )
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertTrue( "embeddedSensorConfigs" in pmUnitDict[ "SCM" ] )
      self.assertEqual( len( pmUnitDict[ "SCM" ][ "embeddedSensorConfigs" ] ), 2 )
      self.assertEqual( 
         pmUnitDict[ "SCM" ][ "embeddedSensorConfigs" ][ 0 ][ "pmUnitScopedName" ],
         "CPU_CORE_TEMP0"
      )
      self.assertEqual( 
         pmUnitDict[ "SCM" ][ "embeddedSensorConfigs" ][ 1 ][ "pmUnitScopedName" ],
         "CPU_CORE_TEMP1"
      )


class EmbeddedSensorConfigTest( unittest.TestCase ):

   def testIncompleteConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SCM" ) ] )
      platform.pmUnitConfigs[ 0 ].addEmbeddedSensorConfigs( [
         EmbeddedSensorConfig( "CPU_CORE_TEMP2", "" )
      ] )
      with self.assertRaises( AssertionError ):
         platform.getPmUnitConfigsDict()


class I2cDeviceConfigTest( unittest.TestCase ):

   def setUp( self ):
      self.platform = PlatformConfig( "test_platform" )
      self.platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SCM" ) ] )

   def testIncompleteConfig( self ):
      self.platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         I2cDeviceConfig("0x5A", "isl68226", None, incomingBusIndex=1 )
      ] )
      with self.assertRaises( AssertionError ):
         self.platform.getPmUnitConfigsDict()

   def testNoExtraFields( self ):
      self.platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         I2cDeviceConfig("0x5B", "isl68226", "SMB_ISL68226_OSFP_TR",
                         incomingBusIndex=1 )
      ] )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      self.assertTrue(
         "initRegSettings" not in pmUnitDict[ "SCM" ][ "i2cDeviceConfigs" ][ 0 ]
      )

   def testOptionalFieldPresent( self ):
      self.platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         GpioChip( "0x74", "pca9539", "SMB_PCA", incomingBusIndex=1 )
      ] )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      self.assertTrue(
         "isGpioChip" in pmUnitDict[ "SCM" ][ "i2cDeviceConfigs" ][ 0 ]
      )
      self.assertTrue( 
         pmUnitDict[ "SCM" ][ "i2cDeviceConfigs" ][ 0 ][ "isGpioChip" ]
      )

   def testInitRegSettings( self ):
      self.platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         I2cDeviceConfig( "0x4D", "max6581", "SMB_MAX6581", incomingBusIndex=1,
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
                        ),
      ] )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      self.assertTrue(
         "initRegSettings" in pmUnitDict[ "SCM" ][ "i2cDeviceConfigs" ][ 0 ]
      )
      self.assertEqual(
         len( pmUnitDict[ "SCM" ][ "i2cDeviceConfigs" ][ 0 ][ "initRegSettings" ] ),
         8
      )


class SlotConfigTest( unittest.TestCase ):

   def testNoExtraFields( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SMB" ) ] )
      platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs( [
         SlotConfig( slotName="FAN_SLOT@1" )
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertTrue(
         "FAN_SLOT@1" in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ]
      )
      self.assertTrue(
         "presenceDetection" 
         not in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ][ "FAN_SLOT@1" ]
      )

   def testIncorrectPresenceDetection( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SMB" ) ] )
      platform.pmUnitConfigs[ 0 ].addPciDeviceConfigs( [
         PciDeviceConfig( "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0003" )
      ] )
      platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addI2cAdapterConfigs(
         2, "SMB_I2C_MASTER{}", "0x8000"
      )
      platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ 
               platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ]
               .i2cAdapterConfigs[ 0 ].buses[ 5 ] 
            ]
         )
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertTrue(
         "PSU_SLOT@0" in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ]
      )
      self.assertTrue(
         "presenceDetection" 
         not in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ][ "PSU_SLOT@0" ]
      )
      self.assertEqual(
         pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ][ "PSU_SLOT@0" ]
                   [ "outgoingI2cBusNames" ],
         [ "SMB_I2C_MASTER0@5" ]
      )

   def testCompletePresenceDetection( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SMB" ) ] )
      platform.pmUnitConfigs[ 0 ].addPciDeviceConfigs( [
         PciDeviceConfig( "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0003" )
      ] )
      platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addI2cAdapterConfigs(
         2, "SMB_I2C_MASTER{}", "0x8000"
      )
      platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="psu1_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[
               platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ]
               .i2cAdapterConfigs[ 1 ].buses[ 6 ] 
            ]
         )
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertTrue(
         "PSU_SLOT@0" in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ]
      )
      self.assertTrue(
         "presenceDetection" 
         in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ][ "PSU_SLOT@0" ]
      )
      self.assertEqual(
         pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ][ "PSU_SLOT@0" ]
                   [ "presenceDetection" ][ "sysfsFileHandle" ][ "devicePath" ],
         "/SMB_SLOT@0/[SMB_FPGA]"
      )


class PciDeviceConfigTest( unittest.TestCase ):

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
      pmUnitDict = platform.getPmUnitConfigsDict()
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


class I2cAdapterConfigTest( unittest.TestCase ):

   def setUp( self ):
      self.platform = PlatformConfig( "test_platform" )
      self.platform.addPmUnitConfigs( [
         PmUnitConfig( "SCM" ),
         PmUnitConfig( "SMB" )
      ] )
      self.platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs(
         [ SlotConfig( slotName="SMB_SLOT@21" ) ]
      )
      # Make sure that the function is robust to handle multi-digit device numbers
      self.platform.pmUnitConfigs[ 1 ].addPciDeviceConfigs( [
         PciDeviceConfig(
            pmUnitScopedName="SMB_FPGA13",
            vendorId="0x3475",
            deviceId="0x0001",
            subSystemVendorId="0x3475",
            subSystemDeviceId="0x0003"
         )
      ] )

   def testAddI2cAdapterConfigs( self ):
      self.platform.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 0 ].addI2cAdapterConfigs(
         numAdapters=20, 
         adapterBaseName="SMB_FPGA{}_I2C_MASTER{}", 
         baseCsrOffset="0x4000"
      )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      testUnitConfig = pmUnitDict[ "SMB" ]
      config = testUnitConfig[ "pciDeviceConfigs" ][ 0 ][ "i2cAdapterConfigs" ]
      self.assertEqual( len( config ), 20 )
      for i in range( 20 ):
         self.assertEqual(
            config[ i ][ "fpgaIpBlockConfig" ][ "pmUnitScopedName" ],
            f"SMB_FPGA13_I2C_MASTER{ i }"
         )
         self.assertEqual(
            config[ i ][ "fpgaIpBlockConfig" ][ "csrOffset" ],
            hex( 0x4000 + i * 0x80 )
         )

   def testI2cBuses( self ):
      self.platform.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 0 ].addI2cAdapterConfigs(
         numAdapters=12, 
         adapterBaseName="SMB_FPGA{}_I2C_MASTER{}", 
         baseCsrOffset="0x4000"
      )
      self.platform.pmUnitConfigs[ 1 ].populateSymlinkToDevicePaths()
      symlinkDict = self.platform.parseSymbolicLinkToDevicePaths()
      self.assertEqual( len( symlinkDict.keys() ), 12 * 8 + 1 )
      self.assertTrue( "/run/devmap/fpgas/TEST_PLATFORM_SMB_FPGA13" in symlinkDict )
      self.assertEqual( 
         symlinkDict[ "/run/devmap/fpgas/TEST_PLATFORM_SMB_FPGA13" ],
         "/SMB_SLOT@21/[SMB_FPGA13]"
      )
      self.assertTrue( 
         "/run/devmap/i2c-busses/TEST_PLATFORM_SMB_FPGA13_SMBUS11_CH7" in symlinkDict
      )
      self.assertEqual(
         symlinkDict["/run/devmap/i2c-busses/TEST_PLATFORM_SMB_FPGA13_SMBUS11_CH7"],
         "/SMB_SLOT@21/[SMB_FPGA13_I2C_MASTER11@7]"
      )
      self.assertFalse(
         "/run/devmap/i2c-busses/TEST_PLATFORM_SMB_FPGA13_SMBUS11_CH8" in symlinkDict
      )
      self.assertFalse(
         "/run/devmap/i2c-busses/TEST_PLATFORM_SMB_FPGA13_SMBUS12_CH7" in symlinkDict
      )


class SpiMasterConfigTest( unittest.TestCase ):

   def setUp( self ):
      self.platform = PlatformConfig( "test_platform" )
      self.platform.addPmUnitConfigs( [ PmUnitConfig( "SCM" ) ] )
      self.platform.pmUnitConfigs[ 0 ].addPciDeviceConfigs( [
         PciDeviceConfig(
            pmUnitScopedName="SCM_FPGA",
            vendorId="0x3475",
            deviceId="0x0001",
            subSystemVendorId="0x3475",
            subSystemDeviceId="0x0003"
         )
      ] )

   def testNoSpiDeviceConfig( self ):
      self.platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addSpiMasterConfigs( [
         SpiMasterConfig( "SCM_SPI_MASTER0", "spi_master", -1, "0x7900" )
      ] )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      testUnitConfig = pmUnitDict[ "SCM" ]
      config = testUnitConfig[ "pciDeviceConfigs" ][ 0 ][ "spiMasterConfigs" ][ 0 ]
      self.assertFalse( "spiDeviceConfigs" in config )
      self.assertFalse( "iobufOffset" in config[ "fpgaIpBlockConfig" ] )
      self.assertEqual( 
         config[ "fpgaIpBlockConfig" ][ "pmUnitScopedName" ],
         "SCM_SPI_MASTER0"
      )

   def testSpiDeviceConfig( self ):
      self.platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addSpiMasterConfigs( [
         SpiMasterConfig( "SCM_SPI_MASTER0", "spi_master", "0x80", "0x7900",
                           spiDeviceConfigs=[ 
                              Flash(
                                 pmUnitScopedName="SMB_SPI_MASTER0_DEVICE42",
                                 chipSelect=0,
                                 modalias="spidev",
                                 maxSpeedHz=25000000
                              )
                           ] 
                        )
      ] )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      testUnitConfig = pmUnitDict[ "SCM" ]
      config = testUnitConfig[ "pciDeviceConfigs" ][ 0 ][ "spiMasterConfigs" ][ 0 ]
      self.assertTrue( "spiDeviceConfigs" in config )
      self.assertTrue( "iobufOffset" in config[ "fpgaIpBlockConfig" ] )
      self.assertEqual( 
         config[ "fpgaIpBlockConfig" ][ "iobufOffset" ], str( int( "0x80", 16 ) )
      )
      self.assertEqual( len( config[ "spiDeviceConfigs" ] ), 1 )
      self.assertEqual(
         config[ "spiDeviceConfigs" ][ 0 ][ "pmUnitScopedName" ],
         "SMB_SPI_MASTER0_DEVICE42"
      )

   def testIncompleteConfig( self ):
      self.platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addSpiMasterConfigs( [
         SpiMasterConfig( "SCM_SPI_MASTER0", "spi_master", -1, None )
      ] )
      with self.assertRaises( AssertionError ):
         self.platform.getPmUnitConfigsDict()


class XcvrConfigTest( unittest.TestCase ):

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
      pmUnitDict = platform.getPmUnitConfigsDict()
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
            hex( 0x00 + i * 0x10 )
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


class LedConfigTest( unittest.TestCase ):

   def setUp( self ):
      self.platform = PlatformConfig( "test_platform" )
      self.platform.addPmUnitConfigs( [ PmUnitConfig( "SCM" ) ] )
      self.platform.pmUnitConfigs[ 0 ].addPciDeviceConfigs( [
         PciDeviceConfig(
            pmUnitScopedName="SCM_FPGA",
            vendorId="0x3475",
            deviceId="0x0001",
            subSystemVendorId="0x3475",
            subSystemDeviceId="0x0003"
         )
      ] )

   def testLedDeviceNames( self ):
      self.platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addLedCtrlConfigs( [
            LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
            LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
            LedConfig( ledName="TEST_LED", offset="0x6070" )
      ] )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      config = pmUnitDict[ "SCM" ][ "pciDeviceConfigs" ][ 0 ][ "ledCtrlConfigs" ]
      self.assertEqual( len( config ), 3 )
      self.assertEqual(
         config[ 0 ][ "fpgaIpBlockConfig" ][ "deviceName" ],
         "sys_led"
      )
      self.assertEqual(
         config[ 1 ][ "fpgaIpBlockConfig" ][ "deviceName" ],
         "fan_led"
      )
      self.assertEqual(
         config[ 2 ][ "fpgaIpBlockConfig" ][ "deviceName" ],
         "tes_led"
      )

   def testIncompleteLedConfig( self ):
      self.platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addLedCtrlConfigs( [
            LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
            LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
            LedConfig( ledName="TEST_LED", offset=None )
      ] )
      with self.assertRaises( AssertionError ):
         self.platform.getPmUnitConfigsDict()


if __name__ == '__main__':
   unittest.main()
