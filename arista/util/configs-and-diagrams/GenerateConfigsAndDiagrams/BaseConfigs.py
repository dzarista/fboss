# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from collections import OrderedDict
import csv
from diagrams import Diagram, Cluster, Edge, Node as _Node
from enum import Enum
import io
import json
import re

BSP_MAPPING_KEYS = [
   "TcvrId",
   "TcvrLaneIdList",
   "PimId",
   "AccessControllerId",
   "AccessControlType",
   "ResetPath",
   "ResetMask",
   "ResetHoldHi",
   "PresentPath",
   "PresentMask",
   "PresentHoldHi",
   "IoControllerId",
   "IoControlType",
   "IoPath",
   "LedId",
   "LedBluePath",
   "LedYellowPath",
]

def reformatOneElementLists( jsonDump ):
   pattern = re.compile( r'\[\s*(-?\d+)\s*\]' )
   output_string = pattern.sub( r'[\1]', jsonDump )
   return output_string


def constructHelper( currDevice, currPath, outputList ):
   '''Return full device path from the root PM unit

   This helper accepts the device/bus object as a parameter and explores all slot
   type configs that match with the device's PM unit. By doing this recursively, it
   eventually reaches the root PM unit, building up the device path along the way.
   This functionality is utilized during symbolic link to device path generation.
   '''
   while not isinstance( currDevice, PmUnitConfig ):
      currDevice = currDevice.parentConfig
   platformConfig = currDevice.parentConfig
   if currDevice.pmUnitName == platformConfig.rootPmUnitName:
      outputList.append( currPath if currPath else "/" )
      return
   for pmUnit in platformConfig.pmUnitConfigs:
      for slotConfig in pmUnit.outgoingSlotConfigs:
         if slotConfig.slotType == f"{ currDevice.pmUnitName }_SLOT":
            constructHelper(
               slotConfig,
               f"/{ slotConfig.slotName }{ currPath }",
               outputList
            )


def constructBusPaths( bus ):
   startPath = f"/[{ bus.busName }]"
   outputList = []
   constructHelper( bus, startPath, outputList )
   return outputList


def constructDevicePaths( device ):
   startPath = f"/[{ device.pmUnitScopedName }]"
   outputList = []
   constructHelper( device, startPath, outputList )
   return outputList

def constructSlotPaths( pmUnit ):
   outputList = []
   constructHelper( pmUnit, "", outputList )
   return outputList

def filterByPrefix( data, prefix ):
   return [ item for item in data if item.get( 'name', '' ).startswith( prefix ) ]

class Node:
   def __init__( self, name, shape="record", fillcolor="#5f97e4", **kwargs ):
      node_attributes = {
        "label": name,
        "labelloc": "c",
        "shape": shape,
        "width": "5",
        "height": "1.6",
        "fixedsize": "true",
        "style": "filled",
        'fontsize': '16',
        "fillcolor": fillcolor,
        "fontcolor": "white",
      }
      node_attributes.update( kwargs )
      self.node = _Node( **node_attributes )

   def getNode(self):
      return self.node


class PlatformConfig:
   def __init__( self, platformName, rootPmUnitName="SCM" ):
      self.platformName = platformName
      self.rootPmUnitName = rootPmUnitName
      self.rootPmUnitPointer = None
      self.pmUnitConfigs = []
      self.i2cAdaptersFromCpu = []
      self.setChassisEepromDevicePath = True
      self.kmodsSettings = {
         "bspKmodsRpmName": "arista_bsp_kmods",
         "bspKmodsRpmVersion": "0.7.9-1",
         "requiredKmodsToLoad": [],
      }

   def getPmUnit( self, pmUnitName ):
      for pmUnit in self.pmUnitConfigs:
         if pmUnit.pmUnitName == pmUnitName:
            return pmUnit
      return None

   def getSlotTypeConfigsDict( self ):
      jsonDict = {}
      for pmConfig in self.pmUnitConfigs:
         jsonDict[
            pmConfig.slotTypeConfig.slotName
         ] = pmConfig.slotTypeConfig.asJson()
      return jsonDict

   def getFruEepromList( self ):
      jsonDict = {}
      for pmConfig in self.pmUnitConfigs:
         slotTypeConfig = pmConfig.slotTypeConfig
         idprom_config = slotTypeConfig.parseIdpromConfig()
         # Call the eeprom config get symlink
         path = slotTypeConfig.getEepromConfig()
         if path:
            offset = idprom_config.get( 'offset', 0 )
            jsonDict[ pmConfig.pmUnitName ] = OrderedDict( [
                  ("path", path),
                  ("offset", offset)
            ] )
      return jsonDict


   def addPmUnitConfigs( self, newConfigs ):
      for config in newConfigs:
         config.addParentConfigPointer( self )
         if config.pmUnitName == self.rootPmUnitName:
            self.rootPmUnitPointer = config
      self.pmUnitConfigs.extend( newConfigs )

   def getPmUnitConfigsDict( self ):
      jsonDict = {}
      for config in self.pmUnitConfigs:
         name = config.pmUnitName
         jsonDict[ name ] = config.asJson()
      return jsonDict

   def parseSymbolicLinkToDevicePaths( self ):
      symlinkDict = {}
      for config in self.pmUnitConfigs:
         pmUnitDict = config.symlinkToDevicePaths
         for symlink, devicePath in pmUnitDict.items():
            symlinkDict[ symlink ] = devicePath
      return symlinkDict

   def getChassisEepromDevicePath( self ):
      scmPmUnit = self.getPmUnit( "SCM" )
      if scmPmUnit:
         for slotConfig in scmPmUnit.outgoingSlotConfigs:
            if slotConfig.slotType == "SMB_SLOT":
               return f"/{ slotConfig.slotName }/[IDPROM]"
      return "/[CHASSIS_EEPROM]"

   def addI2cAdaptersFromCpu( self, newConfigs ):
      self.i2cAdaptersFromCpu.extend( newConfigs )

   def addKmodsSettings( self, newConfigDict ):
      self.kmodsSettings.update( newConfigDict )

   def sensorServiceJson( self ):
      pmUnitSensorsList = []
      for pmConfig in self.pmUnitConfigs:
         sensorServiceDictList = pmConfig.getSensorServiceDictList()
         if sensorServiceDictList:
            pmUnitSensorsList.extend( sensorServiceDictList )
      sensorConfigDict = { 'pmUnitSensorsList': pmUnitSensorsList }
      output = json.dumps( sensorConfigDict, indent=2 )
      return output

   def pmConfigJson( self ):
      jsonDict = OrderedDict()
      jsonDict[ "platformName" ] = self.platformName
      jsonDict[ "rootPmUnitName" ] = self.rootPmUnitName
      jsonDict[ "rootSlotType" ] = f"{ self.rootPmUnitName }_SLOT"
      jsonDict[ "slotTypeConfigs" ] = self.getSlotTypeConfigsDict()
      jsonDict[ "pmUnitConfigs" ] = self.getPmUnitConfigsDict()
      jsonDict[ "i2cAdaptersFromCpu" ] = self.i2cAdaptersFromCpu
      jsonDict[ "symbolicLinkToDevicePath" ] = (
         self.parseSymbolicLinkToDevicePaths()
      )
      if self.setChassisEepromDevicePath:
         jsonDict[ "chassisEepromDevicePath"] = self.getChassisEepromDevicePath()
      jsonDict[ "bspKmodsRpmName" ] = self.kmodsSettings[ "bspKmodsRpmName" ]
      jsonDict[ "bspKmodsRpmVersion" ] = self.kmodsSettings[ "bspKmodsRpmVersion" ]
      jsonDict[ "requiredKmodsToLoad" ] = self.kmodsSettings[ "requiredKmodsToLoad" ]

      jsonDump = json.dumps( jsonDict, indent=2 )
      output = reformatOneElementLists( jsonDump )
      return output

   def weutilJson( self ):
      weutil_data = OrderedDict()
      weutil_data[ "chassisEepromName" ] = "SMB"
      weutil_data[ "fruEepromList" ] = self.getFruEepromList()
      output_json_dump = json.dumps( weutil_data, indent=2 )
      return output_json_dump

   def bspMappingCsv( self ):
      output = io.StringIO()
      writer = csv.DictWriter( output,
                               fieldnames=BSP_MAPPING_KEYS,
                               lineterminator='\n' )
      writer.writeheader()

      xcvrList = []
      for pmConfig in self.pmUnitConfigs:
         for pciConfig in pmConfig.pciDeviceConfigs:
            xcvrList.extend( pciConfig.xcvrCtrlConfigs )

      xcvrListSorted = sorted( xcvrList, key=lambda xcvr: xcvr.portNumber )

      for rec in xcvrListSorted:
         rows = rec.createBspRow()
         for row in rows:
            writer.writerow( {k: row.get(k, "") for k in BSP_MAPPING_KEYS} )

      return output.getvalue()

   def genDiagram( self ):
      graph_attr = {
         "ratio": "0.5625",
         'rankdir': 'LR',
         'show': 'False',
         'fontsize': '48'
      }
      with Diagram( f"Platform: { self.platformName }", show=False,
                    graph_attr = graph_attr ):
         self.rootPmUnitPointer.render()


