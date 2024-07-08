# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

'''
Script to generate an FBOSS OSS Platform Manager JSON config file from a Python
hardware description file.

Thrift model found here:
https://github.com/facebook/fboss/blob/main/fboss/platform/platform_manager/platform_manager_config.thrift
'''

from collections import OrderedDict
import json
import sys

from Viper import Viper

class BaseConfigs:
   def __init__( self, hwDesc ):

      self.platformName = hwDesc.PLATFORM_NAME
      self.rootPmUnitName = hwDesc.ROOT_PM_UNIT_NAME      
      self.slotTypeConfigsDict = hwDesc.SLOT_TYPE_CONFIGS
      self.pmUnitConfigsList = hwDesc.PM_UNIT_CONFIGS
      self.i2cAdaptersFromCpuDict = hwDesc.I2C_ADAPTERS_FROM_CPU
      self.kmodsSettingsDict = hwDesc.KMODS_SETTINGS_DICT

   def dumpJson( self, jsonDict ):
      return json.dumps( jsonDict, indent=3 )


class PlatformConfig( BaseConfigs ):
   '''Models a PlatformConfig JSON object.'''

   def __init__( self, hwDesc ):
      configs = BaseConfigs( hwDesc )

      self.platformName = configs.platformName
      self.rootPmUnitName = configs.rootPmUnitName

      assert self.platformName and self.rootPmUnitName,\
         "platformName and rootPmUnitName are required"
      
      self.slotTypeConfigs = SlotTypeConfigs( configs )
      self.pmUnitConfigs = PmUnitConfigs( configs )
      self.i2cAdaptersFromCpu = I2cAdaptersFromCpu( configs )
      self.kmodsSettings = configs.kmodsSettingsDict

   def asJson( self ):
      jsonDict = OrderedDict()
      jsonDict[ "platformName" ] = self.platformName
      jsonDict[ "rootPmUnitName" ] = self.rootPmUnitName
      jsonDict[ "slotTypeConfigs" ] = self.slotTypeConfigs.getDict()
      jsonDict[ "pmUnitConfigs" ] = self.pmUnitConfigs.getDict()
      jsonDict[ "i2cAdaptersFromCpu" ] = self.i2cAdaptersFromCpu.getList()
      jsonDict[ "symbolicLinkToDevicePath" ] = \
         self.pmUnitConfigs.parseSymbolicLinkToDevicePaths()
      jsonDict[ "bspKmodsRpmName" ] = self.kmodsSettings["bspKmodsRpmName"]
      jsonDict[ "bspKmodsRpmVersion" ] = \
         str( self.kmodsSettings["bspKmodsRpmVersion"] )
      jsonDict[ "bspKmodsToReload" ] = \
         self.kmodsSettings["bspKmodsToReload"].split(", ")
      jsonDict[ "sharedKmodsToReload" ] = \
         self.kmodsSettings["sharedKmodsToReload"].split(", ")
      jsonDict[ "upstreamKmodsToLoad" ] = \
         self.kmodsSettings["upstreamKmodsToLoad"].split(", ")

      return self.dumpJson( jsonDict )


class SlotTypeConfigs( BaseConfigs ):
   def __init__( self, configs ):
      self.entities = configs.slotTypeConfigsDict
      self.jsonDict = OrderedDict()
      for entity in self.entities:
         name = entity.slotName
         self.jsonDict[name] = self.parseSlotConfig( entity )

   def parseSlotConfig( self, entity ):
      idpCfg = self.parseIdpromConfig( entity )

      assert entity.numOutgoingI2cBuses is not None, "numOutgoingI2cBuses is required"

      return {
         "numOutgoingI2cBuses": entity.numOutgoingI2cBuses,
         **({ "idpromConfig": idpCfg } if idpCfg and all( idpCfg.values() ) else {}),
         **({ "pmUnitName": entity.pmUnitName } if entity.pmUnitName else {})
      }

   def parseIdpromConfig( self, entity ):
      busName = entity.idPromConfigBusName
      address = entity.idPromConfigAddress
      kernelDeviceName = entity.idPromConfigKernelDeviceName
      offset = entity.idPromConfigOffset
      assert ( busName == address == kernelDeviceName ) or\
         ( busName and address and kernelDeviceName ),\
            "Error: 1 or 2 of the strings are empty"

      return {
         "busName": busName,
         "address": address.lower() if address else '',
         "kernelDeviceName": kernelDeviceName,
         "offset": offset
      }

   def getDict( self ):
      return self.jsonDict

   def asJson( self ):
      return self.dumpJson( self.jsonDict )


