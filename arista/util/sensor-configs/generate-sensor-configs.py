# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

'''
Script to generate an FBOSS OSS sensor_service.json config file from a
Google Spreadsheet. This script must be run from an Artools-based environment.
'''

import json
import sys

from ArGoogleApps import SpreadsheetLibV4 as SsLib
from collections import OrderedDict


class Thresholds:
   '''Every sensor may define the following four thresholds:

   upperCriticalVal: upper threshold for critical (strong) alarm
   lowerCriticalVal: lower threshold for critical (strong) alarm
   maxAlarmVal: upper threshold for conventional alarm
   minAlarmVal: lower threshold for conventional alarm
   '''

   def __init__( self, upperCriticalVal, lowerCriticalVal,
                 maxAlarmVal, minAlarmVal ):
      self.upperCriticalVal = upperCriticalVal
      self.lowerCriticalVal = lowerCriticalVal
      self.maxAlarmVal = maxAlarmVal
      self.minAlarmVal = minAlarmVal

   def toDict( self ):
      thresholdsDict = OrderedDict()
      if self.upperCriticalVal is not None:
         thresholdsDict[ 'upperCriticalVal' ] = float( self.upperCriticalVal )
      if self.lowerCriticalVal is not None:
         thresholdsDict[ 'lowerCriticalVal' ] = float( self.lowerCriticalVal )
      if self.maxAlarmVal is not None:
         thresholdsDict[ 'maxAlarmVal' ] = float( self.maxAlarmVal )
      if self.minAlarmVal is not None:
         thresholdsDict[ 'minAlarmVal' ] = float( self.minAlarmVal )
      return thresholdsDict


class Sensor:
   '''A distinct sensor in the FRU, composed of:

   name: sensor name
   path: sysfs path that sensor_services uses to read value
   thresholds: collection of sensor thresholds
   compute: scale factor
   sensorType: sensor type, one of:
         0 = power in watts
         1 = voltage in volts
         2 = current in amps
         3 = temperature in C
         4 = fan speed in RPM
   '''

   def __init__( self, name, path, thresholds, compute, sensorType ):
      assert name
      assert path
      assert sensorType in range( 0, 5 )
      self.name = name
      self.path = path
      self.thresholds = thresholds
      self.compute = compute
      self.sensorType = sensorType

   def toDict( self ):
      sensorDict = OrderedDict()
      sensorDict[ 'path' ] = self.path
      if self.thresholds:
         sensorDict[ 'thresholds' ] = self.thresholds.toDict()
      if self.compute:
         sensorDict[ 'compute' ] = self.compute
      sensorDict[ 'type' ] = int( self.sensorType )
      return sensorDict


class Fru:
   '''In the config, sensors are listed by the Field Replacable Unit (FRU) on which
   they physically reside.
   '''

   def __init__( self, name ):
      self.name = name
      self.sensors = OrderedDict()

   def addSensor( self, sensor ):
      assert sensor.name not in self.sensors
      self.sensors[ sensor.name ] = sensor

   def toDict( self ):
      fruDict = OrderedDict()
      for sensorName, sensor in self.sensors.items():
         fruDict[ sensorName ] = sensor.toDict()
      return fruDict


class SensorServiceConfig:
   '''Platform config for sensor_service represented in a Google sheet.
   For format example, see go/dsf-snr-fboss.
   '''

   def __init__( self, spreadsheetId, sheetName ):
      service = SsLib.Service()
      ss = service.getSpreadsheet( spreadsheetId, sheetType=SsLib.SheetType.keyless )
      sheet = ss.sheet( sheetName )

      def getRowSanitized( row, key ):
         # Ignore certain values.
         val = row.get( key )
         if val in ( 'N/A', 'TBA', 'TBD' ):
            return None
         return val

      self.frus = OrderedDict()
      for row in sheet.getRows():
         fruName = row.get( 'FRU/Module' )
         fru = self.frus.get( fruName )
         if not fru:
            fru = Fru( fruName )
            self.frus[ fruName ] = fru
         
         sensorName = getRowSanitized( row, 'Sensor Name' )
         sensorType = int( getRowSanitized( row, 'Sensor Type' ) )
         sensorPath = getRowSanitized( row, 'Sensor Access Method' )
         sensorCompute = getRowSanitized( row, 'SW Scaling Required' )

         thresholds = None
         upperCriticalVal = getRowSanitized( row, 'upperCriticalVal' )
         lowerCriticalVal = getRowSanitized( row, 'lowerCriticalVal' )
         maxAlarmVal = getRowSanitized( row, 'maxAlarmVal' )
         minAlarmVal = getRowSanitized( row, 'minAlarmVal' )
         if any( val is not None for val in
                 [ upperCriticalVal, lowerCriticalVal, maxAlarmVal, minAlarmVal ] ):
            thresholds = Thresholds(
                  upperCriticalVal,
                  lowerCriticalVal,
                  maxAlarmVal,
                  minAlarmVal
            )

         fru.addSensor(
            Sensor( sensorName, sensorPath, thresholds, sensorCompute, sensorType )
         )

   def asJson( self ):
      fruDict = OrderedDict()
      for fruName, fru in self.frus.items():
         fruDict[ fruName ] = fru.toDict()
      sensorConfigDict = { 'sensorMapList': fruDict }
      return json.dumps( sensorConfigDict, indent=2 )


def main():
   if len( sys.argv ) < 3:
      print( f'Usage: {sys.argv[ 0 ]} <spreadsheet id> <sheet name>' )
      sys.exit( 1 )

   spreadsheetId = sys.argv[ 1 ]
   sheetName = sys.argv[ 2 ]

   snrConfig = SensorServiceConfig( spreadsheetId, sheetName )
   print( snrConfig.asJson() )

if __name__ == '__main__':
   main()
