# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from collections import OrderedDict
import csv
from diagrams import Diagram, Cluster, Edge, Node as _Node
from enum import Enum
import io
import json
import re

class OpticConfig:
   def __init__( self, opticName, accessType ):
      self.opticName = opticName

      validAccessTypes = [ "QSFP", "THRIFT" ]
      assert accessType in validAccessTypes, f"Optic type throughput invalid. Please choose from {validAccessTypes}."
      self.accessType = f"ACCESS_TYPE_{accessType}"

      # Hardcoding future argument for future PID support
      aggregationType = "MAX"
      self.aggregationType = f"OPTIC_AGGREGATION_TYPE_{aggregationType}"

      self.portlist = []
      self.tempToPwmMaps = {}

   # "opticTypeThrpt" is the Gbps throughput of the opticPort (e.g. 100, 200, 400, 800 Gbps)
   def addTempToPwmMap( self, opticTypeThrpt, tempToPwm ):
      validThrpts = [ 100, 200, 400, 800 ]
      assert opticTypeThrpt in validThrpts, f"Optic type throughput invalid. Please choose from {validThrpts}."
      opticKey = f"OPTIC_TYPE_{opticTypeThrpt}_GENERIC"
      self.tempToPwmMaps[ opticKey ] = tempToPwm

   def toDict( self ):
      optic_dict = OrderedDict()
      optic_dict[ "opticName" ] = self.opticName
      optic_dict[ "access" ] = {"accessType": self.accessType}
      optic_dict[ "portList" ] = self.portlist
      optic_dict[ "aggregationType" ] = self.aggregationType
      optic_dict[ "tempToPwmMaps" ] = self.tempToPwmMaps
      return optic_dict

class ZoneConfig:
   def __init__( self, zoneName, sensorNames, fanNumbers, slope=3 ):
      self.zoneType = "ZONE_TYPE_MAX"
      self.zoneName = zoneName
      self.sensorNames = sensorNames
      # Automatically format fan numbers into the required "fan_X" strings
      self.fanNames = [ f"fan_{i}" for i in fanNumbers ]
      self.slope = slope

   def toDict( self ):
      return OrderedDict([
         ( "zoneType", self.zoneType ),
         ( "zoneName", self.zoneName ),
         ( "sensorNames", self.sensorNames ),
         ( "fanNames", self.fanNames ),
         ( "slope", self.slope ),
      ])


