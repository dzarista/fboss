#!/usr/bin/env python3
# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from collections import OrderedDict
import csv
import json
import numpy
import re
import sys

# This is for debug purposes so the script drops into pdb if it crashes.
import Tac

# Temperatures approximating the following use cases (add +2 C for every 3000 ft):
# 25 C ambient @ sea level / 3000 ft / 6000 ft
# 30 C ambient @ sea level / 3000 ft / 6000 ft
# 35 C ambient @ sea level / 3000 ft / 6000 ft
# 40 C ambient @ sea level
TARGET_TEMPS = [ 25, 27, 30, 32, 35, 37, 40 ]

class OpticProfile:
   '''A profile for one optic group in FBOSS fan_service.'''

   def __init__( self, opticDict ):
      self.name = opticDict[ 'opticName' ]
      self.speedToLut = {}
      for label, lut in opticDict[ 'tempToPwmMaps' ].items():
         speedMatch = re.match( r'OPTIC_TYPE_(\d+)_GENERIC', label )
         assert speedMatch, 'Can\t tell speed from label'
         speed = int( speedMatch.group( 1 ) )
         self.speedToLut[ speed ] = OrderedDict(
               ( int( key ), value ) for key, value in lut.items()
         )

class SensorProfile:
   '''A profile for one sensor in FBOSS fan_service.'''

   def __init__( self, sensorDict ):
      self.name = sensorDict[ 'sensorName' ]
      self.lut = {
            int( key ) : value for key, value in
            sensorDict[ 'normalUpTable' ].items()
      }

class FbossFanAlgorithm:
   '''Takes a fan_service config JSON file and simulates behavior based on inputs.
   Obviously doesn't account for transient fluctuations but can be helpful.'''

   def __init__( self, jsonFile ):
      with open( jsonFile ) as jf:
         algDict = json.loads( jf.read() )
      self.lowPwm = algDict[ 'pwmLowerThreshold' ]
      self.highPwm = algDict[ 'pwmUpperThreshold' ]
      self.opticProfiles = [
            OpticProfile( opticDict ) for opticDict in algDict[ 'optics' ]
      ]
      self.sensorProfiles = [
            SensorProfile( sensorDict ) for sensorDict in algDict[ 'sensors' ]
      ]

   def getOpticProfileForSpeed( self, speed ):
      '''For the given front-panel port speed, find the relevant thermal profile in
      the configuration.'''

      for opticProfile in self.opticProfiles:
         lut = opticProfile.speedToLut.get( speed )
         if lut:
            return lut
      return None

   def getSteadyState( self, opticSpeed, ambientTemp, defaultPwm, profile, slope ):
      '''Given the front-panel port speed, ambient temperature, starting fan PWM,
      and a thermal profile, simulate the fan algorithm and report on the final
      state. Will tell if the algorithm yields a stable PWM.'''

      lut = self.getOpticProfileForSpeed( opticSpeed )
      assert lut

      lastPwm = None
      currPwm = defaultPwm
      currState = None
      numIters = 1
      stable = False
      while not stable and numIters < 20:
         lastPwm = currPwm
         currState = profile.getState( ambientTemp, lastPwm )

         # Find target PWM for current optic temp
         for opticTemp, pwmTarget in lut.items():
            if currState.maxOpticTemp >= opticTemp:
               pwmToProgram = pwmTarget

         # Gradually approach pwmTarget using the provided slope
         if pwmToProgram > currPwm:
            if (pwmToProgram - currPwm) > slope:
               currPwm = currPwm + slope
            else:
               currPwm = pwmToProgram
         elif pwmToProgram < currPwm:
            if (currPwm - pwmToProgram) > slope:
               currPwm = currPwm - slope
            else:
               currPwm = pwmToProgram
         else:
            currPwm = pwmToProgram

         if currPwm == lastPwm:
            stable = True
         else:
            numIters += 1

      header = f'{opticSpeed}G optics at {ambientTemp}C ambient:'
      if stable:
         print( f'{header} fan speed is stable at {str( currState )}' )
      else:
         currState = profile.getState( ambientTemp, max( lastPwm, currPwm ) )
         print( f'{header} fan speed is unstable, '
                f'oscillating between {lastPwm} and {currPwm}: {str( currState )}' )

class ThermalState:
   '''One ThermalState is a collection of data points for a particular ambient
   temperature.'''

   def __init__( self, rowDict ):
      self.pwm = float( rowDict[ 'AvgFanPwm' ] )
      self.rpm = float( rowDict[ 'AvgRpm' ] )
      self.maxOpticTemp = float( rowDict[ 'HottestOptic' ] )
      self.maxTh3Temp = float( rowDict[ 'HottestAsic' ] )
      self.deltaTemp = float( rowDict[ 'DeltaT' ] )
      self.totalPower = float( rowDict[ 'SystemPower' ] )
      self.cfmw = float( rowDict[ 'CFM/W' ] )

   def cloneWithDeltaTemp( self, deltaTemp ):
      '''Make a copy of this ThermalState, applying a temperature delta. In this way,
      we approximate values at other ambients.'''

      cloneDict = {
            'AvgFanPwm' : self.pwm,
            'AvgRpm' : self.rpm,
            'HottestOptic' : self.maxOpticTemp + deltaTemp,
            'HottestAsic' : self.maxTh3Temp + deltaTemp,
            'DeltaT' : self.deltaTemp,
            'SystemPower' : self.totalPower,
            'CFM/W' : self.cfmw,
      }
      return ThermalState( cloneDict )

   def __str__( self ):
      '''Useful to have a string representation for printing.'''

      return ( f'PWM: {self.pwm} RPM: {self.rpm:.2f} '
               f'Max Optic: {self.maxOpticTemp:.2f} '
               f'ASIC: {self.maxTh3Temp:.2f} Delta: {self.deltaTemp:.2f} '
               f'Power: {self.totalPower:.2f} CFM/W: {self.cfmw:.2f}' )

