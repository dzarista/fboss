# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import unittest
from collections import OrderedDict
from .BaseConfigs import (
   enumerateFANSlotConfigs,
   FANCpld,
   PciDeviceConfig,
   PlatformConfig,
   PmUnitConfig,
   SCMUnit,
   SlotConfig,
)

class LedManagerTest( unittest.TestCase ):
   def setUp( self ):
      self.platform = PlatformConfig( "test_led_platform" )
      self.scm_unit = SCMUnit()
      self.smb_unit = PmUnitConfig( pmUnitName="SMB" )
      self.scm_unit.addOutgoingSlotConfigs( [ SlotConfig( slotName="SMB_SLOT@0" ) ] )
      self.platform.addPmUnitConfigs( [ self.scm_unit, self.smb_unit ] )

   def test_system_and_fru_type_configs( self ):
      generated_data = json.loads( self.platform.ledJson(), object_pairs_hook=OrderedDict )

      self.assertIn( "systemLedConfig", generated_data )
      expected_sys = {
         "presentLedColor": 1,
         "presentLedSysfsPath": "/sys/class/leds/sys_led:green:status/brightness",
         "absentLedColor": 2,
         "absentLedSysfsPath": "/sys/class/leds/sys_led:red:status/brightness"
      }
      self.assertDictEqual( generated_data[ "systemLedConfig" ], expected_sys )

      self.assertIn( "fruTypeLedConfigs", generated_data )
      expected_fan = {
         "presentLedColor": 1,
         "presentLedSysfsPath": "/sys/class/leds/fan_led:green:status/brightness",
         "absentLedColor": 2,
         "absentLedSysfsPath": "/sys/class/leds/fan_led:red:status/brightness"
      }
      self.assertDictEqual( generated_data[ "fruTypeLedConfigs" ][ "FAN" ], expected_fan )

   def test_empty_fru_configs( self ):
      generated_data = json.loads( self.platform.ledJson(), object_pairs_hook=OrderedDict )
      self.assertIn( "fruConfigs", generated_data )
      self.assertEqual( generated_data[ "fruConfigs" ], [] )

   def test_full_fru_configs_generation( self ):
      fan_cplds = [ FANCpld( "0x60", "test_cpld", f"FAN_CPLD{i}" ) for i in range( 3 ) ]
      self.smb_unit.addI2cDeviceConfigs( fan_cplds )

      psu_fpga = PciDeviceConfig( "SMB_FPGA", "0x1234", "0x5678", "0x1234", "0x5678" )
      self.smb_unit.addPciDeviceConfigs( [ psu_fpga ] )

      fan_slots = enumerateFANSlotConfigs( 12, "/SMB_SLOT@0/[FAN_CPLD{}]", fansPerCpld=4 )
      psu_slots = [
         SlotConfig(
            slotName=f"PSU_SLOT@{i}",
            presenceFileName=f"psu{i+1}_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]"
         ) for i in range( 4 )
      ]
      self.smb_unit.addOutgoingSlotConfigs( fan_slots + psu_slots )

      for pm_cfg in self.platform.pmUnitConfigs:
         pm_cfg.populateSymlinkToDevicePaths()

      generated_data = json.loads( self.platform.ledJson(), object_pairs_hook=OrderedDict )
      
      expected_fru_configs = [
         OrderedDict( [
            ( "fruName", f"FAN{i+1}" ),
            ( "fruType", "FAN" ),
            ( "presenceDetection", {
               "sysfsFileHandle": {
                  "presenceFilePath": f"/run/devmap/sensors/FAN_CPLD{i//4}/fan{i%4+1}_present",
                  "desiredValue": 1
               }
            } )
         ] ) for i in range( 12 )
      ] + [
         OrderedDict( [
            ( "fruName", f"PSU{i+1}" ),
            ( "fruType", "PSU" ),
            ( "presenceDetection", {
               "sysfsFileHandle": {
                  "presenceFilePath": f"/run/devmap/fpgas/TEST_LED_PLATFORM_SMB_FPGA/psu{i+1}_present",
                  "desiredValue": 1
               }
            } )
         ] ) for i in range( 4 )
      ]

      self.assertListEqual( generated_data[ "fruConfigs" ], expected_fru_configs )

if __name__ == '__main__':
   unittest.main()