class SlotTypeConfig:
   def __init__( self, pmUnitName ):
      self.slotName = f"{ pmUnitName }_SLOT"
      self.numOutgoingI2cBuses = 0
      self.idPromConfigBusName = None
      self.idPromConfigAddress = None
      self.idPromConfigKernelDeviceName = None
      self.idPromConfigOffset = None
      self.pmUnitName = pmUnitName
      self.parentConfig = None

   def getEepromConfig( self ):
      if not self.idPromConfigBusName:
         return None
      platformName = self.parentConfig.parentConfig.platformName
      # Special case: SCM for the 3 platforms has special handling for the symlink
      if self.pmUnitName == 'SCM' and platformName in ( "meru800bia", "meru800bfa", "glath05a-64o" ):
         return "/run/devmap/eeproms/MERU_SCM_EEPROM"
      else:
         return f"/run/devmap/eeproms/{platformName.upper()}_{self.pmUnitName}_EEPROM"

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

   def asJson( self ):
      idpCfg = self.parseIdpromConfig()
      assert self.numOutgoingI2cBuses is not None, (
         "numOutgoingI2cBuses is required"
      )

      return {
         "numOutgoingI2cBuses": self.numOutgoingI2cBuses,
         **({ "idpromConfig": idpCfg } if idpCfg and 
            all( value is not None for value in idpCfg.values() ) else {}),
         "pmUnitName": self.pmUnitName
      }

   def parseIdpromConfig( self ):
      args = [
         self.idPromConfigBusName,
         self.idPromConfigAddress,
         self.idPromConfigKernelDeviceName,
         self.idPromConfigOffset,
      ]

      assert all(arg is not None for arg in args) or not any(args), \
         "Invalid SlotType IDPROM: all idprom configs must be defined, or none at all."

      return {
         "busName": self.idPromConfigBusName,
         "address": self.idPromConfigAddress.lower() if self.idPromConfigAddress else None,
         "kernelDeviceName": self.idPromConfigKernelDeviceName,
         "offset": self.idPromConfigOffset
      }


