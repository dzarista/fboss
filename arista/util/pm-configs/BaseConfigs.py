# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from collections import OrderedDict
import json
import re


def reformatOneElementLists( jsonDump ):
   pattern = re.compile( r'\[\s*(-?\d+)\s*\]' )
   output_string = pattern.sub( r'[\1]', jsonDump )
   return output_string


class PlatformConfig:
   def __init__( self, platformName, rootPmUnitName="SCM", slotTypeConfigs=None,
                 pmUnitConfigs=None, i2cAdaptersFromCpu=None, kmodsSettings=None ):
      self.platformName = platformName
      self.rootPmUnitName = rootPmUnitName
      self.slotTypeConfigs = slotTypeConfigs or []
      self.pmUnitConfigs = pmUnitConfigs or []
      self.i2cAdaptersFromCpu = (
         i2cAdaptersFromCpu 
         or [ { "adapter" : "SMBus I801 adapter at 1000" } ]
      )
      self.kmodsSettings = (
         kmodsSettings 
         or {
            "bspKmodsRpmName": "arista_bsp_kmods",
            "bspKmodsRpmVersion": "0.7.2-1",
            "bspKmodsToReload" : [
               "scd-xcvr", 
               "scd-spi",
               "scd-leds",
               "scd-smbus",
               "dsf-fan-cpld"
            ],
            "sharedKmodsToReload": [ "scd" ],
            "upstreamKmodsToLoad": [ "spidev", "i2c-i801" ] 
         }
      )

   def addSlotTypeConfigs( self, newConfigs ):
      self.slotTypeConfigs.extend( newConfigs ) 

   def getSlotTypeConfigsDict( self ):
      jsonDict = {}
      for config in self.slotTypeConfigs:
         name = config.slotName
         jsonDict[ name ] = config.asJson()
      return jsonDict

   def addPmUnitConfigs( self, newConfigs ):
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
         if pmUnitDict:
            for symlink, devicePath in pmUnitDict.items():
               symlinkDict[ symlink ] = devicePath
      return symlinkDict

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
   def __init__( self, slotName, numOutgoingI2cBuses=0, 
                 idPromConfigBusName=None, idPromConfigAddress=None,
                 idpromConfigKernelDeviceName=None, idPromConfigOffset=None ):
      self.slotName = slotName
      self.numOutgoingI2cBuses = numOutgoingI2cBuses
      self.idPromConfigBusName = idPromConfigBusName
      self.idPromConfigAddress = idPromConfigAddress
      self.idPromConfigKernelDeviceName = idpromConfigKernelDeviceName
      self.idPromConfigOffset = idPromConfigOffset
      self.pmUnitName = slotName.split( '_' )[ 0 ]

   def asJson( self ):
      idpCfg = self.parseIdpromConfig()

      assert self.numOutgoingI2cBuses is not None, (
         "numOutgoingI2cBuses is required"
      )

      return {
         "numOutgoingI2cBuses": self.numOutgoingI2cBuses,
         **({ "idpromConfig": idpCfg } if idpCfg and all( idpCfg.values() ) else {}),
         **({ "pmUnitName": self.pmUnitName } if self.pmUnitName else {})
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
   def __init__( self, pmUnitName, i2cDeviceConfigs=None, outgoingSlotConfigs=None, 
                 pciDeviceConfigs=None, embeddedSensorConfigs=None, 
                 symlinkToDevicePaths=None ):
      self.pmUnitName = pmUnitName
      self.i2cDeviceConfigs = i2cDeviceConfigs or []
      self.outgoingSlotConfigs = outgoingSlotConfigs or []
      self.pciDeviceConfigs = pciDeviceConfigs or []
      self.embeddedSensorConfigs = embeddedSensorConfigs or []
      self.symlinkToDevicePaths = symlinkToDevicePaths or {}

   def addI2cDeviceConfigs( self, newConfigs ):
      self.i2cDeviceConfigs.extend( newConfigs )

   def addOutgoingSlotConfigs( self, newConfigs ):
      self.outgoingSlotConfigs.extend( newConfigs )

   def addPciDeviceConfigs( self, newConfigs ):
      self.pciDeviceConfigs.extend( newConfigs )

   def addEmbeddedSensorConfigs( self, newConfigs ):
      self.embeddedSensorConfigs.extend( newConfigs )

   def populateSymlinkToDevicePaths( self, platform ):
      addedPaths = { 
         **self.generateFpgaSymlinks( platform ), 
         **self.generateI2cAdapterSymlinks( platform ),
         **self.generateEepromSymlinks( platform ),
         **self.generateGpiochipSymlinks(),
         **self.generateSensorCpldSymlinks( platform ),
         **self.generatePsuBusSymlinks(),
         **self.generateXcvrSymlinks(),
         **self.generateFlashSymlinks()
      }
      self.symlinkToDevicePaths.update( addedPaths )

   def addSymlinkToDevicePaths( self, newPaths ):
      self.symlinkToDevicePaths.update( newPaths )

   def generateI2cAdapterSymlinks( self, platform ):
      symlinkDict = OrderedDict()
      if self.pciDeviceConfigs:
         adapterConfigs = [ config for pciConfig in self.pciDeviceConfigs
                            if pciConfig.i2cAdapterConfigs 
                            for config in pciConfig.i2cAdapterConfigs ]
         for i, adapterConfig in enumerate( adapterConfigs ):
            for adapterNo in range( adapterConfig.numberOfAdapters ):
               if self.pmUnitName == "SCM":
                  basePath = "/run/devmap/i2c-busses/MERU_SCM_CPLD_SMBUS"
                  symlinkDict[ f"{ basePath }{ i }_CH{ adapterNo }" ] = (
                     f"/[{ adapterConfig.pmUnitScopedName }@{ adapterNo }]" )
               elif self.pmUnitName == "SMB":
                  if platform == "meru800bia":
                     basePath = "/run/devmap/i2c-busses/MERU800BIA_SMB_FPGA_SMBUS"
                     symlinkDict[ f"{ basePath }{ i }_CH{ adapterNo }" ] = (
                        f"/SMB_SLOT@0/[{ adapterConfig.pmUnitScopedName }@"
                        f"{ adapterNo }]" )
                  elif platform == "meru800bfa":
                     basePath = "/run/devmap/i2c-busses/MERU800BFA_SMB"
                     devName = adapterConfig.pmUnitScopedName.split( '_', 2 )[ 1 ]
                     symlinkDict[ 
                        f"{ basePath }_{ devName }_SMBUS"
                        f"{ adapterConfig.pmUnitScopedName[ -1 ] }_CH{ adapterNo }" 
                     ] = ( f"/SMB_SLOT@0/[{ adapterConfig.pmUnitScopedName }@"
                           f"{ adapterNo }]" )
      return symlinkDict
   
   def generateSensorCpldSymlinks( self, platform ):
      symlinkDict = OrderedDict()
      if self.pmUnitName == "SCM":
         basePath = "/run/devmap/sensors/CPU"
         if self.embeddedSensorConfigs:
            for config in self.embeddedSensorConfigs:
               name = config.pmUnitScopedName
               symlinkDict[ f"{ basePath }_{ name.split( '_', 1 )[ 1 ]}" ] = (
                  f"/[{ name }]" 
               )
         if self.i2cDeviceConfigs:
            for config in self.i2cDeviceConfigs:
               name = config.pmUnitScopedName
               if "IDPROM" in name or "PCA" in name:
                  continue
               symlinkDict[ f"{ basePath }_{ name.split( '_', 1 )[ 1 ]}" ] = (
                  f"/[{ name }]"
               )
      elif self.pmUnitName == "SMB":
         basePath = "/run/devmap/sensors/"
         if self.embeddedSensorConfigs:
            for config in self.embeddedSensorConfigs:
               name = config.pmUnitScopedName
               symlinkDict[ f"{ basePath }{ name }" ] = f"/SMB_SLOT@0/[{ name }]"
         if self.i2cDeviceConfigs:
            for config in self.i2cDeviceConfigs:
               name = config.pmUnitScopedName
               if "IDPROM" in name or "PCA" in name:
                  continue
               if name == "SMB_CPLD":
                  symlinkDict[ 
                     f"/run/devmap/cplds/{ platform.upper() }_SMB_CPLD" 
                  ] = "/SMB_SLOT@0/[SMB_CPLD]"
                  continue
               if "FAN" in name and "CPLD" in name:
                  if platform == "meru800bia":
                     symlinkDict[ "/run/devmap/cplds/FAN_CPLD" ] = (
                        "/SMB_SLOT@0/FAN_CPLD"
                     )
                     symlinkDict[ "/run/devmap/sensors/FAN_CPLD" ] = (
                        "/SMB_SLOT@0/FAN_CPLD"
                     )
                  elif platform == "meru800bfa":
                     fanNumIdx = name.find( "FAN" ) + 3
                     symlinkDict[ f"/run/devmap/cplds/{ name }" ] = (
                        f"/SMB_SLOT@0/[{ name }]"
                     )
                     symlinkDict[ 
                        f"/run/devmap/sensors/FAN_CPLD{ name[ fanNumIdx ] }" 
                     ] = f"/SMB_SLOT@0/[{ name }]"
               else:
                  symlinkDict[ f"{ basePath }{ name }" ] = f"/SMB_SLOT@0/[{ name }]"
      return symlinkDict
   
   def generateXcvrSymlinks( self ):
      symlinkDict = {}
      if self.pciDeviceConfigs:
         for pciConfig in self.pciDeviceConfigs:
            if pciConfig.xcvrCtrlConfigs:
               for xcvrConfig in pciConfig.xcvrCtrlConfigs:
                  portNumber = xcvrConfig.portNumber
                  portType = xcvrConfig.portType
                  symlinkDict[ f"/run/devmap/xcvrs/xcvr_{ portNumber }" ] = (
                     f"/SMB_SLOT@0/[{ portType.upper() }_PORT{ portNumber }_XCVR]" 
                  )
      symlinkDict = OrderedDict(
         sorted(
            symlinkDict.items(), 
            key=lambda x: int( re.search( r'\d+', x[ 0 ] ).group() )
         )
      )
      return symlinkDict

   def generateFpgaSymlinks( self, platform ):
      symlinkDict = OrderedDict()
      if self.pciDeviceConfigs:
         for pciConfig in self.pciDeviceConfigs:
            if self.pmUnitName == "SCM":
               symlinkDict[ "/run/devmap/fpgas/MERU_SCM_CPLD" ] = (
                  f"/[{ pciConfig.pmUnitScopedName }]"
               )
            elif self.pmUnitName == "SMB":
               symlinkDict[ 
                  f"/run/devmap/fpgas/{ platform.upper() }_"
                  f"{ pciConfig.pmUnitScopedName }"
               ] = f"/SMB_SLOT@0/[{ pciConfig.pmUnitScopedName }]"
      return symlinkDict
   
   def generateEepromSymlinks( self, platform ):
      symlinkDict = OrderedDict()
      if self.i2cDeviceConfigs:
         if self.pmUnitName == "SCM":
            for config in self.i2cDeviceConfigs:
               name = config.pmUnitScopedName
               if "IDPROM" in name:
                  symlinkDict[ 
                     f"/run/devmap/eeproms/MERU_SCM_EEPROM_"
                     f"{ name.split( '_' )[ -1 ] }" 
                  ] = f"/[{ name }]"
            for slotConfig in self.outgoingSlotConfigs:
               if platform == "meru800bia":
                  symlinkDict[ 
                     f"/run/devmap/eeproms/{ platform.upper() }_SMB_EEPROM"
                  ] = f"/{ slotConfig.slotName }/[SMB_IDPROM]"
               elif platform == "meru800bfa":
                  symlinkDict[ 
                     f"/run/devmap/eeproms/{ platform.upper() }_SMB_EEPROM"
                  ] = f"/{ slotConfig.slotName }/[IDPROM]"
      return symlinkDict
   
   def generateGpiochipSymlinks( self ):
      symlinkDict = OrderedDict()
      if self.i2cDeviceConfigs:
         for config in self.i2cDeviceConfigs:
            name = config.pmUnitScopedName
            if "PCA" in name:
               symlinkDict[ f"/run/devmap/gpiochips/{ name }" ] = (
                  f"/SMB_SLOT@0/[{ name }]"
               )
      return symlinkDict

   def generatePsuBusSymlinks( self ):
      symlinkDict = OrderedDict()
      if self.pmUnitName == "SMB":
         if self.outgoingSlotConfigs:
            for slotConfig in self.outgoingSlotConfigs:
               if slotConfig.slotType == "PSU_SLOT":
                  name = slotConfig.slotName
                  portNum = int( name[ -1 ] ) + 1
                  symlinkDict[ f"/run/devmap/sensors/PSU{ portNum }_PMBUS" ] = (
                     f"/SMB_SLOT@0/{ name }/[PSU_PMBUS]"
                  )
      return symlinkDict
   
   def generateFlashSymlinks( self ):
      symlinkDict = OrderedDict()
      if self.pciDeviceConfigs:
         spiMasterConfigs = [ config for pciConfig in self.pciDeviceConfigs
                              if pciConfig.spiMasterConfigs 
                              for config in pciConfig.spiMasterConfigs ]
         for spiMasterConfig in spiMasterConfigs:
            if spiMasterConfig.spiDeviceConfigs:
               for config in spiMasterConfig.spiDeviceConfigs:
                  symlinkDict[ 
                     f"/run/devmap/flashes/{ config.pmUnitScopedName }" 
                  ] = f"/SMB_SLOT@0/[{ config.pmUnitScopedName }]"
      return symlinkDict
   
   def asJson( self ):
      name = self.pmUnitName
      pluggedInSlotType = f'{name}_SLOT'

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
      list = []
      for config in self.embeddedSensorConfigs:
         list.append( config.asJson() )
      return list
   
   def getI2cDeviceConfigsList( self ):
      list = []
      for config in self.i2cDeviceConfigs:
         list.append( config.asJson() )
      return list
   
   def getOutgoingSlotConfigsDict( self ):
      jsonDict = {}
      for config in self.outgoingSlotConfigs:
         slotName = config.slotName
         jsonDict[ slotName ] = config.asJson()
      return jsonDict
   
   def getPciDeviceConfigsList( self ):
      list = []
      for config in self.pciDeviceConfigs:
         list.append( config.asJson() )
      return list
   

class EmbeddedSensorConfig:
   def __init__( self, pmUnitScopedName, sysfsPath ):
      self.pmUnitScopedName = pmUnitScopedName
      self.sysfsPath = sysfsPath

   def asJson( self ):

      assert self.pmUnitScopedName and self.sysfsPath, (
         "missing details in EmbeddedSensorsConfig"
      )

      return {
         "pmUnitScopedName": self.pmUnitScopedName,
         "sysfsPath": self.sysfsPath
      }
   

class I2cDeviceConfig:
   def __init__( self, busName, address, kernelDeviceName, pmUnitScopedName,
                 isGpioChip=False, hasBmcMac=False, hasCpuMac=False, 
                 hasSwitchAsicMac=False, hasReservedMac=False,
                 numOutgoingChannels=None, initRegSettings=None ):
      self.busName = busName
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


class InitRegSettings:
   def __init__( self, offsetBufPairs ):
      self.list = []
      for regOffset, ioBuf in offsetBufPairs:
         self.list.append( { "regOffset": regOffset, "ioBuf": [ ioBuf ] } )


class SlotConfig:
   def __init__( self, slotName, presenceFileName=None, presenceDevicePath=None, 
                 outgoingI2cBusNames=None ):
      self.slotName = slotName
      self.slotType = slotName.split( "@" )[ 0 ] 
      self.presenceFileName = presenceFileName
      self.presenceDevicePath = presenceDevicePath
      self.outgoingI2cBusNames = outgoingI2cBusNames

   def asJson( self ):
      slotType = self.slotType
      presenceDevicePath = self.presenceDevicePath
      presenceFileName = self.presenceFileName
      outgoingI2cBusNames = self.outgoingI2cBusNames

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
                 subSystemDeviceId, i2cAdapterConfigs=None, spiMasterConfigs=None, 
                 ledCtrlConfigs=None, xcvrCtrlConfigs=None ):
      self.pmUnitScopedName = pmUnitScopedName
      self.vendorId = vendorId
      self.deviceId = deviceId
      self.subSystemVendorId = subSystemVendorId
      self.subSystemDeviceId = subSystemDeviceId
      self.i2cAdapterConfigs = i2cAdapterConfigs or []
      self.spiMasterConfigs = spiMasterConfigs or []
      self.ledCtrlConfigs = ledCtrlConfigs or []
      self.xcvrCtrlConfigs = xcvrCtrlConfigs or []

   def addI2cAdapterConfigs( self, numAdapters, adapterBaseName, baseCsrOffset ):
      configs = []
      numFormatSpecifiers = adapterBaseName.count( '{}' )
      for i in range( numAdapters ):
         if numFormatSpecifiers == 2:
            deviceNum = self.pmUnitScopedName[ -1 ]
            adapterName = adapterBaseName.format( deviceNum, i )
         elif numFormatSpecifiers == 1:
            adapterName = adapterBaseName.format( i )
         else:
            adapterName = adapterBaseName
         csrOffset = hex( int( baseCsrOffset, 16 ) + i * 0x80 )
         configs.append( 
            I2cAdapterConfig( adapterName, "i2c_master", -1, csrOffset, 8 )
         )
      self.i2cAdapterConfigs.extend( configs )

   def addSpiMasterConfigs( self, newConfigs ):
      self.spiMasterConfigs.extend( newConfigs )

   def addXcvrCtrlConfigs( self, numConfigs, basePortNumber, portType="osfp", 
                           xcvrBaseOffset="0xA010", led1BaseOffset="0x6100", 
                           led2BaseOffset="0x6110", led3BaseOffset=None, 
                           led4BaseOffset=None, whistler=False ):
      if whistler:
         newConfigs = enumerateXcvrConfigsWhistler( numConfigs, basePortNumber, 
                                                    portType, xcvrBaseOffset, 
                                                    led1BaseOffset, led2BaseOffset, 
                                                    led3BaseOffset, led4BaseOffset )
      else:
         newConfigs = enumerateXcvrConfigsViper( numConfigs, basePortNumber, 
                                                 portType, xcvrBaseOffset, 
                                                 led1BaseOffset, led2BaseOffset, 
                                                 led3BaseOffset, led4BaseOffset )
      self.xcvrCtrlConfigs.extend( newConfigs )

   def addLedCtrlConfigs( self, newConfigs ):
      self.ledCtrlConfigs.extend( newConfigs )

   def asJson( self ):
      pmUnitScopedName = self.pmUnitScopedName
      vendorId = self.vendorId
      deviceId = self.deviceId
      subSystemVendorId = self.subSystemVendorId
      subSystemDeviceId = self.subSystemDeviceId

      assert pmUnitScopedName and vendorId and deviceId and subSystemVendorId\
            and subSystemDeviceId, "missing details in PciDeviceConfigs"

      return {
         "pmUnitScopedName": pmUnitScopedName,
         "vendorId": vendorId,
         "deviceId": deviceId,
         "subSystemVendorId": subSystemVendorId,
         "subSystemDeviceId": subSystemDeviceId,
         "i2cAdapterConfigs": self.getI2cAdapterConfigsList(),
         "spiMasterConfigs": self.getSpiMasterConfigsList(),
         "ledCtrlConfigs": self.getLedCtrlConfigsList(),
         "xcvrCtrlConfigs": self.getXcvrConfigsList()
      }
   
   def getI2cAdapterConfigsList( self ):
      list = []
      for config in self.i2cAdapterConfigs:
         list.append( config.asJson() )
      return list
   
   def getSpiMasterConfigsList( self ):
      list = []
      for config in self.spiMasterConfigs:
         list.append( config.asJson() )
      return list
   
   def getLedCtrlConfigsList( self ):
      list = []
      for config in self.xcvrCtrlConfigs:
         portLeds = [ *config.parseXcvrLeds() ]
         for led in portLeds:
            list.append( led )

      for identifier, config in enumerate( self.ledCtrlConfigs ):
         list.append( config.parseStatusLeds( identifier+1 ) )
      
      return list
   
   def getXcvrConfigsList( self ):
      list = []
      for config in self.xcvrCtrlConfigs:
         list.append( config.parseConfig() )
      return list


