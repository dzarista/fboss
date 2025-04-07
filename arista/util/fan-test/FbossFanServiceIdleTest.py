#!/usr/bin/env python3
# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
import csv
import datetime
import re
import sys
import time
import subprocess

tool_description = '''This script is intended to collect some thermal data on
a system for intention of testing the fan_service.

Example:
python3 FbossFanServiceIdleTest.py --idle 60 --chamber 25 -p Viper'''

def getAverage( data ):
   '''Return an average of a data formatted as a list'''
   if len( data ) == 0:
      return 0
   return sum( data ) / len( data )

def run_unix_command( command ):
   '''Run a Unix command and return its output.'''
   result = subprocess.run( command, shell=True, text=True, capture_output=True )
   return result.stdout

def readPath( path ):
   '''Returns a list for each line outputed by the path'''
   output = run_unix_command( f'cat {path}' )
   return output.split()

def readSensor( sensorPath, compute=1 ):
   '''Returns a list for each line outputed by the path'''
   return list( map(lambda x: int(x) / compute, readPath( sensorPath ) ) )

class FbossDut():
   def __init__( self, chamberTemp ):
      self.chamberTemp = chamberTemp

   def getFanSku( self ):
      raise NotImplementedError

   def getFanMfr( self, id ):
      raise NotImplementedError

   def getFanIds( self ):
      '''Returns a list of fan Ids where indexes map to fan slots'''
      fanIdsList = []
      fanIds = readSensor( '/run/devmap/sensors/FAN_CPLD/fan*_id' )
      for fan in fanIds:
         fanIdsList.append( int( fan ) )
      return fanIdsList

   def getOpticTemps( self ):
      '''Return a list of all optics temperatures'''
      raise NotImplementedError

   def getAsicTemps( self ):
      '''Return a list of all Asic temperatures'''
      raise NotImplementedError

   def getInletTemp( self ):
      '''Return the inlet temperature'''
      return self.chamberTemp

   def getOutletTemp( self ):
      '''Return the outlet temperature'''
      raise NotImplementedError
   
   def getCpuTemps( self ):
      '''Return the CPU temperature'''
      return NotImplementedError
   
   def getSsdTemp( self ):
      '''Return the SSD temperature'''
      return NotImplementedError

   def calculateCFM( self, cfmTable, pwm, fanVendor ):
      '''Estimate CFM based on a lookup table. Uses linear interpolation
      between data points'''
      if pwm < 0 or pwm > 100:
         raise ValueError("PWM must be between 0 and 100.")
   
      lowerBoundPwm = ( pwm // 10 ) * 10
      upperBoundPwm = min( ( ( pwm + 9 ) // 10 ) * 10, 100 )

      if upperBoundPwm == lowerBoundPwm:
         return cfmTable[ upperBoundPwm ][ fanVendor ]

      lowerBoundCfm = cfmTable[ lowerBoundPwm ][ fanVendor ]
      upperBoundCfm = cfmTable[ upperBoundPwm ][ fanVendor ]

      slope = ( upperBoundCfm - lowerBoundCfm ) / ( upperBoundPwm - lowerBoundPwm )
      return ( pwm - lowerBoundPwm ) * slope + lowerBoundCfm

   def getCFM( self, pwm ):
      '''Return the CFM value for a given PWM'''
      return NotImplementedError

   def getTotalSystemPower( self ):
      '''Return the total system power in Watts'''
      totalPower = 0.0
      powers = readSensor( '/run/devmap/sensors/PSU*_PMBUS/power1_input', 1000000 )
      for power in powers:
         totalPower += power

      return totalPower

   def getFanRpms( self ):
      '''Return a list of all system fan RPMs'''
      raise NotImplementedError
   
   def getPsuRpms( self ):
      '''Return a list of all system PSU fan RPMs'''
      raise NotImplementedError

   def getFanPwms( self ):
      '''Return a list of all system fan PWM (%)'''
      raise NotImplementedError

   def getHottestOpticTemp( self ):
      return max( self.getOpticTemps().values() )

   def getHottestAsicTemp( self ):
      return max( self.getAsicTemps() )

   def getHottestCpuTemp( self ):
      return max( self.getCpuTemps() )

   def getAvgFanRpm( self ):
      '''Return average system fan RPMs'''
      return getAverage( self.getFanRpms() )
   
   def getAvgPsuFanRpm( self ):
      '''Return average system PSU fan RPMs'''
      return getAverage( self.getPsuRpms() )

   def getAvgFanPwm( self ):
      '''Return average system fan Pwms'''
      return getAverage( self.getFanPwms() )

   def collectData( self ):
      '''Return an object with all RAW data collected'''
      hottestOptic = self.getHottestOpticTemp()
      opticTemps = self.getOpticTemps()
      fanPwms = self.getFanPwms()
      fanRpms = self.getFanRpms()
      psuRpms = self.getPsuRpms()
      avgFanPwm = self.getAvgFanPwm()
      cfm = self.getCFM( avgFanPwm )
      power = self.getTotalSystemPower()
      inletTemp = self.getInletTemp()
      outletTemp = self.getOutletTemp()

      rawData =  {
            'AvgRpm': round( self.getAvgFanRpm(), 4 ),
            'HottestOptic': round( hottestOptic, 4 ),
            'HottestAsic': round( self.getHottestAsicTemp(), 4),
            'HottestCpuTemp': round( self.getHottestCpuTemp(), 4),
            'AvgFanPwm': round( avgFanPwm, 4 ),
            'Airflow(CFM)': round( cfm, 4 ),
            'SystemPower': round( power, 4 ),
            'Inlet': round( inletTemp, 4 ),
            'Outlet': round( outletTemp, 4 ),
            'SsdTemp': round( self.getSsdTemp(), 4 ),
            'CFM/W': round(cfm / power, 4),
            'AvgPsusRpm': round( self.getAvgPsuFanRpm(), 4 ),
      }

      for opticName, opticTemp in opticTemps.items():
         rawData[opticName] = opticTemp

      for fanIdx, fanPwm in enumerate(fanPwms):
         rawData[f'fan{fanIdx}_pwm'] = fanPwm

      for fanIdx, fanRpm in enumerate(fanRpms):
         rawData[f'fan{fanIdx}_rpm'] = fanRpm

      for psuIdx, psuRpm in enumerate(psuRpms):
         rawData[f'psu{psuIdx}'] = psuRpm
      
      return rawData

class MaunaKea( FbossDut ):
   '''Class that implements methods specifically for Mauna Kea platforms'''
   def getFanMfr( self, id ):
      idBits = int( id ) & 0b111 # filter to fan id according to Mauna key table
      if idBits == 0:
         return 'SANYO DENKI'
      elif idBits == 1:
         return 'DELTA'
      else:
         raise ValueError( 'Fan mfr not detected' )

class Viper( MaunaKea ):
   '''Class that defines some Viper helpers to collect
   FSCD qualification data'''

   CFM_DATA = {
      100: { 'SANYO DENKI': 392, 'DELTA': 417 },
      90: { 'SANYO DENKI': 367, 'DELTA': 393 },
      80: { 'SANYO DENKI': 337, 'DELTA': 356 },
      70: { 'SANYO DENKI': 300, 'DELTA': 319 },
      60: { 'SANYO DENKI': 267, 'DELTA': 280 },
      50: { 'SANYO DENKI': 231, 'DELTA': 241 },
      40: { 'SANYO DENKI': 193, 'DELTA': 204 },
      30: { 'SANYO DENKI': 159, 'DELTA': 163 },
      20: { 'SANYO DENKI': 127, 'DELTA': 127 },
      10: { 'SANYO DENKI': 84, 'DELTA': 94 },
      0: { 'SANYO DENKI': 62, 'DELTA': 47 }
   }

   def getFanSku( self ):
      return 'FAN-7021H-RED'

   def getOpticTemps( self ):
      opticsTemps = {}
      output = run_unix_command( 'wedge_qsfp_util | grep Temperature' )
      lines = output.split('\n')
      index = 1
      for line in lines:
         if "Temperature:" in line:
            temp = re.search(r'[-+]?\d*\.\d+|\d+', output.split('\n')[0]).group()
            opticsTemps[f"Port{index}"] = float( temp )
            index += 1
      return opticsTemps

   def getAsicTemps( self ):
      asicTemps = []
      temps = readSensor( '/run/devmap/sensors/SMB_MAX6581/temp*_input', 1000 )
      for sensor in temps:
         asicTemps.append( sensor )
      return asicTemps

   def getOutletTemp( self ):
      '''Return the outlet temperature'''
      outlet = readSensor( '/run/devmap/sensors/SMB_MAX6581/temp*_input', 1000 )
      return outlet[0]

   def getCpuTemps( self ):
      '''Return the CPU temperature'''
      cpuTemps = []
      temps = readSensor( '/run/devmap/sensors/CPU_CORE_TEMP/temp*_input', 1000 )
      for sensor in temps:
         cpuTemps.append( sensor )
      return cpuTemps
   
   def getSsdTemp( self ):
      '''Return the SSD temperature'''
      path = "/sys/bus/pci/drivers/nvme/0000:05:00.0/nvme/nvme0/hwmon0/temp1_input"
      return readSensor( path, 1000 )[0]

   def getFanRpms( self ):
      rpmList = []
      temps = readSensor( '/run/devmap/sensors/FAN_CPLD/fan*_input' )
      for sensor in temps:
         rpmList.append( sensor )
      return rpmList

   def getPsuRpms( self ):
      '''Return a list of all system PSU fan RPMs'''
      rpmList = []
      
      # each psu directory includes fan3 and 4 which read -1 for rpms.
      # listing each fan individually to avoid any confusion
      psu1_fan1 = readSensor( '/run/devmap/sensors/PSU1_PMBUS/fan1_input' )[0]
      psu1_fan2 = readSensor( '/run/devmap/sensors/PSU1_PMBUS/fan2_input' )[0]
      psu2_fan1 = readSensor( '/run/devmap/sensors/PSU2_PMBUS/fan1_input' )[0]
      psu2_fan2 = readSensor( '/run/devmap/sensors/PSU2_PMBUS/fan2_input' )[0]

      for sensor in [psu1_fan1, psu1_fan2, psu2_fan1, psu2_fan2]:
         rpmList.append( sensor )
      return rpmList

   def getFanPwms( self ):
      '''Return Fan PWMs as a list, reported as a percentage'''
      pwms = []
      temps = readSensor( '/run/devmap/sensors/FAN_CPLD/pwm*' )
      for sensor in temps:
         pwms.append( round( sensor/255 * 100, 2 ) )
      return pwms

   def getCFM( self, pwm ):
      '''Return the CFM value for a given PWM'''
      fanId = self.getFanIds()[ 0 ] # Using cfm data of fan in the first slot
      fanVendor = self.getFanMfr( fanId )
      return self.calculateCFM( self.CFM_DATA, pwm, fanVendor )

def parseArgs( argv ):
   parser = argparse.ArgumentParser(
         prog='FbossFanServiceIdleTest', description=tool_description )
   parser.add_argument( '--idle', default=3600, type=int,
                       help='Idle duration in minutes' )
   parser.add_argument( '--chamber', required=True, type=int,
                       help='chamber temperature' )
   parser.add_argument( '-p', '--product', required=True,
                       help='Dut type e.g. Viper' )
   return parser.parse_args( argv )

def main( argv ):
   args = parseArgs( argv )

   if args.product and args.product.lower() == 'viper':
      obj = Viper( args.chamber )
   else:
      assert( 'Product Class not defined for {}'.format( args.product ) )

   # Get fan info
   fanIds = obj.getFanIds()
   fanSku = obj.getFanSku()

   current_time = datetime.datetime.now()
   timestamp = current_time.strftime( '%Y%m%d_%H%M%S' )
   filename = f'{args.product}_idle_{timestamp}'

   with open(f'{filename}_summary.txt', "w") as file:
      file.write( '#### Fans Info ####\n' )
      for fanIdx, fanId in enumerate( fanIds ):
         binaryId = format( fanId, '08b' )
         fanLog = f'Fan {fanIdx + 1} ID: {binaryId}. \
            Fan SKU: {fanSku} ({obj.getFanMfr(fanId)})\n'
         file.write( fanLog )

      file.write( '\n#### wedge_qsfp_util ####\n' )
      output = run_unix_command( 'wedge_qsfp_util' )
      file.write( output )

   with open( f'{filename}.csv', 'w', newline='' ) as csvfile:
      print( f'Sampling data for {args.idle} minutes...' )
      fieldnames = [ 'Timestamp' ] + list( obj.collectData().keys() )
      csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
      csvwriter.writeheader()

      idleTimeInSeconds = args.idle * 60
      pollStart = time.time()
      
      remainingTime = idleTimeInSeconds
      while remainingTime > 0:
         print( f"remaining time: {remainingTime}" )
         
         dataRaw = obj.collectData()
         timestamp = datetime.datetime.now().strftime( '%Y-%m-%d_%H:%M:%S' )
         row = {'Timestamp': timestamp}
         row.update(dataRaw)
         csvwriter.writerow(row)
         remainingTime = round( idleTimeInSeconds - ( time.time() - pollStart ) )

if __name__ == '__main__':
   sys.exit( main( sys.argv[ 1 : ] ) )
