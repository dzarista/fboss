#!/usr/bin/env python3
# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import ArosTest
from ArosTest.DutMgmt import defaultEdut

import argparse
import CliTest
import csv
import datetime
import pandas as pd
import re
import sys
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

DEFAULT_RPMS = [ 100, 90, 80, 70, 60, 50, 40, 30, 28, 26, 24, 22, 20 ]
SAMPLE_COUNT = 10

tool_description = '''This script is intended to collect some thermal data on
a system for intention of generating some Thermal fan control tables
for FBOSS/OpenBMC.

This script will collect various datapoints according to the options passed and
can generate a csv, which can be maually inspected and processed to generate
a table for certain temperature sensors to PWM.

For Example:
python3 CollectFanSweepData.py -d vpr114 --soak-time 60 --rpms 100 90 80 70 60 50 40
30 20'''

def getAverage( data ):
   '''Return an average of a data formatted as a list'''
   if len( data ) == 0:
      return 0
   return sum( data ) / len( data )

def avgSample(dataFunc, sampleCount):
   '''Calculates the average of the values returned by a given function'''
   total = 0
   for _ in range(sampleCount):
      value = dataFunc()
      total += float(value)
   return total / sampleCount

class FbossFanTestEdut():
   def __init__( self, edut ):
      self.edut = edut

   def getFanSku( self ):
      raise NotImplementedError

   def getFanMfr( self, id ):
      raise NotImplementedError

   def getFanIds( self ):
      '''Returns a list of fan Ids where indexes map to fan slots'''
      raise NotImplementedError

   def getOpticTemps( self ):
      '''Return a list of all optics temperatures'''
      raise NotImplementedError

   def getAsicTemps( self ):
      '''Return a list of all Asic temperatures'''
      raise NotImplementedError

   def getInletTemp( self ):
      '''Return the inlet temperature'''
      shTemp = self.edut.showCmdIs( 'show sys env cool', dataFormat='json' )
      return shTemp[ 'ambientTemperature' ]

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
      shPower = self.edut.showCmdIs( 'show sys env pow detail',
                                     dataFormat='json' )
      for slot in shPower[ 'powerSupplies' ]:
         totalPower += shPower[ 'powerSupplies' ][
                                slot ][ 'inputPower' ]
      return totalPower

   def StartEosFanControl( self ):
      '''Start down EOS fan control algorithm'''
      self.edut.aconsPathCmdIs(
            r"/ar/Sysdb/environment/thermostat/config",
            "_.mode='automatic'" )

   def getFanRpms( self ):
      '''Return a list of all system fan RPMs'''
      raise NotImplementedError
   
   def getPsuRpms( self ):
      '''Return a list of all system PSU fan RPMs'''
      raise NotImplementedError

   def setFanSpeed( self, pct ):
      '''Set fan speed as a % of max fan RPM'''
      cli = self.edut.consoleCli()
      cli.gotoMode( CliTest.enableMode )
      with CliTest.MaybeRunInConfigSession( cli ):
         cli.runCmd( f"environment fan-speed override {pct}" )

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
   
   def getSystemInfo( self ):
      return self.edut.showCmdIs( 'show inv' )

   def getSystemIntfs( self ):
      return self.edut.showCmdIs( 'show int st' )
   
   def getSystemIntfsConnectedCount( self ):
      return int ( self.edut.showCmdIs( 'sh int st | grep connected | wc -l' )[ 0 ] )

   def getSystemIntfsCountRates( self ):
      return self.edut.showCmdIs( 'show int count rates' )
   
   def getAvgTrafficRate( self ):
      '''Get the average traffic rate (percentage)'''
      rates = []
      shRates = self.edut.showCmdIs( 'show int count rates', dataFormat='json' )
      interfaces = shRates[ 'interfaces' ]

      for intf in interfaces:
         if "Ethernet" in intf:
            rates.append( interfaces[ intf ][ 'outPktsRate' ] )

      return int( getAverage( rates ) )

   def getSystemEnvTemp( self ):
      return self.edut.showCmdIs( 'show sys env temp' )

   def getSystemIntfsTemp( self ):
      return self.edut.showCmdIs( 'show sys env temp transceiver' )

   def overridePidAlgo( self ):
      '''Override fan speed to EOS minimum (30) to allow for fan speed to be
      set without interference'''
      cli = self.edut.consoleCli()
      cli.gotoMode( CliTest.enableMode )
      with CliTest.MaybeRunInConfigSession( cli ):
         cli.runCmd( "environment fan-speed override 30" )

      # Set the poll interval to 1 day to avoid the fan speed being overriden by 
      # the algo. This is necessary for zone testing as this test directly modifies
      # the speed of each test and the pollInterval being large will avoid having the 
      # fan speeds being overwritten throughout the duration of the test
      self.edut.aconsPathCmdIs(
         r"/ar/Sysdb/environment/thermostat/config",
         "_.pollInterval=86400" )

   def enablePidAlgo( self ):
      cli = self.edut.consoleCli()
      cli.gotoMode( CliTest.enableMode )
      with CliTest.MaybeRunInConfigSession( cli ):
         cli.runCmd( "environment fan-speed auto" )
      
      # Reset pollInterval to default.
      defaultPollInterval = self.edut.aconsPathCmdIs(
         r"/ar/Sysdb/environment/thermostat/config",
         "print( _.defaultPollInterval )" )[ 0 ]
      self.edut.aconsPathCmdIs(
         r"/ar/Sysdb/environment/thermostat/config",
         f"_.pollInterval={defaultPollInterval}" )

   def collectDataRaw( self ):
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
            'AvgTrafficRate': round( self.getAvgTrafficRate(), 4 ),
            'Connected': self.getSystemIntfsConnectedCount()
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

   def collectData( self ):
      '''Return an object with all collected data'''
      avgFanRpm = avgSample( self.getAvgFanRpm, SAMPLE_COUNT )
      hottestOptic = avgSample( self.getHottestOpticTemp, SAMPLE_COUNT )
      hottestAsic = avgSample( self.getHottestAsicTemp, SAMPLE_COUNT )
      hottestCpuTemp = avgSample( self.getHottestCpuTemp, SAMPLE_COUNT )
      avgFanPwm = avgSample( self.getAvgFanPwm, SAMPLE_COUNT )
      cfm = self.getCFM( avgFanPwm )
      power = avgSample( self.getTotalSystemPower, SAMPLE_COUNT )
      inletTemp = avgSample( self.getInletTemp, SAMPLE_COUNT )
      outletTemp = avgSample( self.getOutletTemp, SAMPLE_COUNT )
      ssdTemp = avgSample( self.getSsdTemp, SAMPLE_COUNT )
      psuRpm = avgSample( self.getAvgPsuFanRpm, SAMPLE_COUNT )
      maxOpticTemp = 75 #TODO: make maxOpticTemp dynamic
      opticsMargin = maxOpticTemp - hottestOptic 
      opticsMargin30C = opticsMargin - ( 30 - inletTemp )

      return {
            'AvgRpm': round( avgFanRpm, 4 ),
            'HottestOptic': round( hottestOptic, 4 ),
            'HottestAsic': round( hottestAsic, 4),
            'HottestCpuTemp': round( hottestCpuTemp, 4),
            'AvgFanPwm': round( avgFanPwm, 4 ),
            'Airflow(CFM)': round( cfm, 4 ),
            'SystemPower': round( power, 4 ),
            'Inlet': round( inletTemp, 4 ),
            'Outlet': round( outletTemp, 4 ),
            'SsdTemp': round( ssdTemp, 4 ),
            'CFM/W': round(cfm / power, 4),
            'DeltaT': round( outletTemp - inletTemp, 4 ),
            'OpticsMargin': round( opticsMargin, 4 ),
            'OpticsMargin30C': round( opticsMargin30C, 4 ),
            'AvgPsusRpm': round( psuRpm, 4 ),
            'AvgTrafficRate': round( self.getAvgTrafficRate(), 4 ),
            'Connected': self.getSystemIntfsConnectedCount()
      }
   
   def checkSetup( self ):
      '''Confirms that the data collected is valid'''
      data = self.collectData()
      # Ignore deltaT and opticsMargin30C as they are calculated and maybe <= 0
      ignoreList = [ 'DeltaT', 'OpticsMargin', 'OpticsMargin30C' ]
      if 'whistler' in self.__class__.__name__.lower():
         ignoreList.append( 'AvgTrafficRate' )

      for key, val in data.items():
         if val <= 0 and key not in ignoreList:
            raise ValueError(f'{key} reading invalid value ({val})')