class PmUnitConfigs( BaseConfigs ):
   def __init__( self, configs ):
      self.entities = configs.pmUnitConfigsList
      self.jsonDict = OrderedDict()
      for pmUnit in self.entities:
         name = pmUnit.PM_UNIT_NAME
         self.jsonDict[name] = self.parsePmUnitConfig( pmUnit )

   def parsePmUnitConfig( self, pmUnit ):
      name = pmUnit.PM_UNIT_NAME
      pluggedInSlotType = f'{name}_SLOT'

      assert name and pluggedInSlotType, "name and pluggedInSlotType are required"

      embeddedSensorConfigs = EmbeddedSensorConfigs( pmUnit ).getList()

      return {
         "pluggedInSlotType": pluggedInSlotType,
         "i2cDeviceConfigs": I2cDeviceConfigs( pmUnit ).getList(),
         "outgoingSlotConfigs": OutgoingSlotConfigs( pmUnit ).getDict(),
         "pciDeviceConfigs": PciDeviceConfigs( pmUnit ).getList(),
         **( { "embeddedSensorConfigs": \
            embeddedSensorConfigs } if len( embeddedSensorConfigs ) > 0 else {} )
      }

   def parseSymbolicLinkToDevicePaths( self ):
      symlinkDict = {}
      for pmUnit in self.entities:
         pmUnitDict = pmUnit.SYMBOLIC_LINK_TO_DEVICE_PATH
         for symlink, devicePath in pmUnitDict.items():
            symlinkDict[symlink] = devicePath
      return symlinkDict

   def getDict( self ):
      return self.jsonDict

   def asJson( self ):
      return self.dumpJson( self.jsonDict )


class I2cDeviceConfigs( BaseConfigs ):
   def __init__( self, pmUnit ):
      self.entities = pmUnit.I2C_DEVICE_CONFIGS
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseI2cDeviceConfigs( entity ) )

   def parseI2cDeviceConfigs( self, entity ):
      busName = entity.busName
      address = entity.address
      kernelDeviceName = entity.kernelDeviceName
      pmUnitScopedName = entity.pmUnitScopedName
      numOutgoingChannels = entity.numOutgoingChannels
      hasBmcMac = entity.hasBmcMac
      hasCpuMac = entity.hasCpuMac
      hasSwitchAsicMac = entity.hasSwitchAsicMac
      hasReservedMac = entity.hasReservedMac
      isGpioChip = entity.isGpioChip
      initRegSettings = entity.initRegSettings

      assert busName and address and kernelDeviceName and pmUnitScopedName\
            , "missing required details in I2cDeviceConfigs"

      return {
         "busName": busName,
         "address": address.lower(),
         "kernelDeviceName": kernelDeviceName,
         "pmUnitScopedName": pmUnitScopedName,
         **({ "numOutgoingChannels": numOutgoingChannels }\
            if numOutgoingChannels else {}),
         **({ "hasBmcMac": bool( hasBmcMac ) } if hasBmcMac else {}),
         **({ "hasCpuMac": bool( hasCpuMac ) } if hasCpuMac else {}),
         **({ "hasSwitchAsicMac": hasSwitchAsicMac } if hasSwitchAsicMac else {}),
         **({ "hasReservedMac": hasReservedMac } if hasReservedMac else {}),
         **({ "isGpioChip": isGpioChip } if isGpioChip else {}),
         **({ "initRegSettings": initRegSettings.list } \
            if initRegSettings and initRegSettings.list else {})
      }

   def getList( self ):
      return self.list