class PmUnitConfig:
   def __init__( self, pmUnitName, prefixSymlink=None ):
      self.pmUnitName = pmUnitName
      self.slotTypeConfig = SlotTypeConfig( self.pmUnitName )
      self.i2cDeviceConfigs = []
      self.outgoingSlotConfigs = []
      self.pciDeviceConfigs = []
      self.embeddedSensorConfigs = []
      self.symlinkToDevicePaths = {}
      self.prefixSymlink = prefixSymlink
      self.parentConfig = None

   def setSlotTypeConfig( self, numOutgoingI2cBuses=0, idPromConfigBusName=None,
                          idPromConfigAddress=None,
                          idPromConfigKernelDeviceName=None,
                          idPromConfigOffset=None,
                          idPromDevice=None ):
      self.slotTypeConfig.numOutgoingI2cBuses = numOutgoingI2cBuses
      self.slotTypeConfig.idPromConfigBusName = idPromConfigBusName
      self.slotTypeConfig.idPromConfigAddress = idPromConfigAddress
      self.slotTypeConfig.idPromConfigKernelDeviceName = idPromConfigKernelDeviceName
      self.slotTypeConfig.idPromConfigOffset = idPromConfigOffset
      self.slotTypeConfig.idPromDevice = idPromDevice
      self.slotTypeConfig.addParentConfigPointer( self )

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

   def addI2cDeviceConfigs( self, newConfigs ):
      for config in newConfigs:
         config.addParentConfigPointer( self )
      self.i2cDeviceConfigs.extend( newConfigs )

   def addOutgoingSlotConfigs( self, newConfigs ):
      for config in newConfigs:
         config.addParentConfigPointer( self )
      self.outgoingSlotConfigs.extend( newConfigs )

   def addPciDeviceConfigs( self, newConfigs ):
      for config in newConfigs:
         config.addParentConfigPointer( self )
      self.pciDeviceConfigs.extend( newConfigs )

   def addEmbeddedSensorConfigs( self, newConfigs ):
      for config in newConfigs:
         config.addParentConfigPointer( self )
      self.embeddedSensorConfigs.extend( newConfigs )

   def populateSymlinkToDevicePaths( self ):
      addedPaths = {
         **self.generateFpgaSymlinks(),
         **self.generateI2cBusSymlinks(),
         **self.generateSMBIdPromSymlinks(),
         **self.generateI2cDeviceSymlinks(),
         **self.generateEmbeddedSensorSymlinks(),
         **self.generateXcvrSymlinks(),
         **self.generateSpiDeviceSymlinks(),
         **self.generateXcvrCtrlSymlinks()
      }
      self.symlinkToDevicePaths.update( addedPaths )

   def generateI2cBusSymlinks( self ):
      symlinkDict = OrderedDict()
      busConfigs = [ bus for pciConfig in self.pciDeviceConfigs
                     for i2cConfig in pciConfig.i2cAdapterConfigs
                     for bus in i2cConfig.buses ]
      for bus in busConfigs:
         symlinkDict.update( bus.generateSymlinkDevicePath() )
      return symlinkDict

   def generateI2cDeviceSymlinks( self ):
      symlinkDict = OrderedDict()
      for i2cConfig in self.i2cDeviceConfigs:
         symlinkDict.update( i2cConfig.generateSymlinkDevicePath() )
      return symlinkDict

   def generateEmbeddedSensorSymlinks( self ):
      symlinkDict = OrderedDict()
      for sensorConfig in self.embeddedSensorConfigs:
         symlinkDict.update( sensorConfig.generateSymlinkDevicePath() )
      return symlinkDict

   def generateXcvrSymlinks( self ):
      symlinkDict = {}
      for pciConfig in self.pciDeviceConfigs:
         for xcvrConfig in pciConfig.xcvrCtrlConfigs:
            symlinkDict[ xcvrConfig.symlink ] = (
               constructDevicePaths( xcvrConfig )[ 0 ]
            )
      symlinkDict = OrderedDict(
         sorted(
            symlinkDict.items(),
            key=lambda x: int( re.search( r'\d+', x[ 0 ] ).group() )
         )
      )
      return symlinkDict

   def generateXcvrCtrlSymlinks( self ):
      symlinkDict = {}
      for pciConfig in self.pciDeviceConfigs:
         for xcvrConfig in pciConfig.xcvrCtrlConfigs:
            outputList = []
            constructHelper( xcvrConfig,
                             f"/[{xcvrConfig.i2cPath}]",
                             outputList )
            symlinkDict[ xcvrConfig.ioSymlink ] = ( outputList[ 0 ] )
            symlinkDict[ xcvrConfig.ctrlSymlink ] = (
               constructDevicePaths( xcvrConfig )[ 0 ]
            )
         symlinkDict = OrderedDict(
         sorted(
            symlinkDict.items(),
            key=lambda x: int( re.search( r'\d+', x[ 0 ] ).group() )
         )
      )
      return symlinkDict

   def generateFpgaSymlinks( self ):
      symlinkDict = OrderedDict()
      for pciConfig in self.pciDeviceConfigs:
         symlinkDict.update( pciConfig.generateSymlinkDevicePath() )
      return symlinkDict

   def generateSMBIdPromSymlinks( self ):
      platform = self.parentConfig.platformName
      symlinkDict = OrderedDict()
      if self.pmUnitName == "SCM":
         for slotConfig in self.outgoingSlotConfigs:
            if slotConfig.slotType == "SMB_SLOT":
               # Add unit test support for SMB EEPROM PM config generation bb/1015713
               smbPmUnit = self.parentConfig.getPmUnit( "SMB" )
               symlinkDeviceName = smbPmUnit.prefixSymlink or platform.upper()
               symlinkDict[
                  f"/run/devmap/eeproms/{ symlinkDeviceName }_SMB_EEPROM"
               ] = f"/{ slotConfig.slotName }/[IDPROM]"
      return symlinkDict

   def generateSpiDeviceSymlinks( self ):
      symlinkDict = OrderedDict()
      spiMasterConfigs = [ config for pciConfig in self.pciDeviceConfigs
                           for config in pciConfig.spiMasterConfigs ]
      for spiMasterConfig in spiMasterConfigs:
         for config in spiMasterConfig.spiDeviceConfigs:
            symlinkDict.update( config.generateSymlinkDevicePath() )
      return symlinkDict

   def asJson( self ):
      name = self.pmUnitName
      pluggedInSlotType = f'{ name }_SLOT'

      assert name and pluggedInSlotType, "name and pluggedInSlotType are required"

      embeddedSensorConfigs = self.getEmbeddedSensorConfigsList()

      return {
         "pluggedInSlotType": pluggedInSlotType,
         "i2cDeviceConfigs": self.getI2cDeviceConfigsList(),
         "outgoingSlotConfigs": self.getOutgoingSlotConfigsDict(),
         "pciDeviceConfigs": self.getPciDeviceConfigsList(),
         **( { "embeddedSensorConfigs":
            embeddedSensorConfigs } if len( embeddedSensorConfigs ) > 0 else {} )
      }

   def getEmbeddedSensorConfigsList( self ):
      return [ config.asJson() for config in self.embeddedSensorConfigs ]

   def getI2cDeviceConfigsList( self ):
      return [ config.asJson() for config in self.i2cDeviceConfigs ]

   def getOutgoingSlotConfigsDict( self ):
      jsonDict = {}
      for config in self.outgoingSlotConfigs:
         slotName = config.slotName
         jsonDict[ slotName ] = config.asJson()
      return jsonDict

   def getPciDeviceConfigsList( self ):
      return [ config.asJson() for config in self.pciDeviceConfigs ]

   def getSensorServiceDictList( self ):
      sensorsList = []
      for embeddedDevice in self.embeddedSensorConfigs:
         configDict = embeddedDevice.getSensorConfigsList()
         for sensorConfigItem in configDict:
            sensorsList.append( sensorConfigItem )
      for i2cDevice in self.i2cDeviceConfigs:
         configDict = i2cDevice.getSensorConfigsList()
         for sensorConfigItem in configDict:
            sensorsList.append( sensorConfigItem )

      if sensorsList:
         sensorServiceDictList = []
         slotPaths = constructSlotPaths( self )
         assert slotPaths, f"Failed to generate slot path for {self.pmUnitName}"

         for slotPath in slotPaths:
            sensorServiceDict = OrderedDict()
            sensorServiceDict.update( {"slotPath": slotPath} )
            sensorServiceDict.update( {"pmUnitName": self.pmUnitName} )

            if len( slotPaths ) > 1 and '@' in slotPath:
               slotIdx = int( slotPath.split( '@' )[ -1 ] )
               sensorsList2 = filterByPrefix( sensorsList, f'PSU{slotIdx + 1}' )
               sensorServiceDict.update( {"sensors": sensorsList2} )
            else:
               sensorServiceDict.update( {"sensors": sensorsList} )   
            
            sensorServiceDictList.append( sensorServiceDict )
         return sensorServiceDictList

   def renderCluster( self, incomingSlot ):
      # NOTE: FANs are handled as a special case since they don't contain any
      # incoming/outgoing buses
      isRoot = self.parentConfig.rootPmUnitName == self.pmUnitName
      pmUnitIndex = (
         f" { int( incomingSlot.slotName.split( '@' )[ 1 ] ) + 1 }"
         if incomingSlot and incomingSlot.slotType in ( "FAN_SLOT", "PSU_SLOT" )
         else ""
      )

      # SMB_IDPROM is a special case that has to be manually added just for the
      # purpose of diagram generation
      if self.pmUnitName == "SMB" and self.slotTypeConfig.idPromConfigBusName:
         smbIdProm = I2cDeviceConfig(
            self.slotTypeConfig.idPromConfigAddress,
            self.slotTypeConfig.idPromConfigKernelDeviceName,
            "SMB_IDPROM",
            incomingBusIndex=int( self.slotTypeConfig.idPromConfigBusName[ -1 ] )
         )
         self.addI2cDeviceConfigs( [ smbIdProm ] )

      with Cluster(
         f"PmUnit - { self.pmUnitName }{ pmUnitIndex } {'(Root)' if isRoot else ''}",
         graph_attr={ "rankdir":"TB", 'fontsize':'30', "margin": "20" }
      ):

         if isRoot:
            with Cluster( "CPU", graph_attr={ 'fontsize':'24' } ):
               for config in self.embeddedSensorConfigs:
                  Node( config.pmUnitScopedName ).getNode()

         for slot in self.outgoingSlotConfigs:
            slot.renderNode()

         with Cluster( "I2C devices", graph_attr={ 'fontsize':'24' } ):
            for i2cDev in self.i2cDeviceConfigs:
               i2cDev.renderNode()
               # This handles the FAN_CPLD to Fans relationship
               if isinstance( i2cDev, FANCpld ):
                  for slot in self.outgoingSlotConfigs:
                     if ( slot.slotType == "FAN_SLOT"
                          and i2cDev.pmUnitScopedName in slot.presenceDevicePath ):
                        attrs = {}
                        i2cDev.node - Edge( style="dashed", **attrs ) - slot.node

         for pciDev in self.pciDeviceConfigs:
            pciDev.renderNode()
            for i2cDev in self.i2cDeviceConfigs:
               thisBus = i2cDev.busName.split( "@" )[ 0 ]
               pciAdapterNames = [ adapter.pmUnitScopedName
                                   for adapter in pciDev.i2cAdapterConfigs ]
               if thisBus in pciAdapterNames:
                  attrs = {
                     "minlen":"2",
                     "headlabel":i2cDev.busName,
                     'fontsize':'16'
                  }
                  pciDev.node >> Edge( **attrs ) >> i2cDev.node

            if pciDev.xcvrCtrlConfigs:
               xcvrNode = Node( "XCVRs" ).getNode()
               attrs = {
                  "minlen":"0",
               }
               pciDev.node >> Edge( **attrs ) >> xcvrNode

         for slot in self.outgoingSlotConfigs:
            for bus in slot.outgoingI2cBuses:
               pciDev = bus.parentConfig.parentConfig
               attrs = {
                  "minlen":"3",
               }
               pciDev.node - Edge( **attrs ) - slot.node

         if incomingSlot:
            for i2cDev in self.i2cDeviceConfigs:
               if i2cDev.busName.split( "@" )[ 0 ] == "INCOMING":
                  attrs = {
                     "minlen": "3",
                     "headlabel":i2cDev.busName,
                     "fontsize":"16",
                     "labeldistance":"6.0"
                  }
                  incomingSlot.node >> Edge( **attrs ) >> i2cDev.node

            if self.pmUnitName == "FAN" and len( self.i2cDeviceConfigs ) == 0:
               attrs = {
                  "minlen": "3",
               }
               incomingSlot.node - Edge(
                  style="dashed", **attrs
               ) >> Node( "FAN" ).getNode()

   def render( self, incomingSlot=None ):
      self.renderCluster( incomingSlot )

      for slotConfig in self.outgoingSlotConfigs:
         for pmConfig in self.parentConfig.pmUnitConfigs:
            if slotConfig.slotType == f"{ pmConfig.pmUnitName }_SLOT":
               pmConfig.render( slotConfig )