class FanServiceConfig:
   def __init__( self ):
      self.pwmConfig = None
      self.optics = []
      self.sensors = OrderedDict()
      self.fans = []
      self.zones = []
      self.controlInterval = None

   def setFans( self, fanSlots, allSymlinks ):
      platformFanConfigs = OrderedDict()
      for pmUnitFans in fanSlots.values():
         platformFanConfigs.update( pmUnitFans )
      inverseSymlinkLookupTable = {v: k for k, v in allSymlinks.items()}
      for slotName, slot in platformFanConfigs.items():
         fanIndex = int( slotName.split( '@' )[ 1 ] ) + 1
         presenceDetection = slot[ "presenceDetection" ][ "sysfsFileHandle" ]
         symlink = inverseSymlinkLookupTable.get( presenceDetection[ "devicePath" ] )
         if symlink:
            fanData = OrderedDict()
            fanData[ "fanName" ] = f"fan_{fanIndex}"
            fanData[ "rpmSysfsPath" ] = f"{symlink}/fan{fanIndex}_input"
            fanData[ "pwmSysfsPath" ] = f"{symlink}/pwm{fanIndex}"
            fanData[ "presenceSysfsPath" ] = f"{symlink}/{presenceDetection[ 'presenceFileName' ]}"
            fanData[ "ledSysfsPath" ] = f"/sys/class/leds/fan{fanIndex}::status/brightness"
            fanData[ "pwmMin" ] = 1
            fanData[ "pwmMax" ] = 255
            fanData[ "fanPresentVal" ] = 1
            fanData[ "fanMissingVal" ] = 0
            fanData[ "fanGoodLedVal" ] = 1
            fanData[ "fanFailLedVal" ] = 2
            self.fans.append( fanData )


   def addOpticConfig( self, opticName, accessType ):
      opticConfig = OpticConfig( opticName, accessType )
      self.optics.append( opticConfig )
      return opticConfig

   def addSensor( self, sensorName, accessType, tempToPwmMap ):
      sensor = OrderedDict()
      sensor["sensorName"] = sensorName

      validAccessTypes = [ "QSFP", "THRIFT" ]
      assert accessType in validAccessTypes, f"Optic type throughput invalid. Please choose from {validAccessTypes}."
      sensor[ "access" ] = {"accessType": f"ACCESS_TYPE_{accessType}"}

      sensor[ "pwmCalcType" ] = "SENSOR_PWM_CALC_TYPE_FOUR_LINEAR_TABLE"
      sensor[ "normalUpTable" ] = tempToPwmMap
      sensor[ "normalDownTable" ] = tempToPwmMap
      sensor[ "failUpTable" ] = tempToPwmMap
      sensor[ "failDownTable" ] = tempToPwmMap
      self.sensors[ sensorName ] = ( sensor )
      return sensor

   def addZone( self, zoneName, sensorNames, fanNumbers, slope=3 ):
      zone = ZoneConfig( zoneName, sensorNames, fanNumbers, slope )
      self.zones.append( zone )

   def setControlInterval( self, sensorReadInterval, pwmUpdateInterval ):
      self.controlInterval = {
         "sensorReadInterval": sensorReadInterval,
         "pwmUpdateInterval": pwmUpdateInterval
      }

   def setPwmConfig( self, pwmBoostOnNumDeadFan,
                     pwmBoostOnNumDeadSensor,
                     pwmBoostOnNoQsfpAfterInSec,
                     pwmBoostValue,
                     pwmTransitionValue,
                     pwmLowerThreshold,
                     pwmUpperThreshold ):
      args = [
         pwmBoostOnNumDeadFan, pwmBoostOnNumDeadSensor, pwmBoostOnNoQsfpAfterInSec,
         pwmBoostValue, pwmTransitionValue, pwmLowerThreshold, pwmUpperThreshold,
      ]
      assert all( arg is not None for arg in args ), "All fan PWM config arguments must be provided."
      self.pwmConfig = {
         "pwmBoostOnNumDeadFan": pwmBoostOnNumDeadFan,
         "pwmBoostOnNumDeadSensor": pwmBoostOnNumDeadSensor,
         "pwmBoostOnNoQsfpAfterInSec": pwmBoostOnNoQsfpAfterInSec,
         "pwmBoostValue": pwmBoostValue,
         "pwmTransitionValue": pwmTransitionValue,
         "pwmLowerThreshold": pwmLowerThreshold,
         "pwmUpperThreshold": pwmUpperThreshold,
      }

   def resolveSensorNames( self, sensors ):
      platformSensorNames = OrderedDict()
      for pmUnitSensors in sensors.values():
         platformSensorNames.update( pmUnitSensors )
      for sensor in self.sensors.values():
         suffix = sensor[ "sensorName" ]
         assert suffix in platformSensorNames, f"'{suffix}' is not a valid sensor name in {platformSensorNames}."
         sensor[ "sensorName" ] = platformSensorNames[ suffix ]
      return list( self.sensors.values() )
   
   def getResolvedZoneConfigs( self ):
      resolved_zones_list = []
      for zone in self.zones:
         resolved_sensor_names = []
         # Get the list of user-inputted names for this zone
         for name in zone.sensorNames:
               # Check if the name is a key in the sensors dictionary
               if name in self.sensors:
                  # If yes, extract the final resolved name
                  resolved_sensor_names.append( self.sensors[ name ][ 'sensorName' ] )
               # Else, check if it's a known optic name
               elif any( optic.opticName == name for optic in self.optics ):
                  resolved_sensor_names.append( name )
               else:
                  raise ValueError( f"Zone name '{name}' not found in configured sensors or optics." )

         # Create the final zone dictionary with the resolved names
         zone_dict = zone.toDict()
         zone_dict[ 'sensorNames' ] = resolved_sensor_names
         resolved_zones_list.append( zone_dict )
      
      return resolved_zones_list