class OutgoingSlotConfigs( BaseConfigs ):
   def __init__( self, pmUnit ):
      self.entities = pmUnit.OUTGOING_SLOT_CONFIGS
      self.jsonDict = OrderedDict()
      for entity in self.entities:
         slotName = entity.slotName
         self.jsonDict[slotName] = self.parseOutgoingSlotConfigs( entity )

   def parseOutgoingSlotConfigs( self, entity ):
      slotType = entity.slotType
      presenceDevicePath = entity.presenceDevicePath
      presenceFileName = entity.presenceFileName
      outgoingI2cBusNames = entity.outgoingI2cBusNames

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

   def getDict( self ):
      return self.jsonDict


class PciDeviceConfigs( BaseConfigs ):
   def __init__( self, pmUnit ):
      self.entities = pmUnit.PCI_DEVICE_CONFIGS
      self.list = []
      for entity in self.entities:
         self.list.append( self.parsePciDeviceConfigs( entity, pmUnit ) )

   def parsePciDeviceConfigs( self, entity, pmUnit ):
      pmUnitScopedName = entity.pmUnitScopedName
      vendorId = entity.vendorId
      deviceId = entity.deviceId
      subSystemVendorId = entity.subSystemVendorId
      subSystemDeviceId = entity.subSystemDeviceId

      assert pmUnitScopedName and vendorId and deviceId and subSystemVendorId\
            and subSystemDeviceId, "missing details in PciDeviceConfigs"

      return {
         "pmUnitScopedName": pmUnitScopedName,
         "vendorId": vendorId,
         "deviceId": deviceId,
         "subSystemVendorId": subSystemVendorId,
         "subSystemDeviceId": subSystemDeviceId,
         "i2cAdapterConfigs": \
            I2cAdapterConfigs( pmUnit ).getList(),
         "spiMasterConfigs": SpiMasterConfigs( pmUnit ).getList(),
         "ledCtrlConfigs": LedCtrlConfigs( pmUnit ).getList(),
         "xcvrCtrlConfigs": XcvrCtrlConfigs( pmUnit ).getList()
      }

   def getList( self ):
      return self.list


class EmbeddedSensorConfigs( BaseConfigs ):
   def __init__( self, pmUnit ):
      self.entities = pmUnit.EMBEDDED_SENSORS_CONFIGS
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseEmbeddedSensorsConfigs( entity ) )

   def parseEmbeddedSensorsConfigs( self, entity ):
      pmUnitScopedName = entity.pmUnitScopedName
      sysfsPath = entity.sysfsPath

      assert pmUnitScopedName and sysfsPath, \
         "missing details in EmbeddedSensorsConfig"

      return {
         "pmUnitScopedName": pmUnitScopedName,
         "sysfsPath": sysfsPath
      }

   def getList( self ):
      return self.list
   

class I2cAdapterConfigs( BaseConfigs ):
   def __init__( self, pmUnit ):
      self.entities = pmUnit.I2C_ADAPTER_CONFIGS
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseI2cAdapterConfigs( entity ) )

   def parseI2cAdapterConfigs( self, entity ):
      pmUnitScopedName = entity.pmUnitScopedName
      deviceName = entity.deviceName
      iobufOffset = str( entity.iobufOffset ).lower()
      csrOffset = str( entity.csrOffset ).lower()
      numberOfAdapters = entity.numberOfAdapters

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

   def getList( self ):
      return self.list