class MaunaKea( FbossFanTestEdut ):
   '''Class that implements methods specifically for Mauna Kea platforms'''
   def getFanMfr( self, id ):
      idBits = id & 0b111 # filter to fan id according to Mauna key table
      if idBits == 0:
         return 'SANYO DENKI'
      elif idBits == 1:
         return 'DELTA'
      else:
         raise ValueError( 'Fan mfr not detected' )

# FIXME: Monterey class is outdated
class Monterey( MaunaKea ):
   '''Class that defines some Monterey helpers to collect
   FSCD qualification data'''
   def getOpticTemps( self ):
      opticsTemps = {}
      shXcvr = self.edut.showCmdIs( 'show int transc', dataFormat='json' )[
                                    'interfaces' ]
      for intf in shXcvr:
         if 'temperature' in intf:
            opticsTemps[intf] = shXcvr[ intf ][ 'temperature' ]
      return opticsTemps

   def getAsicTemps( self ):
      asicTemps = []
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for entry in [ c[ 'tempSensors' ] for c in shTemp[ 'cardSlots' ] ]:
         for sensor in entry:
            # match 'Tomahawk4' or 'TH4'
            if re.search( 'Tomahawk|TH4', sensor[ 'description' ] ):
               asicTemps.append( sensor[ 'currentTemperature' ] )
      return asicTemps

   def getOutletTemp( self ):
      '''Return the inlet temperature'''
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for entry in [ c[ 'tempSensors' ] for c in shTemp[ 'cardSlots' ] ]:
         for sensor in entry:
            # Exact Match
            if re.search( 'Fan Board Ambient', sensor[ 'description' ] ):
               return sensor[ 'currentTemperature' ]
      return 0

   def getFanRpms( self ):
      rpmList = []
      maxSpeed = 0
      # Hacky, will only respect the last maxSpeed, but they should all be the
      # same. Can probably use Acons instead
      shCool = self.edut.showCmdIs( 'show sys env cool det',
                                     dataFormat='json' )
      for fanInfo in shCool[ 'fanTraySlots' ]:
         maxSpeed = fanInfo[ 'fans' ][ 0 ][ 'maxSpeed' ]

      for i in range( 1, 6 ):
         pct = self.edut.aconsPathCmdIs(
            r'/ar/Sysdb/environment/thermostat/status/fanConfig/Fan1\/{}/speed'.
            format( i ), 'ls -l' )[ 0 ].split( ' ' )[ -1 ]
         rpmList.append( maxSpeed * float( pct ) / 100.0 )
      return rpmList

   def getFanPwms( self ):
      '''Return Fan PWMs as a list, reported as a percentage'''
      pwms = []
      # read PWM registers and return them as a pct PWM
      # The registers store it as an unsigned integer 0->255
      for addr in [ 0x10, 0x20, 0x30, 0x40, 0x50 ]:
         pwms.append( int( self.edut.bashSuCmdIs(
            f'smbus read8 /scd/04/00/0x60 {addr}'.format(
            addr=addr ) )[ 0 ].split( ' ' )[ 0 ], 16 ) / 2.55 )
      return pwms

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

   def getFanIds( self ):
      '''Returns a list of fan Ids where indexes map to fan slots'''
      fanIds = []
      for addr in ( 0x61, 0x62, 0x63, 0x64 ):
         fanIds.append( int( self.edut.bashSuCmdIs(
            f'smbus read8 /scd/1/3/0x60 {addr}' )[ 0 ].split( ' ' )[ 0 ], 16 ) )
      return fanIds

   def getOpticTemps( self ):
      opticsTemps = {}
      shXcvr = self.edut.showCmdIs( 'show int transc', dataFormat='json' )[
                                    'interfaces' ]
      for intf in shXcvr:
         if 'temperature' in shXcvr[ intf ]:
            opticsTemps[intf] = shXcvr[ intf ][ 'temperature' ]
      if len( opticsTemps ) == 0:
         raise ValueError( "System does NOT have any optics" )
      return opticsTemps

   def getAsicTemps( self ):
      asicTemps = []
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for sensor in shTemp[ 'tempSensors' ]:
         # match all J3 sensors (exclude VRMs)
         if re.search( r'^(?=.*J3 )(?!.*VRM)', sensor[ 'description' ] ):
            asicTemps.append( sensor[ 'currentTemperature' ] )
      return asicTemps

   def getOutletTemp( self ):
      '''Return the outlet temperature'''
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for sensor in shTemp[ 'tempSensors' ]:
         # Exact Match
         if re.search( 'Board Rear', sensor[ 'description' ] ):
            return sensor[ 'currentTemperature' ]
      return 0

   def getCpuTemps( self ):
      '''Return the CPU temperature'''
      cpuTemps = []
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for sensor in shTemp[ 'tempSensors' ]:
         if re.search( r'^(?=.*CPU)(?!.*VRM)', sensor[ 'description' ] ):
            cpuTemps.append( sensor[ 'currentTemperature' ] )
      return cpuTemps
   
   def getSsdTemp( self ):
      '''Return the SSD temperature'''
      shTemp = self.edut.showCmdIs( 'sh sys stor health smart', dataFormat='json' )
      attributes = shTemp[ 'devices' ][ 'flash' ][ 'attributes' ]
      for attr in attributes:
         # Exact Match
         if attr[ 'name' ] == 'Temperature':
            return attr[ 'value' ]
      return 0

   def getFanRpms( self ):
      rpmList = []
      maxSpeed = 0
      # Hacky, will only respect the last maxSpeed, but they should all be the
      # same. Can probably use Acons instead
      shCool = self.edut.showCmdIs( 'show sys env cool det',
                                     dataFormat='json' )
      for fanInfo in shCool[ 'fanTraySlots' ]:
         maxSpeed = fanInfo[ 'fans' ][ 0 ][ 'maxSpeed' ]

      for i in range( 1, 4 + 1 ):
         pct = self.edut.aconsPathCmdIs(
            r'/ar/Sysdb/environment/thermostat/status/fanConfig/Fan{}\/1/speed'.
            format( i ), 'ls -l' )[ 0 ].split( ' ' )[ -1 ]
         rpmList.append( maxSpeed * float( pct ) / 100.0 )
      return rpmList

   def getPsuRpms( self ):
      '''Return a list of all system PSU fan RPMs'''
      rpmList = []
      maxSpeed = 0
      # Hacky, will only respect the last maxSpeed, but they should all be the
      # same. Can probably use Acons instead
      shCool = self.edut.showCmdIs( 'show sys env cool det',
                                     dataFormat='json' )
      for fanInfo in shCool[ 'powerSupplySlots' ]:
         maxSpeed = fanInfo[ 'fans' ][ 0 ][ 'maxSpeed' ]

      for i in range( 1, 2 + 1 ):
         pct = self.edut.aconsPathCmdIs(
            r'/ar/Sysdb/environment/thermostat/status/fanConfig/FanP{}\/1/speed'.
            format( i ), 'ls -l' )[ 0 ].split( ' ' )[ -1 ]
         rpmList.append( maxSpeed * float( pct ) / 100.0 )
      return rpmList

   def getFanPwms( self ):
      '''Return Fan PWMs as a list, reported as a percentage'''
      pwms = []
      # read PWM registers and return them as a pct PWM
      # The registers store it as an unsigned integer 0->255
      for addr in [ 0x10, 0x20, 0x30, 0x40 ]:
         pwms.append( int( self.edut.bashSuCmdIs(
            f'smbus read8 /scd/1/3/0x60 {addr}'.format(
            addr=addr ) )[ 0 ].split( ' ' )[ 0 ], 16 ) / 2.55 )
      return pwms

   def getCFM( self, pwm ):
      '''Return the CFM value for a given PWM'''
      fanId = self.getFanIds()[ 0 ] # Using cfm data of fan in the first slot
      fanVendor = self.getFanMfr( fanId )
      return self.calculateCFM( self.CFM_DATA, pwm, fanVendor )

