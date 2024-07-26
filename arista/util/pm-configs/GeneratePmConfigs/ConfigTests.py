# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import re
import unittest

from BaseConfigs import (
   EmbeddedSensorConfig,
   enumerateFANSlotConfigs,
   enumeratePciDeviceConfigs,
   FANCpld,
   FANUnit,
   Flash,
   GpioChip,
   InitRegSettings,
   I2cDeviceConfig,
   LedConfig,
   PciDeviceConfig,
   PlatformConfig,
   PSUBus,
   PSUUnit,
   PmUnitConfig,
   SCMIdProm,
   SCMUnit,
   Sensor,
   SlotConfig,
   SMBCpld,
   SMBUnit,
   SpiDeviceConfig,
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

   def testBasePmUnitConfigs( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [
         SCMUnit(),
         SMBUnit(),
         PSUUnit(),
         FANUnit()
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      self.assertEqual( len( pmUnitDict ), 4 )
      self.assertTrue( "SCM" in pmUnitDict )
      self.assertTrue( "SMB" in pmUnitDict )
      self.assertTrue( "PSU" in pmUnitDict )
      self.assertTrue( "FAN" in pmUnitDict )
      self.assertEqual( len( pmUnitDict[ "PSU" ][ "i2cDeviceConfigs" ] ), 1 )


class EmbeddedSensorConfigTest( unittest.TestCase ):

   def testIncompleteConfig( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SCM" ) ] )
      platform.pmUnitConfigs[ 0 ].addEmbeddedSensorConfigs( [
         EmbeddedSensorConfig( "CPU_CORE_TEMP2", "" )
      ] )
      with self.assertRaises( AssertionError ):
         platform.getPmUnitConfigsDict()

   def testSymlinkToDevicePath( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SCM" ) ] )
      platform.pmUnitConfigs[ 0 ].addEmbeddedSensorConfigs( [
         EmbeddedSensorConfig(
            "CPU_CORE_TEMP2",
            "/sys/bus/platform/devices/coretemp.2"
         )
      ] )
      platform.pmUnitConfigs[ 0 ].populateSymlinkToDevicePaths()
      symlinkDict = platform.parseSymbolicLinkToDevicePaths()
      self.assertTrue( "/run/devmap/sensors/CPU_CORE_TEMP2" in symlinkDict )
      self.assertEqual(
         symlinkDict[ "/run/devmap/sensors/CPU_CORE_TEMP2"],
         "/[CPU_CORE_TEMP2]"
      )


class I2cDeviceConfigTest( unittest.TestCase ):

   def setUp( self ):
      self.platform = PlatformConfig( "test_platform" )
      self.platform.addPmUnitConfigs( [ 
         PmUnitConfig( pmUnitName="SCM" ),
         PmUnitConfig( pmUnitName="SMB" ),
         PmUnitConfig( pmUnitName="PSU" )
      ] )

   def testIncompleteConfig( self ):
      self.platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         I2cDeviceConfig( "0x5A", "isl68226", None, incomingBusIndex=1 )
      ] )
      with self.assertRaises( AssertionError ):
         self.platform.getPmUnitConfigsDict()

   def testNoExtraFields( self ):
      self.platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         I2cDeviceConfig( "0x5B", "isl68226", "SMB_ISL68226_OSFP_TR",
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
      jsonDump = self.platform.asJson()
      pattern = re.compile( r'"ioBuf": \[[^\]]*\]' )
      matches = pattern.findall( jsonDump )
      oneLiner = re.compile( r'"ioBuf": \[-?\d+\]' )
      for match in matches:
         self.assertRegex( match, oneLiner )

   def testSymlinkToDevicePaths( self ):
      self.platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         GpioChip( "0x74", "pca9539", "SCM_PCA" ),
         Sensor( "0x30", "pxm1310", "SCM_PXM1310_1" ),
         SCMIdProm( "0x50", "24c512", "SCM_IDPROM_P2", hasCpuMac=True ),
      ] )
      # Note that on a real platform, FAN_CPLD and FAN0_CPLD would not co-exist
      # together. This is simply for symlink testing purposes.
      self.platform.pmUnitConfigs[ 1 ].addI2cDeviceConfigs( [
         FANCpld( "0x60", "pali2_cpld", "FAN_CPLD", incomingBusIndex=2 ),
         FANCpld( "0x61", "oasis_cpld0", "FAN0_CPLD", incomingBusIndex=3 ),
         SMBCpld( "0x23", "decker_cpld", "SMB_CPLD", incomingBusIndex=0 )
      ] )
      self.platform.pmUnitConfigs[ 2 ].addI2cDeviceConfigs( [
         PSUBus( "0x58", "pmbus", "PSU_PMBUS", incomingBusIndex=0 )
      ] )
      scmUnit = self.platform.pmUnitConfigs[ 0 ]
      scmUnit.addPciDeviceConfigs( [
         *enumeratePciDeviceConfigs( 1, "SCM_FPGA", "0x3475", "0x0001", "0x3475", 
                                     "0x0008" )
      ] )
      scmUnit.pciDeviceConfigs[ 0 ].addI2cAdapterConfigs(
         1, "SCM_I2C_MASTER{}", "0x8000" 
      )
      scmUnit.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 0 ].addDevicesOnAdapters(
         {
            3 : [ scmUnit.i2cDeviceConfigs[ 0 ] ],
            4 : [ scmUnit.i2cDeviceConfigs[ 1 ] ],
            5 : [ scmUnit.i2cDeviceConfigs[ 2 ] ]
         }
      )
      scmUnit.addOutgoingSlotConfigs( [
         SlotConfig( slotName="SMB_SLOT@7" )
      ] )
      self.platform.pmUnitConfigs[ 1 ].addOutgoingSlotConfigs( [ 
         SlotConfig( slotName="PSU_SLOT@13" ),
         SlotConfig( slotName="PSU_SLOT@31" )
      ] )
      for pmConfig in self.platform.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()
      symlinkDict = self.platform.parseSymbolicLinkToDevicePaths()

      '''
      8 symlinks for i2c buses
      1 for SCM_FPGA
      3 for SCM i2c devices
      4 symlinks for 2 FAN Cplds
      1 for SMB Cpld
      1 for SMB Idprom (generated automatically)
      2 for PSU buses
      '''
      self.assertEqual( len( symlinkDict ), 20 )
      self.assertTrue( "/run/devmap/gpiochips/SCM_PCA" in symlinkDict )
      self.assertEqual( 
         symlinkDict[ "/run/devmap/gpiochips/SCM_PCA" ], "/[SCM_PCA]"
      )
      self.assertTrue( "/run/devmap/sensors/CPU_PXM1310_1" in symlinkDict )
      self.assertEqual(
         symlinkDict[ "/run/devmap/sensors/CPU_PXM1310_1" ],
         "/[SCM_PXM1310_1]"
      )
      self.assertTrue( "/run/devmap/eeproms/MERU_SCM_EEPROM_P2" in symlinkDict )
      self.assertEqual(
         symlinkDict[ "/run/devmap/eeproms/MERU_SCM_EEPROM_P2" ],
         "/[SCM_IDPROM_P2]"
      )
      self.assertTrue( "/run/devmap/sensors/FAN_CPLD" in symlinkDict )
      self.assertTrue( "/run/devmap/cplds/FAN_CPLD" in symlinkDict )
      self.assertEqual(
         symlinkDict[ "/run/devmap/cplds/FAN_CPLD" ],
         '/SMB_SLOT@7/[FAN_CPLD]'
      )
      self.assertTrue( "/run/devmap/sensors/FAN_CPLD0" in symlinkDict )
      self.assertTrue( "/run/devmap/cplds/FAN0_CPLD" in symlinkDict )
      self.assertEqual(
         symlinkDict[ "/run/devmap/cplds/FAN0_CPLD" ],
         '/SMB_SLOT@7/[FAN0_CPLD]'
      )
      self.assertTrue( "/run/devmap/cplds/TEST_PLATFORM_SMB_CPLD" in symlinkDict )
      self.assertEqual(
         symlinkDict[ "/run/devmap/cplds/TEST_PLATFORM_SMB_CPLD" ],
         "/SMB_SLOT@7/[SMB_CPLD]"
      )
      self.assertTrue( "/run/devmap/sensors/PSU14_PMBUS" in symlinkDict )
      self.assertTrue( "/run/devmap/sensors/PSU32_PMBUS" in symlinkDict )
      self.assertEqual(
         symlinkDict[ "/run/devmap/sensors/PSU14_PMBUS" ],
         "/SMB_SLOT@7/PSU_SLOT@13/[PSU_PMBUS]"
      )
      self.assertEqual(
         symlinkDict[ "/run/devmap/sensors/PSU32_PMBUS" ],
         "/SMB_SLOT@7/PSU_SLOT@31/[PSU_PMBUS]"
      )

   def testDefaultI2cDeviceNoSymlink( self ):
      self.platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         I2cDeviceConfig( "0x49", "tmp75", "SMB_TMP75_FRONT", incomingBusIndex=1 )
      ] )
      self.platform.pmUnitConfigs[ 0 ].populateSymlinkToDevicePaths()
      symlinkDict = self.platform.parseSymbolicLinkToDevicePaths()
      self.assertEqual( len( symlinkDict ), 0 )


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

   def testEnumerateSimpleFANSlotConfigs( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SMB" ) ] )
      platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs( [
         *enumerateFANSlotConfigs( 8, "/SMB_SLOT@0/[FAN_CPLD]" )
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      for i in range( 8 ):
         self.assertTrue(
            f"FAN_SLOT@{ i }" in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ]
         )
         self.assertEqual(
            pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ][ f"FAN_SLOT@{ i }" ][
               "presenceDetection" ][ "sysfsFileHandle" ][ "devicePath" ],
            "/SMB_SLOT@0/[FAN_CPLD]"
         )

   def testEnumerateFormattedFANSlotConfigs( self ):
      platform = PlatformConfig( "test_platform" )
      platform.addPmUnitConfigs( [ PmUnitConfig( pmUnitName="SMB" ) ] )
      platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs( [
         *enumerateFANSlotConfigs( 16, "/SMB_SLOT@0/[FAN{}_CPLD]" )
      ] )
      pmUnitDict = platform.getPmUnitConfigsDict()
      for i in range( 16 ):
         self.assertTrue(
            f"FAN_SLOT@{ i }" in pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ]
         )
         self.assertEqual(
            pmUnitDict[ "SMB" ][ "outgoingSlotConfigs" ][ f"FAN_SLOT@{ i }" ][
               "presenceDetection" ][ "sysfsFileHandle" ][ "devicePath" ],
            f"/SMB_SLOT@0/[FAN{ i // 4 }_CPLD]"
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

   def testSingleAdapterConfig( self ):
      self.platform.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 0 ].addI2cAdapterConfigs(
         1, "SMB_I2C_MASTER", "0x8000"
      )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      testUnitConfig = pmUnitDict[ "SMB" ]
      config = testUnitConfig[ "pciDeviceConfigs" ][ 0 ][ "i2cAdapterConfigs" ]
      self.assertEqual( len( config ), 1 )

   def testMultipleAdapterConfigs( self ):
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

   def testSymlinkToDevicePath( self ):
      self.platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addSpiMasterConfigs( [
         SpiMasterConfig( "SCM_SPI_MASTER13", "spi_master", "0x80", "0x7900",
                           spiDeviceConfigs=[ 
                              Flash(
                                 pmUnitScopedName="SMB_SPI_MASTER13_DEVICE42",
                                 chipSelect=0,
                                 modalias="spidev",
                                 maxSpeedHz=25000000
                              )
                           ] 
                        )
      ] )
      self.platform.pmUnitConfigs[ 0 ].populateSymlinkToDevicePaths()
      symlinkDict = self.platform.parseSymbolicLinkToDevicePaths()
      self.assertEqual( len( symlinkDict ), 2 )
      self.assertTrue( 
         "/run/devmap/flashes/SMB_SPI_MASTER13_DEVICE42" in symlinkDict
      )
      self.assertEqual( 
         symlinkDict[ "/run/devmap/flashes/SMB_SPI_MASTER13_DEVICE42" ],
         "/[SMB_SPI_MASTER13_DEVICE42]"
      )

   def testDefaultSpiDeviceNoSymlink( self ):
      self.platform.pmUnitConfigs[ 0 ].pciDeviceConfigs[ 0 ].addSpiMasterConfigs( [
         SpiMasterConfig( "SCM_SPI_MASTER13", "spi_master", "0x80", "0x7900",
                           spiDeviceConfigs=[ 
                              SpiDeviceConfig(
                                 pmUnitScopedName="SMB_SPI_MASTER13_DEVICE42",
                                 chipSelect=0,
                                 modalias="spidev",
                                 maxSpeedHz=25000000
                              )
                           ] 
                        )
      ] )
      self.platform.pmUnitConfigs[ 0 ].populateSymlinkToDevicePaths()
      symlinkDict = self.platform.parseSymbolicLinkToDevicePaths()
      self.assertEqual( len( symlinkDict ), 1 )
      for symlink, devicePath in symlinkDict.items():
         self.assertFalse( "SMB_SPI_MASTER13_DEVICE42" in symlink )
         self.assertFalse( "SMB_SPI_MASTER13_DEVICE42" in devicePath )