class ThermalProfile:
   '''A ThermalProfile is a collection of ThermalStates for the range of ambient
   temperatures that we care about. The input is one run of fan sweep data at
   the indicated ambient temperature.'''

   def __init__( self, csvFile, ambientTemp ):
      # Read the data points for the given ambient temperature.
      with open( csvFile ) as csvf:
         reader = csv.DictReader( csvf )
         sweepSteps = [ ThermalState( row ) for row in reader ]

      # Map of ambient temp to sweep data.
      self.dataPoints = OrderedDict()

      # Append ambientTemp to beginning of list if not TARGET_TEMPS
      if ambientTemp not in TARGET_TEMPS:
         TARGET_TEMPS.insert(0, ambientTemp)

      # Now take that data and project it for ambient temps in the target range.
      for temp in TARGET_TEMPS:
         if temp == ambientTemp:
            self.dataPoints[ temp ] = OrderedDict( ( s.pwm, s ) for s in sweepSteps )
         else:
            deltaTemp = temp - ambientTemp
            steps = [ s.cloneWithDeltaTemp( deltaTemp ) for s in sweepSteps ]
            self.dataPoints[ temp ] = OrderedDict( ( s.pwm, s ) for s in steps )

   def linearAttr( self, temp, attr ):
      '''Given a ThermalState attribute and an ambient temperature, get a single
      list representation of that attribute's values for every PWM.'''

      linearAttr = []
      for state in self.dataPoints[ temp ].values():
         assert hasattr( state, attr )
         linearAttr.append( getattr( state, attr ) )
      
      if attr == "maxOpticTemp":
         return sorted(linearAttr, reverse=True)
      else:
         return sorted(linearAttr)

   def interpolateState( self, temp, pwm ):
      '''Perform a linear interpolation of all data points for a new PWM, then
      create a new ThermalState for that data. This helps to fill in missing info
      as the input fan sweep won't cover all PWMs.'''

      stateDict = {
            'AvgFanPwm' : pwm,
      }
      x = self.linearAttr( temp, 'pwm' )

      for label, attr in [
            ( 'AvgRpm', 'rpm' ), ( 'HottestOptic', 'maxOpticTemp' ),
            ( 'HottestAsic', 'maxTh3Temp' ), ( 'DeltaT', 'deltaTemp' ),
            ( 'SystemPower', 'totalPower' ), ( 'CFM/W', 'cfmw' )
      ]:
         y = self.linearAttr( temp, attr )

         stateDict[ label ] = numpy.interp( pwm, x, y )

      return ThermalState( stateDict )

   def getState( self, temp, pwm ):
      '''Get data points given an ambient temperature and a fan PWM.'''

      state = self.dataPoints.get( temp, {} ).get( pwm )

      if not state:
         state = self.interpolateState( temp, pwm )
         self.dataPoints[ temp ][ pwm ] = state
      return state

def main():
   '''Given a fan_service.json config file and a CSV of thermal sweep data,
   simulate the steady-state of the algorithm for all target ambient temperatures.
   
   e.g. 
      Running a sim:
         *25C ambient
         *800G optics 
         *starting from default pwm of 30%
         *using a slope of 1 (zone slope; reference fan_service_config.thrift)
      python3 FbossThermoSim.py fan_service.json sweep.csv 25 800 30 1
   '''

   if len( sys.argv ) < 5:
      print( 'Usage: FbossThermoSim.py <fan_service.json> <sweep.csv>\n'
             '       <ambient temp for sweep.csv> <port speed for sweep.csv>'
             '       <slope>' )
      sys.exit( 1 )

   fanServiceJsonFile = sys.argv[ 1 ]
   thermoSweepCsv = sys.argv[ 2 ]
   ambientTemp = float( sys.argv[ 3 ] )
   opticSpeed = int( sys.argv[ 4 ] )
   defaultPwm = int( sys.argv[ 5 ] )
   slope = float( sys.argv[ 6 ] )

   algo = FbossFanAlgorithm( fanServiceJsonFile )
   profile = ThermalProfile( thermoSweepCsv, ambientTemp )

   for targetTemp in TARGET_TEMPS:
      algo.getSteadyState( opticSpeed, targetTemp, defaultPwm, profile, slope )

if __name__ == '__main__':
   main()