class Whistler( MaunaKea ):
   '''Class that defines some Whistler helpers to collect
   FSCD qualification data'''

   CFM_DATA = {
      100: { 'SANYO DENKI': 898, 'DELTA': 946 },
      90: { 'SANYO DENKI': 846, 'DELTA': 907 },
      80: { 'SANYO DENKI': 778, 'DELTA': 823 },
      70: { 'SANYO DENKI': 699, 'DELTA': 735 },
      60: { 'SANYO DENKI': 615, 'DELTA': 649 },
      50: { 'SANYO DENKI': 538, 'DELTA': 566 },
      40: { 'SANYO DENKI': 450, 'DELTA': 478 },
      30: { 'SANYO DENKI': 370, 'DELTA': 389 },
      20: { 'SANYO DENKI': 285, 'DELTA': 301 },
      10: { 'SANYO DENKI': 203, 'DELTA': 214 },
      0: { 'SANYO DENKI': 203, 'DELTA': 214 }
   }

   def getFanSku( self ):
      return 'FAN-7021H-RED'

   def getFanIds( self ):
      '''Returns a list of fan Ids where indexes map to fan slots'''
      fanIds = []
      for cpldAddr in ( 0x60, 0x61, 0x62 ):
         for fanReg in ( 0x61, 0x62, 0x63, 0x64 ):
            fanIds.append( int( self.edut.bashSuCmdIs(
               f'smbus read8 /scd/1/3/{cpldAddr} {fanReg}' 
               )[ 0 ].split( ' ' )[ 0 ], 16 ) )

      if not all( x == fanIds[ 0 ] for x in fanIds ):
         print( "WARN: Not all inserted fans are identical. For CFM calculations, \
               test data from the fan in the first slot will be used" )

      return fanIds

   def getOpticTemps( self ):
      opticsTemps = {}
      shXcvr = self.edut.showCmdIs( 'show int transc', dataFormat='json' )[
                                    'interfaces' ]
      for intf in shXcvr:
         if 'temperature' in shXcvr[ intf ]:
            opticsTemps[intf] = shXcvr[ intf ][ 'temperature' ]
      if len( opticsTemps ) == 0:
         raise ValueError( "System does NOT have any optics" )
      return opticsTemps

   def getAsicTemps( self ):
      asicTemps = []
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for sensor in shTemp[ 'tempSensors' ]:
         if re.search( 'Fe0|Fe1', sensor[ 'description' ] ):
            asicTemps.append( sensor[ 'currentTemperature' ] )
      return asicTemps

   def getOutletTemp( self ):
      '''Return the outlet temperature'''
      temps = []
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for sensor in shTemp[ 'tempSensors' ]:
         # Max temp of one of the 3 Fan Cards
         if re.search( 'Fan Card', sensor[ 'description' ] ):
            temps.append( sensor[ 'currentTemperature' ] )
      return max( temps )

   def getCpuTemps( self ):
      '''Return the CPU temperature'''
      cpuTemps = []
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for sensor in shTemp[ 'tempSensors' ]:
         if re.search( r'^(?=.*CPU)(?!.*VRM)', sensor[ 'description' ] ):
            cpuTemps.append( sensor[ 'currentTemperature' ] )
      return cpuTemps
   
   def getSsdTemp( self ):
      '''Return the SSD temperature'''
      shTemp = self.edut.showCmdIs( 'sh sys stor health smart', dataFormat='json' )
      attributes = shTemp[ 'devices' ][ 'flash' ][ 'attributes' ]
      for attr in attributes:
         # Exact Match
         if attr[ 'name' ] == 'Temperature':
            return attr[ 'value' ]
      return 0

   def getFanRpms( self ):
      rpmList = []
      maxSpeed = 0
      # Hacky, will only respect the last maxSpeed, but they should all be the
      # same. Can probably use Acons instead
      shCool = self.edut.showCmdIs( 'show sys env cool det',
                                     dataFormat='json' )
      for fanInfo in shCool[ 'fanTraySlots' ]:
         maxSpeed = fanInfo[ 'fans' ][ 0 ][ 'maxSpeed' ]

      for i in range( 1, 12 + 1 ):
         pct = self.edut.aconsPathCmdIs(
            r'/ar/Sysdb/environment/thermostat/status/fanConfig/Fan{}\/1/speed'.
            format( i ), 'ls -l' )[ 0 ].split( ' ' )[ -1 ]
         rpmList.append( maxSpeed * float( pct ) / 100.0 )
      return rpmList

   def getPsuRpms( self ):
      '''Return a list of all system PSU fan RPMs'''
      rpmList = []
      maxSpeed = 0
      # Hacky, will only respect the last maxSpeed, but they should all be the
      # same. Can probably use Acons instead
      shCool = self.edut.showCmdIs( 'show sys env cool det',
                                     dataFormat='json' )
      for fanInfo in shCool[ 'powerSupplySlots' ]:
         maxSpeed = fanInfo[ 'fans' ][ 0 ][ 'maxSpeed' ]

      for i in range( 1, 4 + 1 ):
         pct = self.edut.aconsPathCmdIs(
            r'/ar/Sysdb/environment/thermostat/status/fanConfig/FanP{}\/1/speed'.
            format( i ), 'ls -l' )[ 0 ].split( ' ' )[ -1 ]
         rpmList.append( maxSpeed * float( pct ) / 100.0 )
      return rpmList

   def getFanPwms( self ):
      '''Return Fan PWMs as a list, reported as a percentage'''
      pwms = []
      # read PWM registers and return them as a pct PWM
      # The registers store it as an unsigned integer 0->255

      for cpldAddr in ( 0x60, 0x61, 0x62 ):
         for fanReg in ( 0x10, 0x20, 0x30, 0x40 ):
            pwms.append( int( self.edut.bashSuCmdIs(
               f'smbus read8 /scd/1/3/{cpldAddr} {fanReg}' )
               [ 0 ].split( ' ' )[ 0 ], 16 ) / 2.55 )
      return pwms

   def getCFM( self, pwm ):
      '''Return the CFM value for a given PWM'''
      fanId = self.getFanIds()[ 0 ] # Using cfm data of fan in the first slot
      fanVendor = self.getFanMfr( fanId )
      return self.calculateCFM( self.CFM_DATA, pwm, fanVendor )