class XcvrConfigTest( unittest.TestCase ):

   def setUp( self ):
      self.platform = PlatformConfig( "test_platform" )
      self.platform.addPmUnitConfigs( [
         PmUnitConfig( "SCM" ),
         PmUnitConfig( "SMB")
      ] )

   def testXcvrConfigViper( self ):
      self.platform.pmUnitConfigs[ 1 ].addPciDeviceConfigs( [
         PciDeviceConfig(
            pmUnitScopedName="SMB_FPGA",
            vendorId="0x3475",
            deviceId="0x0001",
            subSystemVendorId="0x3475",
            subSystemDeviceId="0x0003"
         )
      ] )
      self.platform.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 0 ].addXcvrCtrlConfigs( 
         numConfigs=32, 
         basePortNumber=1,
         portType="test",
         xcvrBaseOffset="0x0000", 
         led1BaseOffset="0x1000", 
         led2BaseOffset="0x1010"
      )
      self.platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs( [
         SlotConfig( slotName="SMB_SLOT@5" )
      ] )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      testUnitConfig = pmUnitDict[ "SMB" ]
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
      self.platform.pmUnitConfigs[ 1 ].populateSymlinkToDevicePaths()
      symlinkDict = self.platform.parseSymbolicLinkToDevicePaths()
      self.assertEqual( len( symlinkDict ), 33 )
      self.assertTrue( "/run/devmap/xcvrs/xcvr_32" in symlinkDict )
      self.assertEqual(
         symlinkDict[ "/run/devmap/xcvrs/xcvr_32" ],
         "/SMB_SLOT@5/[TEST_PORT32_XCVR]"
      )
      self.assertFalse( "/run/devmap/xcvrs/xcvr_33" in symlinkDict )

   def testXcvrConfigWhistler( self ):
      self.platform.pmUnitConfigs[ 1 ].addPciDeviceConfigs( [
         *enumeratePciDeviceConfigs( 2, "SMB_FPGA{}", "0x3475", "0x0001", "0x3475", 
                                     "0x0003")
      ] )
      self.platform.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 0 ].addXcvrCtrlConfigs( 
         numConfigs=16, basePortNumber=1, whistler=True
      )
      self.platform.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 1 ].addXcvrCtrlConfigs( 
         numConfigs=16, basePortNumber=5, whistler=True
      )
      pmUnitDict = self.platform.getPmUnitConfigsDict()
      testUnitConfig = pmUnitDict[ "SMB" ]
      for i in range( len( self.platform.pmUnitConfigs[ 1 ].pciDeviceConfigs ) ):
         self.assertEqual(
            len( testUnitConfig[ "pciDeviceConfigs" ][ i ][ "xcvrCtrlConfigs" ] ),
            16
         )
         self.assertEqual(
            len( testUnitConfig[ "pciDeviceConfigs" ][ i ][ "ledCtrlConfigs" ] ),
            32
         )


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
