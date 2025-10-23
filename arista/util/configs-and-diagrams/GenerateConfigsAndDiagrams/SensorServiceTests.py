# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import unittest
from .BaseConfigs import (
   EmbeddedSensorConfig,
   FairywrenSensor,
   FANCpld,
   PlatformConfig,
   PmUnitConfig,
   Sensor,
   SensorConfig,
   SensorType,
   SlotConfig,
   Thresholds
)

class SensorServiceTest( unittest.TestCase ):
   def setUp( self ):
      self.platform = PlatformConfig( "test_platform" )
      self.platform.addPmUnitConfigs( [
         PmUnitConfig( "SCM" ),
         PmUnitConfig( "SMB" )
      ] )
      self.platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs( [
         SlotConfig( "SMB_SLOT@0" )
      ] )
      self.platform.pmUnitConfigs[ 0 ].addI2cDeviceConfigs( [
         FairywrenSensor( "0x40", "pmbus", "SCM_MPS_PMBUS" )
      ] )
      self.platform.pmUnitConfigs[ 1 ].addI2cDeviceConfigs( [
         Sensor( "0x54", "bp4a_isl68226", "SMB_ISL68226_J3" )
      ] )

   def findSensor( self, sensors, name ):
      return next(
         ( sensor for sensor in sensors if sensor.get( 'name' ) == name ), None
      )

   def testInvalidConfig( self ):
      with self.assertRaises( TypeError ):
         self.platform.pmUnitConfigs[ 0 ].i2cDeviceConfigs[ 0 ].addSensorConfigs(
            SensorConfig( "ECB_VIN", "in1_input", 0 )
         )
      with self.assertRaises( AssertionError ):
         self.platform.pmUnitConfigs[ 0 ].i2cDeviceConfigs[ 0 ].addSensorConfigs(
            SensorConfig( "ECB_VIN", None, SensorType.POWER )
         )

   def testNoComputeAndThresholds( self ):
      self.platform.pmUnitConfigs[ 0 ].i2cDeviceConfigs[ 0 ].addSensorConfigs( [
            SensorConfig( "ECB_VIN", "in1_input", SensorType.VOLTAGE )
         ] )
      jsonDump = self.platform.sensorServiceJson()
      sensorDict = json.loads( jsonDump )
      sensors = sensorDict[ "pmUnitSensorsList" ][ 0 ][ "sensors" ]
      sensorConfig = self.findSensor( sensors, "SCM_ECB_VIN" )
      self.assertIsNotNone( sensorConfig )
      self.assertFalse( "thresholds" in sensorConfig )
      self.assertFalse( "compute" in sensorConfig )

   def testThresholds( self ):
      self.platform.pmUnitConfigs[ 0 ].i2cDeviceConfigs[ 0 ].addSensorConfigs( [
            SensorConfig( "ECB_VIN", "in1_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=20.0, maxAlarmVal=30.0
                          ) )
         ] )
      jsonDump = self.platform.sensorServiceJson()
      sensorDict = json.loads( jsonDump )
      sensors = sensorDict[ "pmUnitSensorsList" ][ 0 ][ "sensors" ]
      sensorConfig = self.findSensor( sensors, "ECB_VIN" )
      self.assertIsNotNone( sensorConfig )
      self.assertTrue( "thresholds" in sensorConfig )
      self.assertTrue( "compute" in sensorConfig )
      self.assertEqual( sensorConfig[ "compute" ], "@/1000.0" )
      self.assertEqual( sensorConfig[ "type" ], 1 )
      self.assertTrue( "upperCriticalVal" in sensorConfig[ "thresholds" ] )
      self.assertFalse( "lowerCriticalVal" in sensorConfig[ "thresholds" ] )
      self.assertTrue( "maxAlarmVal" in sensorConfig[ "thresholds" ] )
      self.assertFalse( "minAlarmVal" in sensorConfig[ "thresholds" ] )
      self.assertEqual( sensorConfig[ "thresholds" ][ "upperCriticalVal" ], 20.0 )
      self.assertEqual( sensorConfig[ "thresholds" ][ "maxAlarmVal" ], 30.0 )

   def testEmbeddedSensor( self ):
      self.platform.pmUnitConfigs[ 0 ].addEmbeddedSensorConfigs( [
         EmbeddedSensorConfig(
            pmUnitScopedName="CPU_CORE_TEMP",
            sysfsPath="/sys/bus/platform/devices/coretemp.0"
         )
      ] )
      self.platform.pmUnitConfigs[ 0 ].embeddedSensorConfigs[ 0 ].addSensorConfigs( [
         SensorConfig( "CPU_PACKAGE_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "CPU_CORE_TEMP0", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) )
         ] )
      jsonDump = self.platform.sensorServiceJson()
      sensorDict = json.loads( jsonDump )
      sensors = sensorDict[ "pmUnitSensorsList" ][ 0 ][ "sensors" ]
      sensorConfig = self.findSensor( sensors, "CPU_PACKAGE_TEMP" )
      self.assertIsNotNone( sensorConfig )
      self.assertTrue( "sysfsPath" in sensorConfig )
      self.assertEqual(
         sensorConfig[ "sysfsPath" ],
         "/run/devmap/sensors/CPU_CORE_TEMP/temp1_input"
      )
      sensorConfig = self.findSensor( sensors, "SCM_CPU_CORE_TEMP0" )
      self.assertIsNotNone( sensorConfig )
      self.assertTrue( "sysfsPath" in sensorConfig )
      self.assertEqual(
         sensorConfig[ "sysfsPath" ],
         "/run/devmap/sensors/CPU_CORE_TEMP/temp2_input"
      )

   def testMultiplePhysicalSlots( self ):
      self.platform.pmUnitConfigs[ 0 ].addOutgoingSlotConfigs( [
         SlotConfig( "SMB_SLOT@1" )
      ] )
      self.platform.pmUnitConfigs[ 1 ].i2cDeviceConfigs[ 0 ].addSensorConfigs( [
         SensorConfig( "VRM2_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, minAlarmVal=9.6
                       ) )
      ] )
      jsonDump = self.platform.sensorServiceJson()
      sensorDict = json.loads( jsonDump )
      self.assertEqual( len( sensorDict[ "pmUnitSensorsList" ] ), 2 )
      smb1Sensors = sensorDict[ "pmUnitSensorsList" ][ 0 ][ "sensors" ]
      smb2Sensors = sensorDict[ "pmUnitSensorsList" ][ 1 ][ "sensors" ]
      self.assertIsNotNone( self.findSensor( smb1Sensors, "SMB1_VRM2_VIN" ) )
      self.assertIsNotNone( self.findSensor( smb2Sensors, "SMB2_VRM2_VIN" ) )

   def testAddFANRpms( self ):
      self.platform.pmUnitConfigs[ 1 ].addI2cDeviceConfigs( [
         FANCpld( "0x60", "oasis_cpld0", "FAN0_CPLD", incomingBusIndex=3 )
      ] )
      self.platform.pmUnitConfigs[ 1 ].i2cDeviceConfigs[ 1 ].addFANRpms(
         8, upperCriticalVal=14900.0, lowerCriticalVal=1100.0
      )
      jsonDump = self.platform.sensorServiceJson()
      sensorDict = json.loads( jsonDump )
      self.assertEqual( len( sensorDict[ "pmUnitSensorsList" ] ), 1 )
      fanSensors = sensorDict[ "pmUnitSensorsList" ][ 0 ][ "sensors" ]
      self.assertEqual( len( fanSensors ), 8 )
      for i in range( 8 ):
         sensorConfig = self.findSensor( fanSensors, f"FAN{ i+1 }_RPM" )
         self.assertIsNotNone( sensorConfig )
         self.assertEqual(
            sensorConfig[ "sysfsPath" ],
            f"/run/devmap/sensors/FAN_CPLD0/fan{ i+1 }_input"
         )


if __name__ == '__main__':
   unittest.main()