class WhistlerSystemZone( Whistler ):
   '''Updates functions to only test fans within the System zone'''

   def getFanIds( self ):
      '''Returns a list of fan Ids where indexes map to fan slots'''
      fanIds = []

      for cpldAddr in ( 0x61, 0x62 ):
         for fanReg in ( 0x61, 0x62, 0x63, 0x64 ):
            fanIds.append( int( self.edut.bashSuCmdIs(
               f'smbus read8 /scd/1/3/{cpldAddr} {fanReg}' 
               )[ 0 ].split( ' ' )[ 0 ], 16 ) )

      if not all( x == fanIds[ 0 ] for x in fanIds ):
         print( "WARN: Not all inserted fans are identical. For CFM calculations, \
               test data from the fan in the first slot will be used" )

      return fanIds

   def getFanRpms( self ):
      rpmList = []
      maxSpeed = 0

      shCool = self.edut.showCmdIs( 'show sys env cool det',
                                     dataFormat='json' )
      for fanInfo in shCool[ 'fanTraySlots' ]:
         maxSpeed = fanInfo[ 'fans' ][ 0 ][ 'maxSpeed' ]

      for i in range( 5, 12 + 1 ):
         pct = self.edut.aconsPathCmdIs(
            r'/ar/Sysdb/environment/thermostat/status/fanConfig/Fan{}\/1/speed'.
            format( i ), 'ls -l' )[ 0 ].split( ' ' )[ -1 ]
         rpmList.append( maxSpeed * float( pct ) / 100.0 )
      return rpmList

   def getFanPwms( self ):
      '''Return Fan PWMs as a list, reported as a percentage'''
      pwms = []
      # read PWM registers and return them as a pct PWM
      # The registers store it as an unsigned integer 0->255

      for cpldAddr in ( 0x61, 0x62 ):
         for fanReg in ( 0x10, 0x20, 0x30, 0x40 ):
            pwms.append( int( self.edut.bashSuCmdIs(
               f'smbus read8 /scd/1/3/{cpldAddr} {fanReg}' )
               [ 0 ].split( ' ' )[ 0 ], 16 ) / 2.55 )
      return pwms

   def setFanSpeed( self, pct ):
      '''Set fan speed as a % of max fan RPM for System zone'''
      # Set System zone fans speed
      for fanIdx in range( 5, 12 + 1 ):
         self.edut.aconsPathCmdIs(
            fr"/ar/Sysdb/environment/thermostat/status/fanConfig/Fan{fanIdx}\/1",
            f"_.speed={pct}" )
      # Set Asic zone fans speed to 20%
      for fanIdx in range( 1, 4 + 1 ):
         self.edut.aconsPathCmdIs(
            fr"/ar/Sysdb/environment/thermostat/status/fanConfig/Fan{fanIdx}\/1",
            f"_.speed=20" )