class I2cAdapterConfig:
   def __init__( self, pmUnitScopedName, deviceName, iobufOffset, 
                 csrOffset, numberOfAdapters ):
      self.pmUnitScopedName = pmUnitScopedName
      self.deviceName = deviceName
      self.iobufOffset = iobufOffset
      self.csrOffset = csrOffset
      self.numberOfAdapters = numberOfAdapters

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
      self.spiDeviceConfigs = spiDeviceConfigs

   def asJson( self ):
      pmUnitScopedName = self.pmUnitScopedName
      deviceName = self.deviceName
      iobufOffset = str( self.iobufOffset ).lower()
      csrOffset = str( self.csrOffset ).lower()
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
            "csrOffset": csrOffset
         },
         **({ "spiDeviceConfigs": [ config.dict for config in spiDeviceConfigs ] }
            if spiDeviceConfigs else {}),
      }


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

   def parseXcvrLeds( self ):
      returnList = []
      portNumber = self.portNumber
      portType = self.portType
      ledList = []
      for i in range( 1, 5 ):
         attribute = f"led{i}Offset"
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
      name = self.ledName.upper()
      offset = self.offset.lower()

      assert name and offset, "missing details in status leds"
      
      led = {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": name,
            "deviceName": f"{ name[ :3 ].lower() }_led",
            "csrOffset": offset
         },
         "portNumber": -1,
         "ledId": identifier
      }
   
      return led


