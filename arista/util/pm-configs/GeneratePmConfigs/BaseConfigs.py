# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from collections import OrderedDict
import json
import re


def reformatOneElementLists( jsonDump ):
   pattern = re.compile( r'\[\s*(-?\d+)\s*\]' )
   output_string = pattern.sub( r'[\1]', jsonDump )
   return output_string


def constructHelper( currDevice, currPath, outputList ):
   while not isinstance( currDevice, PmUnitConfig ):
      currDevice = currDevice.parentConfig
   platformConfig = currDevice.parentConfig
   if currDevice.pmUnitName == platformConfig.rootPmUnitName:
      outputList.append( currPath )
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
   outputList = []
   startPath = f"/[{ bus.busName }]"
   outputList = []
   constructHelper( bus, startPath, outputList )
   return outputList


def constructDevicePaths( device ):
   startPath = f"/[{ device.pmUnitScopedName }]"
   outputList = []
   constructHelper( device, startPath, outputList )
   return outputList


class PlatformConfig:
   def __init__( self, platformName, rootPmUnitName="SCM" ):
      self.platformName = platformName
      self.rootPmUnitName = rootPmUnitName
      self.pmUnitConfigs = []
      self.i2cAdaptersFromCpu = []
      self.kmodsSettings = {
         "bspKmodsRpmName": "arista_bsp_kmods",
         "bspKmodsRpmVersion": "0.7.2-1",
         "bspKmodsToReload": [],
         "sharedKmodsToReload": [],
         "upstreamKmodsToLoad": []
      }

   def getSlotTypeConfigsDict( self ):
      jsonDict = {}
      for pmConfig in self.pmUnitConfigs:
         jsonDict[ 
            pmConfig.slotTypeConfig.slotName 
         ] = pmConfig.slotTypeConfig.asJson()
      return jsonDict

   def addPmUnitConfigs( self, newConfigs ):
      for config in newConfigs:
         config.addParentConfigPointer( self )
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
   
   def addI2cAdaptersFromCpu( self, newConfigs ):
      self.i2cAdaptersFromCpu.extend( newConfigs )

   def addKmodsSettings( self, newConfigDict ):
      self.kmodsSettings.update( newConfigDict )

   def asJson( self ):
      jsonDict = OrderedDict()
      jsonDict[ "platformName" ] = self.platformName
      jsonDict[ "rootPmUnitName" ] = self.rootPmUnitName
      jsonDict[ "slotTypeConfigs" ] = self.getSlotTypeConfigsDict()
      jsonDict[ "pmUnitConfigs" ] = self.getPmUnitConfigsDict()
      jsonDict[ "i2cAdaptersFromCpu" ] = self.i2cAdaptersFromCpu
      jsonDict[ "symbolicLinkToDevicePath" ] = (
         self.parseSymbolicLinkToDevicePaths()
      )
      jsonDict[ "bspKmodsRpmName" ] = self.kmodsSettings[ "bspKmodsRpmName" ]
      jsonDict[ "bspKmodsRpmVersion" ] = self.kmodsSettings[ "bspKmodsRpmVersion" ]
      jsonDict[ "bspKmodsToReload" ] = self.kmodsSettings[ "bspKmodsToReload" ] 
      jsonDict[ "sharedKmodsToReload" ] = self.kmodsSettings[ "sharedKmodsToReload" ] 
      jsonDict[ "upstreamKmodsToLoad" ] = self.kmodsSettings[ "upstreamKmodsToLoad" ] 

      jsonDump = json.dumps( jsonDict, indent=2 )
      output = reformatOneElementLists( jsonDump )

      return output


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

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

   def asJson( self ):
      idpCfg = self.parseIdpromConfig()

      assert self.numOutgoingI2cBuses is not None, (
         "numOutgoingI2cBuses is required"
      )

      return {
         "numOutgoingI2cBuses": self.numOutgoingI2cBuses,
         **({ "idpromConfig": idpCfg } if idpCfg and all( idpCfg.values() ) else {}),
         "pmUnitName": self.pmUnitName
      }

   def parseIdpromConfig( self ):
      busName = self.idPromConfigBusName
      address = self.idPromConfigAddress
      kernelDeviceName = self.idPromConfigKernelDeviceName
      offset = self.idPromConfigOffset
      assert ( busName == address == kernelDeviceName ) or\
         ( busName and address and kernelDeviceName ), (
            "Error: 1 or 2 of the strings are empty"
         )

      return {
         "busName": busName,
         "address": address.lower() if address else '',
         "kernelDeviceName": kernelDeviceName,
         "offset": offset
      }