class WhistlerAsicZone( Whistler ):
   '''Updates functions to only test fans within the Asic zone'''

   def getFanIds( self ):
      '''Returns a list of fan Ids where indexes map to fan slots'''
      fanIds = []
      cpldAddr = 0x60
      
      for fanReg in ( 0x61, 0x62, 0x63, 0x64 ):
         fanIds.append( int( self.edut.bashSuCmdIs(
            f'smbus read8 /scd/1/3/{cpldAddr} {fanReg}' 
            )[ 0 ].split( ' ' )[ 0 ], 16 ) )

      if not all( x == fanIds[ 0 ] for x in fanIds ):
         print( "WARN: Not all inserted fans are identical. For CFM calculations, \
               test data from the fan in the first slot will be used" )

      return fanIds

   def getFanRpms( self ):
      rpmList = []
      maxSpeed = 0

      shCool = self.edut.showCmdIs( 'show sys env cool det',
                                     dataFormat='json' )
      for fanInfo in shCool[ 'fanTraySlots' ]:
         maxSpeed = fanInfo[ 'fans' ][ 0 ][ 'maxSpeed' ]

      for i in range( 1, 4 + 1 ):
         pct = self.edut.aconsPathCmdIs(
            r'/ar/Sysdb/environment/thermostat/status/fanConfig/Fan{}\/1/speed'.
            format( i ), 'ls -l' )[ 0 ].split( ' ' )[ -1 ]
         rpmList.append( maxSpeed * float( pct ) / 100.0 )
      return rpmList

   def getFanPwms( self ):
      '''Return Fan PWMs as a list, reported as a percentage'''
      pwms = []
      cpldAddr = 0x60
      # read PWM registers and return them as a pct PWM
      # The registers store it as an unsigned integer 0->255

      for fanReg in ( 0x10, 0x20, 0x30, 0x40 ):
         pwms.append( int( self.edut.bashSuCmdIs(
            f'smbus read8 /scd/1/3/{cpldAddr} {fanReg}' )
            [ 0 ].split( ' ' )[ 0 ], 16 ) / 2.55 )
      return pwms

   def setFanSpeed( self, pct ):
      '''Set fan speed as a % of max fan RPM for System zone'''
      # Set Asic zone fans speed
      for fanIdx in range( 1, 4 + 1 ):
         self.edut.aconsPathCmdIs(
            fr"/ar/Sysdb/environment/thermostat/status/fanConfig/Fan{fanIdx}\/1",
            f"_.speed={pct}" )
      # Set System zone fans speed to 30%
      for fanIdx in range( 5, 12 + 1 ):
         self.edut.aconsPathCmdIs(
            fr"/ar/Sysdb/environment/thermostat/status/fanConfig/Fan{fanIdx}\/1",
            f"_.speed=30" )