def enumerateXcvrConfigsViper( numConfigs, basePortNumber, portType, 
                               xcvrBaseOffset, led1BaseOffset, led2BaseOffset, 
                               led3BaseOffset=None, led4BaseOffset=None ):
   configs = []
   for i in range( numConfigs ):
      xcvrCtrlOffset = hex( int( xcvrBaseOffset, 16 ) + i * 0x10 )
      led1Off = hex( int( led1BaseOffset, 16 ) + i * 0x20 )
      led2Off = hex( int( led2BaseOffset, 16 ) + i * 0x20 )
      led3Off = None
      if led3BaseOffset:
         led3Off = hex( int( led3BaseOffset, 16 ) + i * 0x20 )
      led4Off = None
      if led4BaseOffset:
         led4Off = hex( int( led4BaseOffset, 16 ) + i * 0x20 )
      configs.append( 
         XcvrConfig(
            portNumber=basePortNumber + i,
            portType=portType,
            xcvrCtrlOffset=xcvrCtrlOffset,
            led1Offset=led1Off,
            led2Offset=led2Off,
            led3Offset=led3Off if led3Off else None,
            led4Offset=led4Off if led4Off else None
         )
      )
   return configs


def enumerateXcvrConfigsWhistler( numConfigs, basePortNumber, portType, 
                                  xcvrBaseOffset, led1BaseOffset, led2BaseOffset, 
                                  led3BaseOffset=None, led4BaseOffset=None ):
   configs = []
   currIndex = basePortNumber
   for i in range( numConfigs ):
      xcvrCtrlOffset = hex( int( xcvrBaseOffset, 16 ) + i * 0x10 )
      led1Off = hex( int( led1BaseOffset, 16 ) + i * 0x20 )
      led2Off = hex( int( led2BaseOffset, 16 ) + i * 0x20 )
      led3Off = None
      if led3BaseOffset:
         led3Off = hex( int( led3BaseOffset, 16 ) + i * 0x20 )
      led4Off = None
      if led4BaseOffset:
         led4Off = hex( int( led4BaseOffset, 16 ) + i * 0x20 )
      configs.append( 
         XcvrConfig(
            portNumber=currIndex,
            portType=portType,
            xcvrCtrlOffset=xcvrCtrlOffset,
            led1Offset=led1Off,
            led2Offset=led2Off,
            led3Offset=led3Off if led3Off else None,
            led4Offset=led4Off if led4Off else None
         )
      )
      if currIndex % 4 == 0:
         currIndex += 4
      currIndex += 1
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

      self.addI2cDeviceConfigs( [
         I2cDeviceConfig( "SCM_I2C_MASTER0@0", "0x40", "pmbus", "SCM_MPS_PMBUS" ),
         I2cDeviceConfig( "SCM_I2C_MASTER0@1", "0x50", "24c512", "SCM_IDPROM_P1", 
                          hasCpuMac=True ),
         I2cDeviceConfig( "SCM_I2C_MASTER0@2", "0x30", "pxm1310", "SCM_PXM1310_1" ),
         I2cDeviceConfig( "SCM_I2C_MASTER0@2", "0x3e", "pxe1610", "SCM_PXE1211" ),
         I2cDeviceConfig( "SCM_I2C_MASTER0@2", "0x40", "pxm1310", "SCM_PXM1310_2" )
      ] )

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="SMB_SLOT@0",
            outgoingI2cBusNames=[ "SCM_I2C_MASTER1@0", 
                                  "SCM_I2C_MASTER1@2",
                                  "SCM_I2C_MASTER1@3" ]
         )
      ] )

      self.addPciDeviceConfigs( [
         *enumeratePciDeviceConfigs( 1, "SCM_FPGA", "0x3475", "0x0001", "0x3475", 
                                     "0x0008" )
      ] )

      self.pciDeviceConfigs[ 0 ].addI2cAdapterConfigs( 2, "SCM_I2C_MASTER{}", 
                                                       "0x8000" )
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


class FANUnit( PmUnitConfig ):
   def __init__( self ):
      super().__init__( "FAN" )