class EmbeddedSensorConfig:
   def __init__( self, pmUnitScopedName, sysfsPath ):
      self.pmUnitScopedName = pmUnitScopedName
      self.sysfsPath = sysfsPath
      self.parentConfig = None
      self.sensorConfigs = []
      self.symlinkPath = f"/run/devmap/sensors/{ self.pmUnitScopedName }"

   def asJson( self ):
      assert self.pmUnitScopedName and self.sysfsPath, (
         "missing details in EmbeddedSensorsConfig"
      )

      return {
         "pmUnitScopedName": self.pmUnitScopedName,
         "sysfsPath": self.sysfsPath
      }

   def generateSymlinkDevicePath( self ):
      return { self.symlinkPath: constructDevicePaths( self )[ 0 ] }

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

   def getSensorConfigsList( self ):
      sensorsList = []
      devicePaths = constructDevicePaths( self )
      pmUnitName = self.parentConfig.pmUnitName
      if len( devicePaths ) == 1:
         for config in self.sensorConfigs:
            sensorsList.append( config.toDict() )
      else:
         for i in range( len( devicePaths ) ):
            pmUnit = f"{ pmUnitName }{ i+1 }"
            for config in self.sensorConfigs:
               sensorsList.append( config.toDict( i+1 ) )
      return sensorsList

   def addSensorConfigs( self, newConfigs ):
      for config in newConfigs:
         config.addParentConfigPointer( self )
      self.sensorConfigs.extend( newConfigs )


class I2cDeviceConfig:
   def __init__( self, address, kernelDeviceName, pmUnitScopedName,
                 incomingBusIndex=None, isGpioChip=False, hasBmcMac=False,
                 hasCpuMac=False, hasSwitchAsicMac=False, hasReservedMac=False,
                 numOutgoingChannels=None, initRegSettings=None ):

      if incomingBusIndex is not None:
         self.busName = f"INCOMING@{ incomingBusIndex }"
      self.address = address
      self.kernelDeviceName = kernelDeviceName
      self.pmUnitScopedName = pmUnitScopedName
      self.isGpioChip = isGpioChip
      self.hasBmcMac = hasBmcMac
      self.hasCpuMac = hasCpuMac
      self.hasSwitchAsicMac = hasSwitchAsicMac
      self.hasReservedMac = hasReservedMac
      self.numOutgoingChannels = numOutgoingChannels
      self.initRegSettings = initRegSettings
      self.parentConfig = None
      self.symlinkPath = None
      self.sensorConfigs = []
      self.node = None

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

   def addBusName( self, busName ):
      self.busName = busName

   def generateSymlinkDevicePath( self ):
      return ( { self.symlinkPath: constructDevicePaths( self )[ 0 ] }
         if self.symlinkPath else {} )

   def addSensorConfigs( self, newConfigs ):
      for config in newConfigs:
         config.addParentConfigPointer( self )
      self.sensorConfigs.extend( newConfigs )

   def getSensorConfigsList( self ):
      sensorsList = []
      devicePaths = constructDevicePaths( self )
      pmUnitName = self.parentConfig.pmUnitName
      if len( devicePaths ) == 1:
         for config in self.sensorConfigs:
            sensorsList.append( config.toDict() )
      else:
         for i in range( len( devicePaths ) ):
            pmUnit = f"{ pmUnitName }{ i+1 }"
            for config in self.sensorConfigs:
               thisConfig = config.toDict( i+1 )
               thisConfig['name'] = f"{ pmUnitName }{ i+1 }_{ config.name }" 
               sensorsList.append( thisConfig )
      return sensorsList

   def asJson( self ):
      busName = self.busName
      address = self.address
      kernelDeviceName = self.kernelDeviceName
      pmUnitScopedName = self.pmUnitScopedName
      numOutgoingChannels = self.numOutgoingChannels
      hasBmcMac = self.hasBmcMac
      hasCpuMac = self.hasCpuMac
      hasSwitchAsicMac = self.hasSwitchAsicMac
      hasReservedMac = self.hasReservedMac
      isGpioChip = self.isGpioChip
      initRegSettings = self.initRegSettings

      assert busName and address and kernelDeviceName and pmUnitScopedName, (
         "missing required details in I2cDeviceConfigs"
      )

      return {
         "busName": busName,
         "address": address.lower(),
         "kernelDeviceName": kernelDeviceName,
         "pmUnitScopedName": pmUnitScopedName,
         **({ "numOutgoingChannels": numOutgoingChannels }
            if numOutgoingChannels else {}),
         **({ "hasBmcMac": bool( hasBmcMac ) } if hasBmcMac else {}),
         **({ "hasCpuMac": bool( hasCpuMac ) } if hasCpuMac else {}),
         **({ "hasSwitchAsicMac": hasSwitchAsicMac } if hasSwitchAsicMac else {}),
         **({ "hasReservedMac": hasReservedMac } if hasReservedMac else {}),
         **({ "isGpioChip": isGpioChip } if isGpioChip else {}),
         **({ "initRegSettings": initRegSettings.list }
            if initRegSettings and initRegSettings.list else {})
      }

   def renderNode( self ):
      self.node = Node( f"{{ { self.address } | { self.pmUnitScopedName } }}",
                        shape="Mrecord" ).getNode()