def renderPlot( pdf, dfX, dfY, title ):
   fig, ax = plt.subplots(figsize=( 8, 6 ))
   for column in dfY:
      ax.plot( dfX, dfY[ column ], label=column, marker='o' )
   ax.set_title( title )
   ax.set_xlabel( dfX.name )
   ax.legend()
   ax.grid( True )
   pdf.savefig( fig )
   plt.close( fig )  

def parseArgs( argv ):
   parser = argparse.ArgumentParser(
         prog='CollectFanSweepData', description=tool_description )
   parser.add_argument( '-d', '--dut', help='Dut to setup fan data collection' )
   parser.add_argument( '-z', '--zone', help='Specify cooling zone if valid' )
   parser.add_argument( '--soak-time', type=int, default=30,
         help='Number minutes to soak at each step' )
   parser.add_argument( '--rpms', metavar='N', type=int, nargs='*',
         default=DEFAULT_RPMS, help='List of RPMs to iterate through')
   parser.add_argument( '--ignore-checks',action='store_true', default=False,
         help='Ignore pre-test checks' )
   return parser.parse_args( argv )

def main( argv ):
   args = parseArgs( argv )
   if args.dut:
      edut = ArosTest.getEdut( args.dut )
   else:
      edut = defaultEdut()
   ArosTest.ownOrElse( ArosTest.getDut( edut.name() ) )

   if edut.product() == 'Monterey':
      obj = Monterey( edut )
   elif edut.product() in ( 'Viper', 'ViperJ3' ):
      obj = Viper( edut )
   elif edut.product() in ( 'Whistler' ):
      if args.zone.lower() == 'asic':
         obj = WhistlerAsicZone( edut )
      elif args.zone.lower() == 'system':
         obj = WhistlerSystemZone( edut )
      else:
         obj = Whistler( edut )
   else:
      assert( 'Product Class not defined for {}'.format( edut.product() ) )

   # Confirm readings are valid
   if not args.ignore_checks:
      obj.checkSetup()

   # Get system info
   sysInfo = obj.getSystemInfo()
   sysIntfs = obj.getSystemIntfs()
   sysIntfsRates = obj.getSystemIntfsCountRates()
   sysEnvTemp = obj.getSystemEnvTemp()
   sysIntfsTemp = obj.getSystemIntfsTemp()
   fanIds = obj.getFanIds()
   fanSku = obj.getFanSku()

   df = pd.DataFrame( columns=[
      'TargetRpm', 'AvgRpm', 'HottestOptic', 'HottestAsic', 'HottestCpuTemp', 'AvgFanPwm',
      'Airflow(CFM)', 'SystemPower', 'Inlet', 'Outlet', 'SsdTemp', 'CFM/W', 'DeltaT',
      'OpticsMargin', 'OpticsMargin30C', 'AvgPsusRpm', 'AvgTrafficRate', 'Connected' ] )

   obj.overridePidAlgo()

   current_time = datetime.datetime.now()
   timestamp = current_time.strftime( '%Y%m%d_%H%M%S' )
   filename = f'{args.dut}_{timestamp}'

   with open( f'{filename}_RAW.csv', 'w', newline='' ) as csvfile:
      fieldnames = ['Timestamp', 'TargetRpm'] + list(obj.collectDataRaw().keys())
      csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
      csvwriter.writeheader()

      for targetRpm in args.rpms:
         print( f'Setting fan speed to {targetRpm}' )
         obj.setFanSpeed( targetRpm )

         # FIXME: For whistler, the log is so large and takes about 20 seconds.
         # This limits the soak time on whistler to 20 minutes minimum
         for _ in range( args.soak_time * 6 ):
            start_time = time.time()
            dataRaw = obj.collectDataRaw()
            timestamp = datetime.datetime.now().strftime( '%Y-%m-%d_%H:%M:%S' )
            row = {'Timestamp': timestamp, 'TargetRpm': targetRpm}
            row.update(dataRaw)
            csvwriter.writerow(row)
            end_time = time.time()
            time_wasted = end_time - start_time
            sleep_time = 10 - time_wasted

            if sleep_time > 0:
               time.sleep(sleep_time)

         data = obj.collectData()
         data[ 'TargetRpm' ] = targetRpm

         print( data )
         df = df.append( data, ignore_index=True )

   with PdfPages( f'{filename}.pdf' ) as pdf:
      # Cover page
      fig, ax = plt.subplots()
      coverLog = f'''
         System: {args.dut}\n
         Timestamp: {timestamp}\n
         Soak Time: {args.soak_time} Minutes\n
         RPMs List: {args.rpms}
      '''
      ax.text( 0, 1, coverLog, fontsize = 9, va = 'top', ha = 'left', wrap = True )
      ax.axis( 'off' )
      pdf.savefig( fig )
      plt.close( fig )
  
      # Fans info
      fans_log = [ 'Fans Info\n' ]
      for fanIdx, fanId in enumerate( fanIds ):
          binaryId = format(fanId, '08b')
          fanLog = f'Fan {fanIdx + 1} ID: {binaryId}. \
            Fan SKU: {fanSku} ({obj.getFanMfr(fanId)})'
          fans_log.append( fanLog )
      fig, ax = plt.subplots()
      ax.text( 0, 1, "\n".join( fans_log ), fontsize = 9,
              va = 'top', ha = 'left' )
      ax.axis( 'off' )
      pdf.savefig( fig )
      plt.close( fig )

      # sysInfo log
      fig = plt.figure( figsize = ( 8, 11 ) )
      ax = fig.add_subplot()
      ax.text( 0, 1, "\n".join(sysInfo), fontsize = 6, va = 'top', ha = 'left',
              transform = fig.transFigure )
      ax.axis( 'off' )
      pdf.savefig( fig,bbox_inches='tight' )
      plt.close( fig )

      # sysIntfs log
      fig = plt.figure()
      ax = fig.add_subplot()
      ax.text( 0, 1, "\n".join(sysIntfs), fontsize = 6, va = 'top', ha = 'left',
               transform = fig.transFigure )
      ax.axis( 'off' )
      pdf.savefig( fig, bbox_inches='tight' )
      plt.close( fig )

      # sysIntfsRates log
      fig = plt.figure()
      ax = fig.add_subplot()
      ax.text( 0, 1, "\n".join(sysIntfsRates), fontsize = 6, va = 'top', ha = 'left',
              transform = fig.transFigure )
      ax.axis( 'off' )
      pdf.savefig( fig, bbox_inches='tight' )
      plt.close( fig )

      # sysEnvTemp log
      fig = plt.figure( figsize = ( 8, 11 ) )
      ax = fig.add_subplot()
      ax.text( 0, 1, "\n".join( sysEnvTemp ), fontsize = 6, va = 'top', ha = 'left',
              transform = fig.transFigure )
      ax.axis( 'off' )
      pdf.savefig( fig, bbox_inches='tight' )
      plt.close( fig )

      # sysIntfsTemp log
      fig = plt.figure( figsize = ( 8, 11 ) )
      ax = fig.add_subplot()
      ax.text( 0, 1, "\n".join( sysIntfsTemp ), fontsize = 6, va = 'top', ha = 'left',
              transform = fig.transFigure )
      ax.axis( 'off' )
      pdf.savefig( fig, bbox_inches='tight' )
      plt.close( fig )

      # Create a table of the data
      fig, ax = plt.subplots( figsize = ( 11, 8 ) )
      ax.axis( 'off' )
      tbl = ax.table( cellText = df.values, colLabels = df.columns,
                     cellLoc = 'center', loc = 'center', transform = fig.transFigure  )
      tbl.auto_set_font_size(False)
      tbl.set_fontsize(6)
      pdf.savefig( fig, bbox_inches='tight' )
      plt.close( fig )

      # Adding graphs of the data
      y_axis = df[ [ 'HottestOptic', 'HottestAsic', 'HottestCpuTemp',
                    'SsdTemp', 'Inlet', 'Outlet' ] ]
      renderPlot( pdf, df[ 'AvgFanPwm' ], y_axis, 'Temperatures' )

      y_axis = df[ [ 'AvgFanPwm' ] ]
      renderPlot( pdf, df[ 'Airflow(CFM)' ], y_axis, 'Airflow(CFM)' )

      y_axis = df[ [ 'SystemPower' ] ]
      renderPlot( pdf, df[ 'AvgFanPwm' ], y_axis, 'System Power' )

      y_axis = df[ [ 'Airflow(CFM)' ] ]
      renderPlot( pdf, df[ 'SystemPower' ], y_axis, 'CFM/W' )

   # write collected data to a csv 
   df.to_csv( f'{filename}.csv', index = False )

   # Renable PID algo
   obj.enablePidAlgo()

if __name__ == '__main__':
   sys.exit( main( sys.argv[ 1 : ] ) )
