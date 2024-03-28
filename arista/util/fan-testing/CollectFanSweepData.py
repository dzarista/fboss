#!/usr/bin/env arista-python

# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import ArosTest
from ArosTest.DutMgmt import defaultEdut

import argparse
import datetime
import pandas as pd
import re
import sys
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

tool_description = '''This script is intended to collect some thermal data on
a system for intention of generating some Thermal fan control tables
for FBOSS/OpenBMC.

This script will collect various datapoints according to the options passed and
can generate a csv, which can be maually inspected and processed to generate
a table for certain temperature sensors to PWM.

For Example:
python3 CollectFanSweepData.py -d vpr114 --start-rpm 30 --end-rpm 100
--stride 10 --soak-time 60'''

def getAverage( data ):
   '''Return an average of a data formatted as a list'''
   if len( data ) == 0:
      return 0
   return sum( data ) / len( data )

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
      raise NotImplementedError

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
      if pwm < 0 or pwm > 100:
         raise ValueError("PWM must be between 0 and 100.")
   
      lowerBoundPwm = ( pwm // 10 ) * 10
      upperBoundPwm = min( ( ( pwm + 9 ) // 10 ) * 10, 100 )

      lowerBoundCfm = cfmTable[ lowerBoundPwm ][ fanVendor ]
      upperBoundCfm = cfmTable[ upperBoundPwm ][ fanVendor ]

      return int( ( upperBoundCfm + lowerBoundCfm )/2 )

   def getCFM( self, pwm ):
      '''Return the CFM value for a given PWM'''
      return NotImplementedError

   def getTotalSystemPower( self ):
      '''Return the total system power in Watts'''
      totalPower = 0.0
      shPower = self.edut.showCmdIs( 'show sys env pow',
                                     dataFormat='json' )
      for slot in shPower[ 'powerSupplies' ]:
         totalPower += shPower[ 'powerSupplies' ][
                                slot ][ 'outputPower' ]
      return totalPower

   def shutEosFanControl( self ):
      '''Shut down EOS fan control algorithm'''
      self.edut.aconsPathCmdIs(
            r"/ar/Sysdb/environment/thermostat/config",
            "_.mode='manual'" )

   def StartEosFanControl( self ):
      '''Start down EOS fan control algorithm'''
      self.edut.aconsPathCmdIs(
            r"/ar/Sysdb/environment/thermostat/config",
            "_.mode='automatic'" )

   def getFanRpms( self ):
      '''Return a list of all system fan RPMs'''
      raise NotImplementedError

   def getFanPwms( self ):
      '''Return a list of all system fan PWM (%)'''
      raise NotImplementedError

   def setPwm( self, pwm ):
      '''Set pwm (0-100%) on all fans'''
      raise NotImplementedError

   def getHottestOpticTemp( self ):
      return max( self.getOpticTemps() )

   def getHottestAsicTemp( self ):
      return max( self.getAsicTemps() )

   def getHottestCpuTemp( self ):
      return max( self.getCpuTemps() )

   def getAvgFanRpm( self ):
      '''Return average system fan RPMs'''
      return getAverage( self.getFanRpms() )

   def getAvgFanPwm( self ):
      '''Return average system fan Pwms'''
      return getAverage( self.getFanPwms() )
   
   def getSystemInfo( self ):
      return self.edut.showCmdIs( 'show inv' )

   def getSystemIntfs( self ):
      return self.edut.showCmdIs( 'show int st' )

   def getSystemIntfsCountRates( self ):
      return self.edut.showCmdIs( 'show int count rates' )

   def getSystemEnvTemp( self ):
      return self.edut.showCmdIs( 'show sys env temp' )

   def getSystemIntfsTemp( self ):
      return self.edut.showCmdIs( 'show sys env temp transceiver' )

   def collectData( self ):
      '''Return an object with all collected data'''
      avgFanPwm = self.getAvgFanPwm()
      return {
            'AvgRpm': self.getAvgFanRpm(),
            'HottestOptic': self.getHottestOpticTemp(),
            'HottestAsic': self.getHottestAsicTemp(),
            'HottestCpuTemp': self.getHottestCpuTemp(),
            'AvgFanPwm': avgFanPwm,
            'Airflow(CFM)': self.getCFM( avgFanPwm ),
            'SystemPower': self.getTotalSystemPower(),
            'Inlet': self.getInletTemp(),
            'Outlet': self.getOutletTemp(),
            'ssdTemp': self.getSsdTemp()
      }
   
   def checkSetup( self ):
      '''Confirms that the data collected is valid'''
      data = self.collectData()
      for key, value in data.items():
         if value <= 0:
            raise ValueError(f'{key} reading invalid value ({value})')

# FIXME: Monterey class is outdated
class Monterey( FbossFanTestEdut ):
   '''Class that defines some Monterey helpers to collect
   FSCD qualification data'''
   def getOpticTemps( self ):
      opticsTemps = []
      shXcvr = self.edut.showCmdIs( 'show int transc', dataFormat='json' )[
                                    'interfaces' ]
      for intf in shXcvr:
         if 'temperature' in intf:
            opticsTemps.append( shXcvr[ intf ][ 'temperature' ] )
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

   def getInletTemp( self ):
      '''Return the inlet temperature'''
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for entry in [ c[ 'tempSensors' ] for c in shTemp[ 'cardSlots' ] ]:
         for sensor in entry:
            # Exact Match
            if re.search( 'Front-panel temp sensor', sensor[ 'description' ] ):
               return sensor[ 'currentTemperature' ]
      return 0

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

   def setFanRpm( self, pct ):
      'Set fan speed as a % of max fan RPM'
      self.shutEosFanControl()
      self.edut.aconsPathCmdIs(
            '/ar/Sysdb/environment/thermostat/config',
            f'_.fanSpeed={pct}'.format( pct=pct ) )

   def setPwm( self, pwm ):
      # pwm comes in as a %, set it as an integer range 0->255
      # requires agents to not set pwm
      pwm = int( 255.0 * pwm / 100.0 )
      for addr in [ 0x10, 0x20, 0x30, 0x40, 0x50 ]:
         self.edut.bashCmdIs(
               f'smbus write8 /scd/04/00/0x60 {addr} {pwm}'.format(
               addr=addr, pwm=pwm ) )

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

class Viper( FbossFanTestEdut ):
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

   def getFanMfr( self, id ):
      idBits = id & 0b111 # filter to fan id according to Mauna key table
      if idBits == 0:
         return 'SANYO DENKI'
      elif idBits == 1:
         return 'DELTA'
      else:
         raise ValueError( 'Fan mfr not detected' )

   def getFanIds( self ):
      '''Returns a list of fan Ids where indexes map to fan slots'''
      fanIds = []
      for addr in [ 0x61, 0x62, 0x63, 0x64 ]:
         fanIds.append( int( self.edut.bashSuCmdIs(
            f'smbus read8 /scd/1/3/0x60 {addr}'.format(
            addr=addr ) )[ 0 ].split( ' ' )[ 0 ], 16 ) )
      
      if not all( x == fanIds[ 0 ] for x in fanIds ):
         print( "WARN: Not all inserted fans are identical. For CFM calculations, \
               test data from the fan in the first slot will be used" )

      return fanIds

   def getOpticTemps( self ):
      opticsTemps = []
      shXcvr = self.edut.showCmdIs( 'show int transc', dataFormat='json' )[
                                    'interfaces' ]
      for intf in shXcvr:
         if 'temperature' in shXcvr[ intf ]:
            opticsTemps.append( shXcvr[ intf ][ 'temperature' ] )
      if len( opticsTemps ) == 0:
         raise ValueError( "System does NOT have any optics" )
      return opticsTemps

   def getAsicTemps( self ):
      asicTemps = []
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for sensor in shTemp[ 'tempSensors' ]:
         # match 'Jericho3' or 'J3'
         if re.search( 'Jericho3|J3', sensor[ 'description' ] ):
            asicTemps.append( sensor[ 'currentTemperature' ] )
      return asicTemps

   def getInletTemp( self ):
      '''Return the inlet temperature'''
      shTemp = self.edut.showCmdIs( 'show sys env temp', dataFormat='json' )
      for sensor in shTemp[ 'tempSensors' ]:
         # Exact Match
         if re.search( 'Board front', sensor[ 'description' ] ):
            return sensor[ 'currentTemperature' ]
      return 0

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
         if re.search( 'CPU', sensor[ 'description' ] ):
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

   def setFanRpm( self, pct ):
      'Set fan speed as a % of max fan RPM'
      self.shutEosFanControl()
      self.edut.aconsPathCmdIs(
            '/ar/Sysdb/environment/thermostat/config',
            f'_.fanSpeed={pct}'.format( pct=pct ) )

   def setPwm( self, pwm ):
      # pwm comes in as a %, set it as an integer range 0->255
      # requires agents to not set pwm
      pwm = int( 255.0 * pwm / 100.0 )
      for addr in [ 0x10, 0x20, 0x30, 0x40 ]:
         self.edut.bashCmdIs(
               f'smbus write8 /scd/1/3/0x60 {addr} {pwm}'.format(
               addr=addr, pwm=pwm ) )

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
   parser.add_argument( '--stride', type=int, default=10,
         help='RPM percent step size between start/end' )
   parser.add_argument( '--soak-time', type=int, default=30,
         help='Number minutes to soak at each step' )
   parser.add_argument( '--start-rpm', type=int, default=0,
         help='Minimum percent of maxRPM to start collecting data' )
   parser.add_argument( '--end-rpm', type=int, default=100,
         help='Maximum percent of maxRPM to start collecting data' )

   parser.add_argument( '--csv', action='store_true' )
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
   elif edut.product() in ( 'Viper', 'ViperJ3', 'ViperJ3' ):
      obj = Viper( edut )
   elif edut.product() in ( 'Whistler' ):
      # TODO: add Whistler support
      pass
   else:
      assert( 'Product Class not defined for {}'.format( edut.product() ) )

   # Confirm readings are valid
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
      'TargetRpm', 'AvgRpm', 'HottestOptic',
      'HottestAsic', 'AvgFanPwm', 'Airflow(CFM)', 'SystemPower',
      'Inlet', 'Outlet' ] )

   for targetRpm in range( args.start_rpm, args.end_rpm + 1, args.stride ):
      obj.setFanRpm( targetRpm )
      time.sleep( args.soak_time * 60 )

      Data = obj.collectData()
      Data['TargetRpm'] = targetRpm

      print( Data )
      df = df.append( Data, ignore_index=True )

   current_time = datetime.datetime.now()
   timestamp = current_time.strftime( '%Y%m%d_%H%M%S' )
   filename = f'{args.dut}_{timestamp}'

   with PdfPages( f'{filename}.pdf' ) as pdf:
      # Cover page
      fig, ax = plt.subplots()
      coverLog = f'''
         System: {args.dut}\n
         Timestamp: {timestamp}\n
         Soak Time: {args.soak_time} Minutes\n
         Stride Size: {args.stride}%
      '''
      ax.text( 0, 1, coverLog, fontsize = 12, va = 'top', ha = 'left' )
      ax.axis( 'off' )
      pdf.savefig( fig )
      plt.close( fig )
  
      # Fans info
      fans_log = [ 'Fans Info\n' ]
      for fanIdx, fanId in enumerate( fanIds ):
          binaryId = format(fanId, '08b')
          fanLog = f'Fan {fanIdx + 1} ID: {binaryId}. \n\
            Fan SKU: {fanSku} ({obj.getFanMfr(fanId)})'
          fans_log.append( fanLog )
      fig, ax = plt.subplots()
      ax.text( 0, 1, "\n\n".join( fans_log ), fontsize = 12,
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
      pdf.savefig( fig )
      plt.close( fig )

      # sysIntfs log
      fig = plt.figure( figsize = ( 8, 20 ) )
      ax = fig.add_subplot()
      ax.text( 0, 1, "\n".join(sysIntfs), fontsize = 6, va = 'top', ha = 'left',
               transform = fig.transFigure )
      ax.axis( 'off' )
      pdf.savefig( fig )
      plt.close( fig )

      # sysIntfsRates log
      fig = plt.figure( figsize = ( 8, 11 ) )
      ax = fig.add_subplot()
      ax.text( 0, 1, "\n".join(sysIntfsRates), fontsize = 6, va = 'top', ha = 'left',
              transform = fig.transFigure )
      ax.axis( 'off' )
      pdf.savefig( fig )
      plt.close( fig )

      # sysEnvTemp log
      fig = plt.figure( figsize = ( 8, 11 ) )
      ax = fig.add_subplot()
      ax.text( 0, 1, "\n".join( sysEnvTemp ), fontsize = 6, va = 'top', ha = 'left',
              transform = fig.transFigure )
      ax.axis( 'off' )
      pdf.savefig( fig )
      plt.close( fig )

      # sysIntfsTemp log
      fig = plt.figure( figsize = ( 8, 11 ) )
      ax = fig.add_subplot()
      ax.text( 0, 1, "\n".join( sysIntfsTemp ), fontsize = 6, va = 'top', ha = 'left',
              transform = fig.transFigure )
      ax.axis( 'off' )
      pdf.savefig( fig )
      plt.close( fig )

      # Create a table of the data
      fig, ax = plt.subplots( figsize = ( 8, 3 ) )
      ax.axis( 'off' )
      tbl = ax.table( cellText = df.values, colLabels = df.columns,
                     cellLoc = 'center', loc = 'center' )
      tbl.auto_set_font_size( True )
      tbl.scale( 1.2, 1.2 )
      pdf.savefig( fig )
      plt.close( fig )

      # Adding graphs of the data
      y_axis = df[ [ 'HottestOptic', 'HottestAsic', 'HottestCpuTemp',
                    'ssdTemp', 'Inlet', 'Outlet' ] ]
      renderPlot( pdf, df[ 'AvgFanPwm' ], y_axis, 'Temperatures' )

      y_axis = df[ [ 'AvgFanPwm' ] ]
      renderPlot( pdf, df[ 'Airflow(CFM)' ], y_axis, 'Airflow(CFM)' )

      y_axis = df[ [ 'SystemPower' ] ]
      renderPlot( pdf, df[ 'AvgFanPwm' ], y_axis, 'System Power' )

      y_axis = df[ [ 'Airflow(CFM)' ] ]
      renderPlot( pdf, df[ 'SystemPower' ], y_axis, 'CFM/W' )

   # write collected data to a csv 
   df.to_csv( f'{filename}.csv', index = False )

if __name__ == '__main__':
   sys.exit( main( sys.argv[ 1 : ] ) )