class PmUnitConfig:
   def __init__( self, pmUnitName ):
      self.pmUnitName = pmUnitName
      self.slotTypeConfig = SlotTypeConfig( self.pmUnitName )
      self.i2cDeviceConfigs = []
      self.outgoingSlotConfigs = []
      self.pciDeviceConfigs = []
      self.embeddedSensorConfigs = []
      self.symlinkToDevicePaths = {}
      self.parentConfig = None

   def setSlotTypeConfig( self, numOutgoingI2cBuses=0, idPromConfigBusName=None, 
                          idPromConfigAddress=None, 
                          idPromConfigKernelDeviceName=None,
                          idPromConfigOffset=None ):
      self.slotTypeConfig.numOutgoingI2cBuses = numOutgoingI2cBuses
      self.slotTypeConfig.idPromConfigBusName = idPromConfigBusName
      self.slotTypeConfig.idPromConfigAddress = idPromConfigAddress
      self.slotTypeConfig.idPromConfigKernelDeviceName = idPromConfigKernelDeviceName
      self.slotTypeConfig.idPromConfigOffset = idPromConfigOffset
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
         **self.generateSpiDeviceSymlinks()
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
            portNumber = xcvrConfig.portNumber
            symlinkDict[ f"/run/devmap/xcvrs/xcvr_{ portNumber }" ] = (
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
               symlinkDict[ 
                  f"/run/devmap/eeproms/{ platform.upper() }_SMB_EEPROM"
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
   

class EmbeddedSensorConfig:
   def __init__( self, pmUnitScopedName, sysfsPath ):
      self.pmUnitScopedName = pmUnitScopedName
      self.sysfsPath = sysfsPath
      self.parentConfig = None

   def asJson( self ):

      assert self.pmUnitScopedName and self.sysfsPath, (
         "missing details in EmbeddedSensorsConfig"
      )

      return {
         "pmUnitScopedName": self.pmUnitScopedName,
         "sysfsPath": self.sysfsPath
      }
   
   def generateSymlinkDevicePath( self ):
      return { 
         f"/run/devmap/sensors/{ self.pmUnitScopedName }": 
         constructDevicePaths( self )[ 0 ]
      }
   
   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig  

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

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig 

   def addBusName( self, busName ):
      self.busName = busName

   def generateSymlinkDevicePath( self ):
      return {}

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


class GpioChip( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      super().__init__( *args, **kwargs )
      self.isGpioChip = True

   def generateSymlinkDevicePath( self ):
      return {
         f"/run/devmap/gpiochips/{ self.pmUnitScopedName }": 
            constructDevicePaths( self )[ 0 ]
      }
   

class Sensor( I2cDeviceConfig ):
   def generateSymlinkDevicePath( self ):
      pmUnitName = self.parentConfig.pmUnitName
      symlinkDict = {
         "SCM":
            f"/run/devmap/sensors/CPU_"
            f"{ self.pmUnitScopedName.split( '_', 1 )[ 1 ] }",
         "SMB": f"/run/devmap/sensors/{ self.pmUnitScopedName }"
      }
      return { symlinkDict[ pmUnitName ]: constructDevicePaths( self )[ 0 ] }

   
class SMBCpld( I2cDeviceConfig ):
   def generateSymlinkDevicePath( self ):
      platform = self.parentConfig.parentConfig.platformName
      return {
         f"/run/devmap/cplds/{ platform.upper() }_SMB_CPLD":
            constructDevicePaths( self )[ 0 ]
      }


class FANCpld( I2cDeviceConfig ):
   def generateSymlinkDevicePath( self ):
      devicePath = constructDevicePaths( self )[ 0 ]
      match = re.search( r'FAN(\d+)', devicePath )
      if not match:
         return {
            f"/run/devmap/cplds/{ self.pmUnitScopedName }": devicePath,
            f"/run/devmap/sensors/{ self.pmUnitScopedName }": devicePath
         }
      else:
         return {
            f"/run/devmap/cplds/{ self.pmUnitScopedName }": 
               devicePath,
            f"/run/devmap/sensors/FAN_CPLD{ match.group( 1 ) }":
               devicePath
         }


class SCMIdProm( I2cDeviceConfig ):
   def generateSymlinkDevicePath( self ):
      return {
         f"/run/devmap/eeproms/MERU_SCM_EEPROM_"
         f"{ self.pmUnitScopedName.split( '_' )[ -1 ] }": 
            constructDevicePaths( self )[ 0 ]
      }
   

class PSUBus( I2cDeviceConfig ):
   def generateSymlinkDevicePath(self ):
      symlinkDict = OrderedDict()
      devicePaths = constructDevicePaths( self )
      for path in devicePaths:
         match = re.search( r'PSU_SLOT@(\d+)', path )
         portNum = int( match.group( 1 ) ) + 1
         symlinkDict[ f"/run/devmap/sensors/PSU{ portNum }_PMBUS" ] = path
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


class PciDeviceConfig:
   def __init__( self, pmUnitScopedName, vendorId, deviceId, subSystemVendorId,
                 subSystemDeviceId ):
      self.pmUnitScopedName = pmUnitScopedName
      self.vendorId = vendorId
      self.deviceId = deviceId
      self.subSystemVendorId = subSystemVendorId
      self.subSystemDeviceId = subSystemDeviceId
      self.i2cAdapterConfigs = []
      self.spiMasterConfigs = []
      self.ledCtrlConfigs = []
      self.xcvrCtrlConfigs = []
      self.parentConfig = None

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

   def addXcvrCtrlConfigs( self, numConfigs, basePortNumber, portType="osfp", 
                           xcvrBaseOffset="0xA010", ledBaseOffset="0x6100",
                           ledsPerXcvr=2, portNumberSkipStep=1 ):
      newConfigs = enumerateXcvrConfigs( numConfigs, basePortNumber, portType, 
                                         xcvrBaseOffset, ledBaseOffset, ledsPerXcvr,
                                         portNumberSkipStep )
      for config in newConfigs:
         config.addParentConfigPointer( self )
      self.xcvrCtrlConfigs.extend( newConfigs )

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
         "xcvrCtrlConfigs": self.getXcvrConfigsList()
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

      for identifier, config in enumerate( self.ledCtrlConfigs ):
         configList.append( config.parseStatusLeds( identifier+1 ) )
      
      return configList
   
   def getXcvrConfigsList( self ):
      return [ config.parseConfig() for config in self.xcvrCtrlConfigs ]

   def generateSymlinkDevicePath( self ):
      platform = self.parentConfig.parentConfig.platformName
      pmUnitName = self.parentConfig.pmUnitName
      symlinkDict = {
         "SCM": "/run/devmap/fpgas/MERU_SCM_CPLD",
         "SMB": f"/run/devmap/fpgas/{ platform.upper() }_{ self.pmUnitScopedName }"
      }
      return { symlinkDict[ pmUnitName ]: constructDevicePaths( self )[ 0 ] } 


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
      pciDevice = self.parentConfig.parentConfig
      pciDeviceName = pciDevice.pmUnitScopedName
      platform = pciDevice.parentConfig.parentConfig.platformName
      pmUnitName = pciDevice.parentConfig.pmUnitName
      busPath = constructBusPaths( self )[ 0 ]
      match = re.search( r'(\d+)@(\d+)', busPath )
      symlinkDict = {
         "SCM": 
            f"/run/devmap/i2c-busses/MERU_SCM_CPLD_SMBUS"
            f"{ match.group( 1 ) }_CH{ match.group( 2 ) }",
         "SMB":
            f"/run/devmap/i2c-busses/{ platform.upper() }_{ pciDeviceName }_SMBUS"
            f"{ match.group( 1 ) }_CH{ match.group( 2 ) }"
      }
      return { symlinkDict[ pmUnitName ]: busPath }


class I2cAdapterConfig:
   def __init__( self, parentConfig, pmUnitScopedName, deviceName, iobufOffset, 
                 csrOffset, numberOfAdapters ):
      self.parentConfig = parentConfig
      self.pmUnitScopedName = pmUnitScopedName
      self.deviceName = deviceName
      self.iobufOffset = iobufOffset
      self.csrOffset = csrOffset
      self.numberOfAdapters = numberOfAdapters
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
   def __init__( self, portNumber, portType,	xcvrCtrlOffset, led1Offset,
                 led2Offset, led3Offset, led4Offset ):
      self.portNumber = portNumber
      self.portType = portType
      self.xcvrCtrlOffset = xcvrCtrlOffset
      self.led1Offset = led1Offset
      self.led2Offset = led2Offset
      self.led3Offset = led3Offset
      self.led4Offset = led4Offset
      self.pmUnitScopedName = f"{ portType }_PORT{ portNumber }_XCVR".upper()
      self.parentConfig = None

   def addParentConfigPointer( self, parentConfig ):
      self.parentConfig = parentConfig

   def parseXcvrLeds( self ):
      returnList = []
      portNumber = self.portNumber
      portType = self.portType
      ledList = []
      for i in range( 1, 5 ):
         attribute = f"led{ i }Offset"
         if hasattr( self, attribute ) and getattr( self, attribute ):
            ledList.append( getattr( self, attribute ) )
      ledIdx = 1

      assert portNumber and portType and len( ledList ) >= 2, (
            "missing details in xcvr leds"
      )
      
      for idx, ledOffset in enumerate( ledList ):
         returnList.append( {
            "fpgaIpBlockConfig": {
               "pmUnitScopedName": 
                  f'{ portType }_PORT{ portNumber }_LED{ idx+1 }'.upper(),
               "deviceName": 'port_led',
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


class LedConfig:
   def __init__( self, ledName, offset ):
      self.ledName = ledName
      self.offset = offset

   def parseStatusLeds( self, identifier ):
      name = self.ledName
      offset = self.offset

      assert name and offset, "missing details in status leds"
      
      led = {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": name.upper(),
            "deviceName": f"{ name[ :3 ].lower() }_led",
            "csrOffset": offset.lower()
         },
         "portNumber": -1,
         "ledId": identifier
      }
   
      return led


def enumerateXcvrConfigs( numConfigs, basePortNumber, portType, xcvrBaseOffset, 
                          ledBaseOffset, ledsPerXcvr, portNumberSkipStep=1 ):
   configs = []
   currIndex = basePortNumber
   currLedOffset = int( ledBaseOffset, 16 )
   for i in range( numConfigs ):
      xcvrCtrlOffset = hex( int( xcvrBaseOffset, 16 ) + i * 0x10 )
      ledOffsets = [ hex( currLedOffset + i * 0x10 ) 
                     for i in range( ledsPerXcvr ) ]
      configs.append( 
         XcvrConfig(
            portNumber=currIndex,
            portType=portType,
            xcvrCtrlOffset=xcvrCtrlOffset,
            led1Offset=ledOffsets[ 0 ],
            led2Offset=ledOffsets[ 1 ],
            led3Offset=ledOffsets[ 2 ] if ledsPerXcvr > 2 else None,
            led4Offset=ledOffsets[ 3 ] if ledsPerXcvr > 3 else None
         )
      )
      if portNumberSkipStep > 1:
         if currIndex % portNumberSkipStep == 0:
            currIndex += portNumberSkipStep
      currIndex += 1
      currLedOffset += ledsPerXcvr * 0x10
   return configs


def enumerateFANSlotConfigs( numConfigs, generalPath ):
   configs = []
   for i in range( numConfigs ):
      if '{}' in generalPath:
         presenceDevicePath = generalPath.format( i // 4 )
      else:
         presenceDevicePath = generalPath
      configs.append( 
         SlotConfig(
            slotName=f"FAN_SLOT@{ i }",
            presenceFileName=f"fan{ ( i % 4 ) + 1 }_present",
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


class SCMUnit( PmUnitConfig ):
   def __init__( self ):
      super().__init__( "SCM" )


class SCMFairyWren( SCMUnit ):
   def __init__( self ):
      super().__init__()

      self.setSlotTypeConfig(
         idPromConfigBusName="SMBus I801 adapter at 1000",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )

      scmMpsDev = Sensor( "0x40", "pmbus", "SCM_MPS_PMBUS" )
      scmIdprom = SCMIdProm( "0x50", "24c512", "SCM_IDPROM_P1", hasCpuMac=True )
      scmPxm1310_1 = Sensor( "0x30", "pxm1310", "SCM_PXM1310_1" )
      scmPxe1610 = Sensor( "0x3e", "pxe1610", "SCM_PXE1211" )
      scmPxm1310_2 = Sensor( "0x40", "pxm1310", "SCM_PXM1310_2" )
      self.addI2cDeviceConfigs( [
         scmMpsDev,
         scmIdprom,
         scmPxm1310_1,
         scmPxe1610,
         scmPxm1310_2
      ] )

      scmFpga = PciDeviceConfig( "SCM_FPGA", "0x3475", "0x0001", "0x3475", "0x0008" )
      self.addPciDeviceConfigs( [ scmFpga ] )

      scmFpga.addI2cAdapterConfigs( 2, "SCM_I2C_MASTER{}", "0x8000" )

      scmI2cMaster0 = scmFpga.i2cAdapterConfigs[ 0 ]
      scmI2cMaster0.buses[ 0 ].addI2cDevices( [ scmMpsDev ] )
      scmI2cMaster0.buses[ 1 ].addI2cDevices( [ scmIdprom ] )
      scmI2cMaster0.buses[ 2 ].addI2cDevices( [
         scmPxm1310_1,
         scmPxe1610,
         scmPxm1310_2
      ] )

      scmI2cMaster1 = scmFpga.i2cAdapterConfigs[ 1 ]
      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="SMB_SLOT@0",
            outgoingI2cBuses=[ 
               scmI2cMaster1.buses[ 0 ],
               scmI2cMaster1.buses[ 2 ],
               scmI2cMaster1.buses[ 3 ]
            ]
         )
      ] )

      self.addEmbeddedSensorConfigs( [
         EmbeddedSensorConfig( 
            pmUnitScopedName="CPU_CORE_TEMP", 
            sysfsPath="/sys/bus/platform/devices/coretemp.0" 
         )
      ] )


class SMBUnit( PmUnitConfig ):
   def __init__( self ):
      super().__init__( "SMB" )


class PSUUnit( PmUnitConfig ):
   def __init__( self ):
      super().__init__( "PSU" )

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=1
      )

      self.addI2cDeviceConfigs( [
         PSUBus( "0x58", "pmbus", "PSU_PMBUS", incomingBusIndex=0 )
      ] )


class FANUnit( PmUnitConfig ):
   def __init__( self ):
      super().__init__( "FAN" )