class SpiMasterConfigs( BaseConfigs ):
   def __init__( self, pmUnit ):
      self.entities = pmUnit.SPI_MASTER_CONFIGS
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseSpiMasterConfigs( entity ) )

   def parseSpiMasterConfigs( self, entity ):
      pmUnitScopedName = entity.pmUnitScopedName
      deviceName = entity.deviceName
      iobufOffset = str( entity.iobufOffset ).lower()
      csrOffset = str( entity.csrOffset ).lower()
      spiDeviceConfigs = entity.spiDeviceConfigs

      assert pmUnitScopedName and deviceName and csrOffset\
         is not None, "missing details in SpiMasterConfigs"
      
      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": pmUnitScopedName,
            "deviceName": deviceName,
            **({ "iobufOffset": str( int( iobufOffset, 16 ) ) }\
               if iobufOffset and iobufOffset != "-1" else {}),            
            "csrOffset": csrOffset
         },
         **({ "spiDeviceConfigs": [ config.dict for config in spiDeviceConfigs ] } \
            if spiDeviceConfigs else {}),
      }

   def getList( self ):
      return self.list


class LedCtrlConfigs( BaseConfigs ):
   def __init__( self, pmUnit ):
      self.list = []
      self.entities = pmUnit.XCVR_CONFIGS
      for entity in self.entities:
         portLeds = [ *self.parseXcvrLeds( entity ) ]
         for led in portLeds:
            self.list.append( led )

      self.entities = pmUnit.LED_CONFIGS
      for id, entity in enumerate( self.entities ):
         self.list.append( self.parseStatusLeds( entity, id+1 ) )

   def parseXcvrLeds( self, entity ):
      returnList = []
      portNumber = entity.portNumber
      portType = entity.portType
      ledList = []
      for i in range( 1, 5 ):
         attribute = f"led{i}Offset"
         if hasattr( entity, attribute ) and getattr( entity, attribute ):
            ledList.append( getattr( entity, attribute ) )
      ledIdx = 1

      assert portNumber and portType and len( ledList ) >= 2,\
            "missing details in xcvr leds"
      
      for idx, ledOffset in enumerate( ledList ):
         returnList.append( {
            "fpgaIpBlockConfig": {
               "pmUnitScopedName": f'{portType}_PORT{portNumber}_LED{idx+1}'.upper(),
               "deviceName": 'port_led',
               "csrOffset": ledOffset.lower()
            },
            "portNumber": portNumber,
            "ledId": ledIdx
         } )
         ledIdx += 1

      return returnList

   def parseStatusLeds( self, entity, id ):
      name = entity.ledName.upper()
      offset = entity.offset.lower()

      assert name and offset, "missing details in status leds"
      
      led = {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": name,
            "deviceName": f"{name[:3].lower()}_led",
            "csrOffset": offset
         },
         "portNumber": -1,
         "ledId": id
      }
   
      return led

   def getList( self ):
      return self.list


class XcvrCtrlConfigs( BaseConfigs ):
   def __init__( self, pmUnit ):
      self.entities = pmUnit.XCVR_CONFIGS
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseXcvrCtrlConfig( entity ) )

   def parseXcvrCtrlConfig( self, entity ):
      portNumber = entity.portNumber
      portType = entity.portType
      xcvrCtrlOffset = entity.xcvrCtrlOffset.lower()

      assert portNumber and portType and xcvrCtrlOffset,\
            "missing details in xcvr file"
         
      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": f'{portType}_PORT{portNumber}_XCVR'.upper(),
            "deviceName": 'xcvr_ctrl',
            "csrOffset": xcvrCtrlOffset
         },
         "portNumber": portNumber,
      }

   def getList( self ):
      return self.list


class I2cAdaptersFromCpu( BaseConfigs ):
   def __init__( self, configs ):
      self.entities = configs.i2cAdaptersFromCpuDict
      self.list = []
      for entity in self.entities:
         adapter = entity.get( "adapter" )
         self.list.append( adapter )

   def getList( self ):
      return self.list


def main():
   if len( sys.argv ) < 2:
      print( f'Usage: {sys.argv[ 0 ]} <platform_name>' )
      sys.exit( 1 )

   platformName = sys.argv[ 1 ]
   if platformName == 'Viper':
      pmconfigs = PlatformConfig( Viper )
      print( pmconfigs.asJson() )

if __name__ == '__main__':
   main()