class GpioChip( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      super().__init__( *args, **kwargs )
      self.isGpioChip = True
      self.symlinkPath = f"/run/devmap/gpiochips/{ self.pmUnitScopedName }"


class Sensor( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      super().__init__( *args, **kwargs )
      self.symlinkPath = f"/run/devmap/sensors/{ self.pmUnitScopedName }"


class FairywrenSensor( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      super().__init__( *args, **kwargs )
      self.symlinkPath = (
         f"/run/devmap/sensors/CPU_{ self.pmUnitScopedName.split( '_', 1 )[ 1 ] }"
      )


class SMBCpld( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      super().__init__( *args, **kwargs )
      self.symlinkPath = "/run/devmap/cplds/{}_SMB_CPLD"

   def generateSymlinkDevicePath( self ):
      platform = self.parentConfig.parentConfig.platformName
      return {
         self.symlinkPath.format( platform.upper() ):
            constructDevicePaths( self )[ 0 ]
      }


class FANCpld( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      super().__init__( *args, **kwargs )
      match = re.search( r'FAN(\d+)', self.pmUnitScopedName )
      self.symlinkPath = (
         f"/run/devmap/sensors/FAN_CPLD{ match.group( 1 ) }" if match
         else f"/run/devmap/sensors/{ self.pmUnitScopedName }"
      )

   def generateSymlinkDevicePath( self ):
      devicePath = constructDevicePaths( self )[ 0 ]
      return {
         f"/run/devmap/cplds/{ self.pmUnitScopedName }": devicePath,
         self.symlinkPath: devicePath
      }

   def getSensorConfigsList( self ):
      sensorsList = []
      match = re.search( r'FAN(\d+)', self.pmUnitScopedName )
      baseFanIndex = 4 * int( match.group( 1 ) ) if match else 0
      for i, config in enumerate( self.sensorConfigs ):
         thisConfig = config.toDict( i )
         thisConfig['name'] = f"FAN{ baseFanIndex+i+1 }_{ config.name }"
         sensorsList.append( thisConfig )
      return sensorsList

   def addFANRpms( self, numConfigs, upperCriticalVal, lowerCriticalVal ):
      newConfigs = []
      for i in range( numConfigs ):
         newConfigs.append(
            SensorConfig( "RPM", f"fan{ i+1 }_input", SensorType.FAN_SPEED,
                          thresholds=Thresholds(
                              upperCriticalVal=upperCriticalVal,
                              lowerCriticalVal=lowerCriticalVal
                          ) )
         )
      self.addSensorConfigs( newConfigs )


class I2cIdProm( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      super().__init__( *args, **kwargs )
      self.symlinkPath = f"/run/devmap/eeproms/{ self.pmUnitScopedName }"


class FairywrenIdProm( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      super().__init__( *args, **kwargs )
      self.symlinkPath = "/run/devmap/eeproms/MERU_SCM_EEPROM_P1"


class PSUBus( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      self.singlePSU = kwargs.pop( 'singlePSU', False )
      super().__init__( *args, **kwargs )
      if self.singlePSU:
         self.symlinkPath = "/run/devmap/sensors/PSU_PMBUS"
      else:
         self.symlinkPath = "/run/devmap/sensors/PSU{}_PMBUS"

   def generateSymlinkDevicePath(self ):
      symlinkDict = OrderedDict()
      devicePaths = constructDevicePaths( self )
      if self.singlePSU:
         symlinkDict[ self.symlinkPath ] = devicePaths[ 0 ]
      else:
         for path in devicePaths:
            match = re.search( r'PSU_SLOT@(\d+)', path )
            portNum = int( match.group( 1 ) ) + 1
            symlinkDict[ self.symlinkPath.format( portNum ) ] = path
      return symlinkDict


class InitRegSettings:
   def __init__( self, offsetBufPairs ):
      self.list = []
      for regOffset, ioBuf in offsetBufPairs:
         self.list.append( { "regOffset": regOffset, "ioBuf": [ ioBuf ] } )


class SlotConfig:
   def __init__( self, slotName, presenceFileName=None, presenceDevicePath=None,
                 outgoingI2cBuses=None ):
      self.slotName = slotName
      self.slotType = slotName.split( "@" )[ 0 ]
      self.presenceFileName = presenceFileName
      self.presenceDevicePath = presenceDevicePath
      self.outgoingI2cBuses = outgoingI2cBuses or []
      self.parentConfig = None
      self.node = None

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

   def asJson( self ):
      slotType = self.slotType
      presenceDevicePath = self.presenceDevicePath
      presenceFileName = self.presenceFileName
      outgoingI2cBusNames = [ bus.busName for bus in self.outgoingI2cBuses ]

      assert slotType, "missing slotType in OutgoingSlotConfigs"

      presenceDetection = None
      if presenceFileName and presenceDevicePath:
         presenceDetection = {
            "sysfsFileHandle": {
               "devicePath": presenceDevicePath,
               "presenceFileName": presenceFileName,
               "desiredValue": 1
            }
         }

      return {
         "slotType": slotType,
         **({ "presenceDetection":  presenceDetection }\
             if presenceDetection else {}),
         "outgoingI2cBusNames": outgoingI2cBusNames \
              if outgoingI2cBusNames else []
      }

   def renderNode( self ):
      buses=""
      for bus in self.outgoingI2cBuses:
         buses += f"{ bus.busName }|"
      buses = buses[ :-1 ]

      if buses:
         label = f" { self.slotName } | {{ {{ { buses } }} }}"
      else:
         label = self.slotName

      height = max( str( 2*len( self.outgoingI2cBuses ) ), "2" )
      self.node = Node( self.slotName, fillcolor="transparent", fontcolor="black",
                        height=height, style="dashed", width="4", label=label
                  ).getNode()


class PciDeviceConfig:
   def __init__( self, pmUnitScopedName, vendorId, deviceId, subSystemVendorId,
                 subSystemDeviceId, symlinkDeviceName=None, symlinkDir='fpgas', 
                 desiredDriver=None ):
      self.pmUnitScopedName = pmUnitScopedName
      self.vendorId = vendorId
      self.deviceId = deviceId
      self.subSystemVendorId = subSystemVendorId
      self.subSystemDeviceId = subSystemDeviceId
      self.symlinkDeviceName = symlinkDeviceName
      self.symlinkDir = symlinkDir
      self.i2cAdapterConfigs = []
      self.spiMasterConfigs = []
      self.ledCtrlConfigs = []
      self.xcvrCtrlConfigs = []
      self.infoRomConfigs = []
      self.miscCtrlConfigs = []
      self.parentConfig = None
      self.desiredDriver = desiredDriver
      self.node = None

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

   def addI2cAdapterConfigs( self, numAdapters, adapterBaseName, baseCsrOffset ):
      configs = []
      numFormatSpecifiers = adapterBaseName.count( '{}' )
      for i in range( numAdapters ):
         if numFormatSpecifiers == 2:
            deviceNum = re.search( r'(\d+)', self.pmUnitScopedName ).group( 1 )
            adapterName = adapterBaseName.format( deviceNum, i )
         else:
            adapterName = adapterBaseName.format( i )
         csrOffset = hex( int( baseCsrOffset, 16 ) + i * 0x80 )
         configs.append(
            I2cAdapterConfig( self, adapterName, "i2c_master", -1, csrOffset, 8 )
         )
      self.i2cAdapterConfigs.extend( configs )

   def addSpiMasterConfigs( self, newConfigs ):
      for config in newConfigs:
         config.addParentConfigPointer( self )
      self.spiMasterConfigs.extend( newConfigs )


   def addXcvrCtrlConfigs( self, numConfigs, basePortNumber, smbusName,
                           smbusAccelStart, accelBusRange, portType="osfp", 
                           xcvrBaseOffset="0xA010", ledBaseOffset="0x6100",
                           ledsPerXcvr=2, ledDeviceName='port_led',
                           portNumberSkipStep=1, xcvrOffsetStep=0x10,
                           portLedOffsetStep=0x10, lanesCount=None,
                           defaultLedColor='blue' ):
      newConfigs = enumerateXcvrConfigs( numConfigs, basePortNumber, smbusName,
                                         smbusAccelStart, accelBusRange, portType, 
                                         xcvrBaseOffset, ledBaseOffset, ledsPerXcvr,
                                         ledDeviceName, portNumberSkipStep,
                                         xcvrOffsetStep, portLedOffsetStep,
                                         lanesCount, defaultLedColor )
      for config in newConfigs:
         config.addParentConfigPointer( self )
      self.xcvrCtrlConfigs.extend( newConfigs )

   def addInfoRomConfigs( self, offset ):
      infoRomConfig = InfoRomConfigs( self.pmUnitScopedName, offset )
      infoRomConfig.addParentConfigPointer( self )
      self.infoRomConfigs.extend( [ infoRomConfig ] )

   def addMiscCtrlConfigs( self, newConfigs ):
      self.miscCtrlConfigs.extend( newConfigs )

   def addLedCtrlConfigs( self, newConfigs ):
      self.ledCtrlConfigs.extend( newConfigs )

   def asJson( self ):

      assert self.pmUnitScopedName and self.vendorId and self.deviceId \
         and self.subSystemVendorId and self.subSystemDeviceId, (
            "missing details in PciDeviceConfigs"
         )

      return {
         "pmUnitScopedName": self.pmUnitScopedName,
         "vendorId": self.vendorId,
         "deviceId": self.deviceId,
         "subSystemVendorId": self.subSystemVendorId,
         "subSystemDeviceId": self.subSystemDeviceId,
         "i2cAdapterConfigs": self.getI2cAdapterConfigsList(),
         "spiMasterConfigs": self.getSpiMasterConfigsList(),
         "ledCtrlConfigs": self.getLedCtrlConfigsList(),
         "xcvrCtrlConfigs": self.getXcvrConfigsList(),
         "infoRomConfigs": self.getInfoRomConfigsList(),
         **({ "miscCtrlConfigs": [ cfg.asJson() for cfg in self.miscCtrlConfigs ] }
            if self.miscCtrlConfigs else {}),
         **({"desiredDriver": self.desiredDriver} if self.desiredDriver else {})
      }

   def getI2cAdapterConfigsList( self ):
      return [ config.asJson() for config in self.i2cAdapterConfigs ]

   def getSpiMasterConfigsList( self ):
      return [ config.asJson() for config in self.spiMasterConfigs ]

   def getLedCtrlConfigsList( self ):
      configList = []
      for config in self.xcvrCtrlConfigs:
         portLeds = [ *config.parseXcvrLeds() ]
         for led in portLeds:
            configList.append( led )

      statusLedsNumbers = {}
      for config in self.ledCtrlConfigs:
         configList.append( config.parseStatusLeds( statusLedsNumbers ) )

      return configList

   def getXcvrConfigsList( self ):
      return [ config.parseConfig() for config in self.xcvrCtrlConfigs ]

   def getInfoRomConfigsList( self ):
      return [ config.asJson() for config in self.infoRomConfigs ]

   def generateSymlinkDevicePath( self ):
      platform = self.parentConfig.parentConfig.platformName
      self.symlinkDeviceName = (
         self.symlinkDeviceName or f"{ platform.upper() }_{ self.pmUnitScopedName }"
      )
      fpgaSymlinks = {
         f"/run/devmap/{ self.symlinkDir }/{ self.symlinkDeviceName }":
            constructDevicePaths( self )[ 0 ]
      }
      for infoRomConfig in self.infoRomConfigs:
         path = (
            f"/run/devmap/{ self.symlinkDir }/{ self.symlinkDeviceName }_INFO_ROM" )
         fpgaSymlinks[ path ] = (
               constructDevicePaths( infoRomConfig )[ 0 ]
         )

         # inforoms subdirectory to only contain fpga versions
         if self.symlinkDir == 'fpgas':
            path_inforoms = (
               f"/run/devmap/inforoms/{ self.symlinkDeviceName }_INFO_ROM" )
            fpgaSymlinks[ path_inforoms ] = (
                  constructDevicePaths( infoRomConfig )[ 0 ]
            )
      return fpgaSymlinks

   def renderNode(self):
      vid = f"VID: { self.vendorId }"
      did = f"DID: { self.deviceId }"
      svid = f"SVID: { self.subSystemVendorId }"
      sdid = f"SDID: { self.subSystemDeviceId }"

      label = ( f"{ self.pmUnitScopedName } |"
                f" {{ {{{ vid } | { did } }}| {{{ svid } | { sdid } }} }}" )
      self.node = Node( label, fillcolor="#ecf3e7", fontcolor="black", height="4",
                        width="4" ).getNode()


class I2cBus:
   def __init__( self, busName, parentConfig, devicesOnBus=None ):
      self.busName = busName
      self.parentConfig = parentConfig
      self.devicesOnBus = devicesOnBus or []

   def addI2cDevices( self, i2cDevices ):
      for device in i2cDevices:
         device.addBusName( self.busName )
      self.devicesOnBus.extend( i2cDevices )

   def generateSymlinkDevicePath( self ):
      busPath = constructBusPaths( self )[ 0 ]
      match = re.search( r'(\d+)@(\d+)', busPath )
      busPrefix = self.parentConfig.busSymlinkPrefix
      if not busPrefix:
         pciDevice = self.parentConfig.parentConfig
         busPrefix = f'{pciDevice.symlinkDeviceName}_SMBUS'
      return {
         f"/run/devmap/i2c-busses/{ busPrefix }"
         f"{ match.group( 1 ) }_CH{ match.group( 2 ) }": busPath
      }


class I2cAdapterConfig:
   def __init__( self, parentConfig, pmUnitScopedName, deviceName, iobufOffset,
                 csrOffset, numberOfAdapters, busSymlinkPrefix=None ):
      self.parentConfig = parentConfig
      self.pmUnitScopedName = pmUnitScopedName
      self.deviceName = deviceName
      self.iobufOffset = iobufOffset
      self.csrOffset = csrOffset
      self.numberOfAdapters = numberOfAdapters
      self.busSymlinkPrefix = busSymlinkPrefix
      self.buses = [
         I2cBus(
            busName=f"{ self.pmUnitScopedName }@{ i }",
            parentConfig=self,
            devicesOnBus=[]
         ) for i in range( numberOfAdapters )
      ]

   def asJson( self ):
      pmUnitScopedName = self.pmUnitScopedName
      deviceName = self.deviceName
      iobufOffset = str( self.iobufOffset ).lower()
      csrOffset = str( self.csrOffset ).lower()
      numberOfAdapters = self.numberOfAdapters

      assert pmUnitScopedName and deviceName and iobufOffset and csrOffset\
            and numberOfAdapters, "missing details in I2cAdapterConfigs"

      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": pmUnitScopedName,
            "deviceName": deviceName,
            **({ "iobufOffset": str( int( iobufOffset, 16 ) ) }\
               if iobufOffset and iobufOffset != "-1" else {}),
            "csrOffset": csrOffset
         },
         "numberOfAdapters": numberOfAdapters
      }


class SpiMasterConfig:
   def __init__( self, pmUnitScopedName, deviceName, iobufOffset,
                 csrOffset, spiDeviceConfigs=None ):
      self.pmUnitScopedName = pmUnitScopedName
      self.deviceName = deviceName
      self.iobufOffset = iobufOffset
      self.csrOffset = csrOffset
      self.spiDeviceConfigs = spiDeviceConfigs or []
      for config in self.spiDeviceConfigs:
         config.addParentConfigPointer( self )
      self.parentConfig = None

   def asJson( self ):
      pmUnitScopedName = self.pmUnitScopedName
      deviceName = self.deviceName
      iobufOffset = str( self.iobufOffset ).lower()
      csrOffset = self.csrOffset
      spiDeviceConfigs = self.spiDeviceConfigs

      assert pmUnitScopedName and deviceName and csrOffset is not None, (
         "missing details in SpiMasterConfigs"
      )

      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": pmUnitScopedName,
            "deviceName": deviceName,
            **({ "iobufOffset": str( int( iobufOffset, 16 ) ) }
               if iobufOffset and iobufOffset != "-1" else {}),
            "csrOffset": str( csrOffset ).lower()
         },
         **({ "spiDeviceConfigs": [ config.dict for config in spiDeviceConfigs ] }
            if spiDeviceConfigs else {}),
      }

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig


class SpiDeviceConfig:
   def __init__( self, pmUnitScopedName, chipSelect, modalias, maxSpeedHz ):
      self.pmUnitScopedName = pmUnitScopedName
      self.chipSelect = chipSelect
      self.modalias = modalias
      self.maxSpeedHz = maxSpeedHz
      self.dict = {
         "pmUnitScopedName": pmUnitScopedName,
         "chipSelect": chipSelect,
         "modalias": modalias,
         "maxSpeedHz": maxSpeedHz
      }
      self.parentConfig = None

   def generateSymlinkDevicePath( self ):
      return {}

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig


class Flash( SpiDeviceConfig ):
   def generateSymlinkDevicePath( self ):
      return {
         f"/run/devmap/flashes/{ self.pmUnitScopedName }":
            constructDevicePaths( self )[ 0 ]
      }


class XcvrConfig:
   def __init__( self, portNumber, portType, xcvrCtrlOffset, ledDeviceName,
                 led1Offset, led2Offset, led3Offset, led4Offset, i2cPath,
                 lanesCount, defaultLedColor ):
      self.portNumber = portNumber
      self.portType = portType
      self.xcvrCtrlOffset = xcvrCtrlOffset
      self.ledDeviceName = ledDeviceName
      self.led1Offset = led1Offset
      self.led2Offset = led2Offset
      self.led3Offset = led3Offset
      self.led4Offset = led4Offset
      self.pmUnitScopedName = f"{ portType }_PORT{ portNumber }_XCVR".upper()
      self.parentConfig = None
      self.i2cPath = i2cPath
      self.lanesCount = lanesCount
      self.symlink = f"/run/devmap/xcvrs/xcvr_{ portNumber }"
      self.ioSymlink = f"/run/devmap/xcvrs/xcvr_io_{self.portNumber}"
      self.ctrlSymlink = f"/run/devmap/xcvrs/xcvr_ctrl_{self.portNumber}"
      self.defaultLedColor = defaultLedColor

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

   def parseXcvrLeds( self ):
      returnList = []
      portNumber = self.portNumber
      portType = self.portType
      ledDeviceName = self.ledDeviceName
      ledList = []
      for i in range( 1, 5 ):
         attribute = f"led{ i }Offset"
         if hasattr( self, attribute ) and getattr( self, attribute ):
            ledList.append( getattr( self, attribute ) )
      ledIdx = 1

      assert portNumber and portType and len( ledList ) >= 1, (
            "missing details in xcvr leds"
      )

      for idx, ledOffset in enumerate( ledList ):
         if len( ledList ) == 1:
            portLedName = f'{ portType }_PORT{ portNumber }_LED'.upper()
         else:
            portLedName = f'{ portType }_PORT{ portNumber }_LED{ idx+1 }'.upper()

         returnList.append( {
            "fpgaIpBlockConfig": {
               "pmUnitScopedName": portLedName,
               "deviceName": ledDeviceName,
               "csrOffset": ledOffset.lower()
            },
            "portNumber": portNumber,
            "ledId": ledIdx
         } )
         ledIdx += 1

      return returnList

   def parseConfig( self ):
      portNumber = self.portNumber
      portType = self.portType
      xcvrCtrlOffset = self.xcvrCtrlOffset.lower()

      assert portNumber and portType and xcvrCtrlOffset, (
            "missing details in xcvr file"
      )

      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": f'{ portType }_PORT{ portNumber }_XCVR'.upper(),
            "deviceName": 'xcvr_ctrl',
            "csrOffset": xcvrCtrlOffset
         },
         "portNumber": portNumber,
      }

   def createBspRow( self ):
      rows = []
      port = self.portNumber
      color = self.defaultLedColor
      def _createBspRow( ledId, lanes ):
         ledCount = 1
         if self.led4Offset:
            ledCount = 4
         elif self.led2Offset:
            ledCount = 2

         ledIdx = ( ledId - 1 ) % ledCount + 1
         return {
            "TcvrId": port,
            "TcvrLaneIdList": " ".join(map(str, range(lanes[0], lanes[1] + 1))),
            "PimId": 1, # All fixed systems are ID 1
            "AccessControllerId": self.portNumber, # Not used
            "AccessControlType": "CPLD",
            "ResetPath": f"{self.ctrlSymlink}/xcvr{port}_reset",
            "ResetMask": "1",
            "ResetHoldHi": "0",
            "PresentPath": f"{self.ctrlSymlink}/xcvr{port}_present",
            "PresentMask": "1",
            "PresentHoldHi": "0",
            "IoControllerId": port,
            "IoControlType": "I2C",
            "IoPath": self.ioSymlink,
            "LedId": ledId,
            "LedBluePath": f"/sys/class/leds/port{port}_led{ledIdx}:{color}:status",
            "LedYellowPath": f"/sys/class/leds/port{port}_led{ledIdx}:yellow:status",
         }

      lanes = self.lanesCount // 4 if self.portType == "qsfp" else self.lanesCount // 2
      ledId = ( port - 1 ) * 2
      if self.led2Offset:
         rows.append( _createBspRow( ledId + 1, [ 1, lanes ] ) )
         rows.append( _createBspRow( ledId + 2, [ lanes + 1, lanes * 2 ] ) )
      if self.led3Offset and self.led4Offset:
         rows.append( _createBspRow( ledId + 3, [ lanes + 2, lanes * 3 ] ) )
         rows.append( _createBspRow( ledId + 4, [ lanes + 3, lanes * 4 ] ) )
      if not self.led2Offset:
         rows.append( _createBspRow( port, [ 1, self.lanesCount ] ) )
      return rows


class LedConfig:
   def __init__( self, ledName, offset ):
      self.ledName = ledName
      self.offset = offset

   def parseStatusLeds( self, statusLedNumbers ):
      name = self.ledName
      offset = self.offset

      assert name and offset, "missing details in status leds"

      deviceName = f"{ name[ :3 ].lower() }_led"
      statusLedNumbers[ deviceName ] = statusLedNumbers.get( deviceName, 0 ) + 1
      led = {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": name.upper(),
            "deviceName": deviceName,
            "csrOffset": offset.lower()
         },
         "portNumber": -1,
         "ledId": statusLedNumbers[ deviceName ]
      }

      return led


class InfoRomConfigs:
   def __init__( self, fpgaPrefix, offset ):
      self.pmUnitScopedName = f'{fpgaPrefix}_INFO_ROM'
      self.offset = offset

   def asJson( self ):
      return {
         "pmUnitScopedName": self.pmUnitScopedName,
         "deviceName": "fpga_info_iob",
         "csrOffset": self.offset
      }

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

class MiscConfig:
   def __init__( self, name, deviceName, offset ):
      self.name = name
      self.deviceName = deviceName
      self.offset = offset

   def asJson( self ):
      assert self.name and self.deviceName and self.offset, (
         "Invalid misc config")
      return {
         "pmUnitScopedName": self.name,
         "deviceName": self.deviceName,
         "csrOffset": self.offset
      }


def enumerateXcvrConfigs( numConfigs, basePortNumber, smbusName, smbusAccelStart, 
                          accelBusRange, portType, xcvrBaseOffset, ledBaseOffset,
                          ledsPerXcvr, ledDeviceName, portNumberSkipStep=1,
                          xcvrOffsetStep=0x10, portLedOffsetStep=0x10,
                          lanesCount=None, defaultLedColor="blue" ):
   configs = []
   currIndex = basePortNumber
   currLedOffset = int( ledBaseOffset, 16 )
   currSmbusAccel = smbusAccelStart
   currAccelBus = accelBusRange[ 0 ]
   for i in range( numConfigs ):
      xcvrCtrlOffset = hex( int( xcvrBaseOffset, 16 ) + i * xcvrOffsetStep )
      ledOffsets = [ hex( currLedOffset + i * 0x10 )
                     for i in range( ledsPerXcvr ) ]
      i2cPath = f"{smbusName}{currSmbusAccel}@{currAccelBus}"
      configs.append(
         XcvrConfig(
            portNumber=currIndex,
            portType=portType,
            xcvrCtrlOffset=xcvrCtrlOffset,
            ledDeviceName=ledDeviceName,
            led1Offset=ledOffsets[ 0 ],
            led2Offset=ledOffsets[ 1 ] if ledsPerXcvr > 1 else None,
            led3Offset=ledOffsets[ 2 ] if ledsPerXcvr > 2 else None,
            led4Offset=ledOffsets[ 3 ] if ledsPerXcvr > 3 else None,
            i2cPath=i2cPath,
            lanesCount=lanesCount,
            defaultLedColor=defaultLedColor
         )
      )
      if portNumberSkipStep > 1:
         if currIndex % portNumberSkipStep == 0:
            currIndex += portNumberSkipStep
      currIndex += 1
      currLedOffset += ledsPerXcvr * portLedOffsetStep
      if currAccelBus == accelBusRange[ 1 ]:
         currSmbusAccel += 1
         currAccelBus = 0
      else:
         currAccelBus += 1
   return configs


def enumerateFANSlotConfigs( numConfigs, generalPath, fansPerCpld=4 ):
   configs = []
   for i in range( numConfigs ):
      if '{}' in generalPath:
         presenceDevicePath = generalPath.format( i // fansPerCpld )
      else:
         presenceDevicePath = generalPath
      configs.append(
         SlotConfig(
            slotName=f"FAN_SLOT@{ i }",
            presenceFileName=f"fan{ ( i % fansPerCpld ) + 1 }_present",
            presenceDevicePath=presenceDevicePath
         )
      )
   return configs


def enumeratePciDeviceConfigs( numConfigs, deviceBaseName, vendorId, deviceId,
                               subSystemVendorId, subSystemBaseDeviceId ):
   configs = []
   for i in range( numConfigs ):
      if '{}' in deviceBaseName:
         deviceName = deviceBaseName.format( i )
      else:
         deviceName = deviceBaseName
      configs.append(
         PciDeviceConfig(
            pmUnitScopedName=deviceName,
            vendorId=vendorId,
            deviceId=deviceId,
            subSystemVendorId=subSystemVendorId,
            subSystemDeviceId=f"0x{ ( int( subSystemBaseDeviceId, 16 ) + i ):04x}"
         )
      )
   return configs


class Thresholds:
   def __init__( self, upperCriticalVal=None, lowerCriticalVal=None,
                 maxAlarmVal=None, minAlarmVal=None ):
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


class SensorType( Enum ):
   POWER = 0
   VOLTAGE = 1
   CURRENT = 2
   TEMP = 3
   FAN_SPEED = 4


class SensorConfig:
   def __init__( self, name, filename, sensorType, compute=None, thresholds=None,
                 prependPmUnit=True ):
      assert name
      assert filename
      assert sensorType in SensorType
      self.name = name
      self.filename = filename
      self.thresholds = thresholds
      self.compute = compute
      self.sensorType = sensorType
      self.parentConfig = None
      self.prependPmUnit = prependPmUnit

   def toDict( self, pmUnitIndex=None ):
      sensorDict = OrderedDict()
      baseSensorPath = self.parentConfig.symlinkPath
      
      if self.prependPmUnit and self.parentConfig:
         pmUnitName = self.parentConfig.parentConfig.pmUnitName
         sensorDict[ 'name' ] = f"{ pmUnitName }_{ self.name }"
      else:
         sensorDict[ 'name' ] = self.name

      sensorDict[ 'sysfsPath' ] = (
         f"{ baseSensorPath.format( pmUnitIndex ) }/{ self.filename }"
         if pmUnitIndex and "{}" in baseSensorPath
         else f"{ baseSensorPath.format( pmUnitIndex ) }/{ self.filename }"
      )
      sensorDict[ 'type' ] = self.sensorType.value
      if self.thresholds:
         sensorDict[ 'thresholds' ] = self.thresholds.toDict()
      if self.compute:
         sensorDict[ 'compute' ] = self.compute
      
      return sensorDict

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig


class SCMUnit( PmUnitConfig ):
   def __init__( self ):
      super().__init__( "SCM" )


class SCMFairywren( SCMUnit ):
   supportsP1 = False

   def __init__( self ):
      super().__init__()

      self.setSlotTypeConfig(
         idPromConfigBusName="SMBus I801 adapter at 1000",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )

      scmMpsDev = FairywrenSensor( "0x40", "pmbus", "SCM_MPS_PMBUS" )
      scmMpsDev.addSensorConfigs( [
         SensorConfig( "ECB_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/32000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=10.5
                       ) ),
         SensorConfig( "ECB_VOUT", "in2_input", SensorType.VOLTAGE,
                       compute="@/32000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "ECB_IOUT", "curr1_input", SensorType.CURRENT,
                       compute="@/1000.0" )
      ] )

      scmIdprom = FairywrenIdProm( "0x50", "24c512", "SCM_IDPROM_P1",
                                   hasCpuMac=True )

      i2cDeviceConfigs = [
         scmMpsDev,
      ]

      if self.supportsP1:
         i2cDeviceConfigs.append( scmIdprom )

      self.addI2cDeviceConfigs( i2cDeviceConfigs )

      self.scmFpga = PciDeviceConfig( "SCM_FPGA", "0x3475", "0x0001", "0x3475",
                                      "0x0008", symlinkDeviceName="MERU_SCM_CPLD" )
      self.scmFpga.addInfoRomConfigs( "0x100" )
      self.scmFpga.addMiscCtrlConfigs( [
         MiscConfig( name="SCM_ADC", deviceName="adc", offset="0x7300" ),
      ] )
      self.addPciDeviceConfigs( [ self.scmFpga ] )

      self.scmFpga.addI2cAdapterConfigs( 2, "SCM_I2C_MASTER{}", "0x8000" )

      self.scmI2cMaster0 = self.scmFpga.i2cAdapterConfigs[ 0 ]
      self.scmI2cMaster0.buses[ 0 ].addI2cDevices( [ scmMpsDev ] )

      if self.supportsP1:
         self.scmI2cMaster0.buses[ 1 ].addI2cDevices( [ scmIdprom ] )

      self.scmI2cMaster1 = self.scmFpga.i2cAdapterConfigs[ 1 ]

      cpuCoreTemp = EmbeddedSensorConfig(
                        pmUnitScopedName="CPU_CORE_TEMP",
                        sysfsPath="/sys/bus/platform/devices/coretemp.0"
                    )

      cpuCoreTemp.addSensorConfigs( [
         SensorConfig( "CPU_PACKAGE_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "CPU_CORE0_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "CPU_CORE1_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "CPU_CORE2_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "CPU_CORE3_TEMP", "temp5_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "CPU_CORE4_TEMP", "temp6_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "CPU_CORE5_TEMP", "temp7_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "CPU_CORE6_TEMP", "temp8_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "CPU_CORE7_TEMP", "temp9_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=100.0, maxAlarmVal=90.0
                       ) )
      ] )

      nvmeTemp = EmbeddedSensorConfig(
         pmUnitScopedName="NVME_TEMP",
         sysfsPath="/sys/class/nvme/nvme0"
      )
      nvmeTemp.addSensorConfigs( [
         SensorConfig( "NVME_COMPOSITE_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                          upperCriticalVal=80.0
                       ) )
      ] )
      self.addEmbeddedSensorConfigs( [ cpuCoreTemp, nvmeTemp ] )


