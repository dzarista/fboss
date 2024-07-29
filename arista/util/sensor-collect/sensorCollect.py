#!/usr/bin/env python3
# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
import csv
import datetime
import json
import subprocess
import sys
import time

tool_description = '''This script is intended to collect sensor data and verify
the values are within the thresholds specified in sensor_configs

For Example:
python3 sensorCollect.py --interval 10 --time 36000 --sensors \
SCM_VRM1_VIN SCM_VRM1_VOUT_VCCIN SCM_VRM1_VOUT_1V8_CPU SCM_VRM1_TEMP1 \
SCM_VRM1_TEMP2 SCM_VRM2_VIN SCM_VRM2_VOUT_1V2_VDDQ SCM_VRM2_VOUT_VNN_NAC \
SCM_VRM2_VOUT_1V0_CPU SCM_VRM2_TEMP1 SCM_VRM2_TEMP2 SCM_VRM3_VIN \
SCM_VRM3_VOUT_1V05_CPU SCM_VRM3_VOUT_VNN_PCH SCM_VRM3_TEMP1 SCM_VRM3_TEMP2
'''

SENSOR_SERVICE_JSON = '/opt/fboss/share/platform_configs/sensor_service.json'

class SensorCollect:
   def __init__( self, sensors ):
      self.sensorNames = sensors
      self.sensors = {}
      self.getSensorsConfig()

   def runCmd( self, cmd ):
      result = subprocess.run( cmd, shell=True, text=True, capture_output=True )
      return result.stdout

   def readMultiplePaths( self, paths ):
      cmd = "cat " + " ".join( paths )
      output = self.runCmd( cmd )
      return output.splitlines()

   def getSensorsConfig( self ):
      '''Returns a map of sensors extracted from sensorConfig'''
      print( "Getting sensor configs..." )
      rawSensorSrvJson = self.runCmd( f"cat {SENSOR_SERVICE_JSON}" )
      sensorConfig = json.loads( rawSensorSrvJson )[ "sensorMapList" ]

      filtered_data = {}
      for group_data in sensorConfig.values():
         if isinstance(group_data, dict):
            for sensor in self.sensorNames:
               if sensor in group_data:
                  filtered_data[sensor] = group_data[sensor]
      self.sensors = filtered_data

   def getSensors( self, logFile ):
      '''Reads sensors and verifies that no value exceeds alarm'''
      data = {}
      paths = []

      for details in self.sensors.values():
         paths.append( details[ 'path' ] )
      
      readings = self.readMultiplePaths( paths )
      for sensor, details in self.sensors.items():
         pathIdx = paths.index( details[ 'path' ] )
         rawSensorVal = int( readings[ pathIdx ]  )
         sensorVal = rawSensorVal / float( details[ 'compute' ].split( "@/" )[ 1 ] )         
         data[sensor] = sensorVal

         thresholds = details['thresholds']
         upperCriticalVal = thresholds.get( 'upperCriticalVal' )
         maxAlarmVal = thresholds.get( 'maxAlarmVal' )
         lowerCriticalVal = thresholds.get( 'lowerCriticalVal' )
         timestamp = datetime.datetime.now()
         timestampStr = timestamp.strftime( '%Y-%m-%d_%H:%M:%S:' )\
            + f"{timestamp.microsecond // 1000:03d}"
         with open(logFile, 'a') as file:
            if upperCriticalVal and sensorVal > upperCriticalVal:
               file.write( f"{timestampStr}\t{sensor} exceeded upperCriticalVal of "
                           f"{upperCriticalVal} with a value {sensorVal}\n" )
            elif maxAlarmVal and sensorVal > maxAlarmVal:
               file.write( f"{timestampStr}\t{sensor} exceeded maxAlarmVal of "
                           f"{maxAlarmVal} with a value {sensorVal}\n" )
            elif lowerCriticalVal and sensorVal < lowerCriticalVal:
               file.write( f"{timestampStr}\t{sensor} is below lowerCriticalVal of "
                           f"{lowerCriticalVal} with a value {sensorVal}\n" )
            elif sensorVal <= 0:
               file.write( f"{timestampStr}\t{sensor} <=0 "
                           f"with a value of {sensorVal}\n" )
      return data

def parseArgs( argv ):
   parser = argparse.ArgumentParser(
         prog='sensorCollect', description=tool_description )
   parser.add_argument( '-i','--interval', type=int, default=10,
            required=True, help='Interval between data collected in milliseconds' )
   parser.add_argument( '-t','--time', type=int, default=3600,
                       required=True, help='Duration of the test in seconds' )
   parser.add_argument( '-s', '--sensors', type=str, nargs='*', required=True,
                       help='List of sensors')
   return parser.parse_args( argv )

def main( argv ):
   args = parseArgs( argv )

   obj = SensorCollect( args.sensors )

   current_time = datetime.datetime.now()
   timestamp = current_time.strftime('%Y%m%d_%H%M%S')
   interval = args.interval / 1000
   iterations = int(args.time / interval)
   filename = f'sensors_{timestamp}'

   with open( f'{filename}.csv', 'w', newline='' ) as csvfile:
      fieldnames = [ 'Timestamp' ] + list(args.sensors)
      csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
      csvwriter.writeheader()

      print( "starting sensor test..." )
      for _ in range( iterations ):
         start_time = time.time()
         dataRaw = obj.getSensors( f"{filename}.log" )
         timestamp = datetime.datetime.now()
         timestampStr = timestamp.strftime( '%Y-%m-%d_%H:%M:%S:' )\
            + f"{timestamp.microsecond // 1000:03d}"
         row = { 'Timestamp': timestampStr }
         row.update( dataRaw )
         csvwriter.writerow( row )

         end_time = time.time()
         time_wasted = end_time - start_time
         sleep_time = interval - time_wasted
         if sleep_time > 0:
            time.sleep(interval)

if __name__ == '__main__':
   sys.exit( main( sys.argv[ 1 : ] ) )