class SMBUnit( PmUnitConfig ):
   def __init__( self, prefixSymlink=None ):
      super().__init__( "SMB", prefixSymlink )


class PSUUnit( PmUnitConfig ):
   def __init__( self, singlePSU=False, *args, **kwargs ):
      super().__init__( "PSU" )

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=1
      )

      psuBus = PSUBus( "0x58", "pmbus", "PSU_PMBUS", incomingBusIndex=0,
                       singlePSU=singlePSU, *args, **kwargs )
      psuBus.addSensorConfigs( [
         SensorConfig( "VIN", "in1_input", SensorType.VOLTAGE, compute="@/1000.0" ),
         SensorConfig( "VOUT", "in3_input", SensorType.VOLTAGE, compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "FAN1_RPM", "fan1_input", SensorType.FAN_SPEED,
                       thresholds=Thresholds(
                           upperCriticalVal=25500.0, lowerCriticalVal=0.0
                       ) ),
         SensorConfig( "FAN2_RPM", "fan2_input", SensorType.FAN_SPEED,
                       thresholds=Thresholds(
                           upperCriticalVal=25500.0, lowerCriticalVal=0.0
                       ) ),
         SensorConfig( "TEMP1", "temp1_input", SensorType.TEMP, compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=70.0, maxAlarmVal=65.0
                       ) ),
         SensorConfig( "TEMP2", "temp2_input", SensorType.TEMP, compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=130.0, maxAlarmVal=120.0
                       ) ),
         SensorConfig( "TEMP3", "temp3_input", SensorType.TEMP, compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=112.0
                       ) ),
         SensorConfig( "IIN", "curr1_input", SensorType.CURRENT,
                       compute="@/1000.0" ),
         SensorConfig( "IOUT", "curr2_input", SensorType.CURRENT,
                       compute="@/1000.0" ),
         SensorConfig( "PIN", "power1_input", SensorType.POWER,
                       compute="@/1000000.0" ),
         SensorConfig( "POUT", "power2_input", SensorType.POWER,
                       compute="@/1000000.0" ),
      ] )

      self.addI2cDeviceConfigs( [
         psuBus
      ] )


class FANUnit( PmUnitConfig ):
   def __init__( self ):
      super().__init__( "FAN" )
