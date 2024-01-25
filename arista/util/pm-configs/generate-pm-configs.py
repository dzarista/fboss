# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

'''
Script to generate an FBOSS OSS Platform Manager JSON config file from a Google Spreadsheet.

Thrift model found here:
https://github.com/facebook/fboss/blob/main/fboss/platform/platform_manager/platform_manager_config.thrift
'''

from ArGoogleApps import SpreadsheetLibV4 as SsLib
from collections import OrderedDict
import json
import sys

def sheetToDicts( ss, sheet_name ):
   # Helper function to parse a sheet into a list of dicts
   sheet = ss.sheet( sheet_name )
   cols = sheet.getColumns()

   dicts = []
   for row in sheet.getRows():
      row_dict = { col: row.get( col ) for col in cols }
      dicts.append( row_dict )

   return dicts

class BaseConfigs:
   def __init__( self, spId ):
      service = SsLib.Service()
      ss = service.getSpreadsheet( spId, sheetType=SsLib.SheetType.keyless )

      self.platformConfigsDict = sheetToDicts( ss, "PlatformConfig" )
      self.slotTypeConfigsDict = sheetToDicts( ss, "slotTypeConfigs" )
      self.pmUnitConfigsDict = sheetToDicts( ss, "pmUnitConfigs" )
      self.pciDeviceConfigsDict = sheetToDicts( ss, "pciDeviceConfigs" )
      self.i2cAdapterConfigsDict = sheetToDicts( ss, "i2cAdapterConfigs" )
      self.spiMasterConfigsDict = sheetToDicts( ss, "SpiMasterConfigs" )
      self.xcvrConfigsDict = sheetToDicts( ss, "XcvrConfigs" )
      self.ledConfigsDict = sheetToDicts( ss, "LedConfigs" )
      self.i2cDeviceConfigsDict = sheetToDicts( ss, "i2cDeviceConfigs" )
      self.outgoingSlotConfigsDict = sheetToDicts( ss, "outgoingSlotConfigs" )
      self.i2cAdaptersFromCpuDict = sheetToDicts( ss, "i2cAdaptersFromCpu" )
      self.symbolicLinkToDevicePathDict = \
         sheetToDicts( ss, "symbolicLinkToDevicePath" )
      self.kmodsSettingsDict = sheetToDicts( ss, "KmodsSettings" )

   def dumpJson( self, jsonDict ):
      return json.dumps( jsonDict, indent=3 )
   
   def filterEntities( self, name, entities ):
      return [ entity for entity in entities if entity.get("name") == name ]

class PlatformConfigs( BaseConfigs ):
   '''Models a PlatformConfig JSON object.'''

   def __init__( self, spreadsheetId ):
      configs = BaseConfigs( spreadsheetId )
      
      self.entities = configs.platformConfigsDict

      self.platformName = self.entities[ 0 ].get( "platformName" )
      self.rootPmUnitName = self.entities[ 0 ].get( "rootPmUnitName" )
      assert self.platformName and self.rootPmUnitName,\
         "platformName and rootPmUnitName are required"

      self.slotTypeConfigs = SlotTypeConfigs( configs )
      self.pmUnitConfigs = PmUnitConfigs( configs )
      self.i2cAdaptersFromCpu = I2cAdaptersFromCpu( configs )
      self.symbolicLinkToDevicePath = SymbolicLinkToDevicePath( configs )
      self.kmodsSettings = configs.kmodsSettingsDict[ 0 ]

   def asJson( self ):
      jsonDict = OrderedDict()
      jsonDict[ "platformName" ] = self.platformName
      jsonDict[ "rootPmUnitName" ] = self.rootPmUnitName
      jsonDict[ "slotTypeConfigs" ] = self.slotTypeConfigs.getDict()
      jsonDict[ "pmUnitConfigs" ] = self.pmUnitConfigs.getDict()
      jsonDict[ "i2cAdaptersFromCpu" ] = self.i2cAdaptersFromCpu.getList()
      jsonDict[ "symbolicLinkToDevicePath" ] = \
         self.symbolicLinkToDevicePath.getDict()
      jsonDict[ "bspKmodsRpmName" ] = self.kmodsSettings["bspKmodsRpmName"]
      jsonDict[ "bspKmodsRpmVersion" ] = \
         str( self.kmodsSettings["bspKmodsRpmVersion"] )
      jsonDict[ "kmodsToReload" ] = self.kmodsSettings["kmodsToReload"].split(", ")

      return self.dumpJson( jsonDict )


class SlotTypeConfigs( BaseConfigs ):
   def __init__( self, configs ):
      self.entities = configs.slotTypeConfigsDict
      self.jsonDict = OrderedDict()
      for entity in self.entities:
         name = entity.get( "name" )
         self.jsonDict[name] = self.parseSlotConfig( entity )

   def parseSlotConfig( self, entity ):
      numOutgoingI2cBuses = entity.get( "numOutgoingI2cBuses" )
      pmUnitName = entity.get( "pmUnitName" )
      idpCfg = self.parseIdpromConfig( entity )

      assert numOutgoingI2cBuses is not None, "numOutgoingI2cBuses is required"

      return {
         "numOutgoingI2cBuses": numOutgoingI2cBuses,
         **({ "idpromConfig": idpCfg } if idpCfg and all( idpCfg.values() ) else {}),
         **({ "pmUnitName": pmUnitName } if pmUnitName else {})
      }

   def parseIdpromConfig( self, entity ):
      busName = entity.get( "idpromConfigBusName" )
      address = entity.get( "idpromConfigAddress" )
      kernelDeviceName = entity.get( "idpromConfigKernelDeviceName" )
      assert ( busName == address == kernelDeviceName ) or\
         ( busName and address and kernelDeviceName ),\
            "Error: 1 or 2 of the strings are empty"

      return {
         "busName": busName,
         "address": address.lower() if address else '',
         "kernelDeviceName": kernelDeviceName
      }

   def getDict( self ):
      return self.jsonDict

   def asJson( self ):
      return self.dumpJson( self.jsonDict )


class PmUnitConfigs( BaseConfigs ):
   def __init__( self, configs ):
      self.entities = configs.pmUnitConfigsDict
      self.jsonDict = OrderedDict()
      for entity in self.entities:
         name = entity.get( "name" )
         self.jsonDict[name] = self.parsePmUnitConfig( entity, configs )

   def parsePmUnitConfig( self, entity, configs):
      name = entity.get( "name" )
      pluggedInSlotType = entity.get( "pluggedInSlotType" )
      outgoingSlotConfigs = OutgoingSlotConfigs( configs, name )

      assert name and pluggedInSlotType, "name and pluggedInSlotType are required"

      return {
         "pluggedInSlotType": pluggedInSlotType,
         "i2cDeviceConfigs": I2cDeviceConfigs( configs, name ).getList(),
         "outgoingSlotConfigs": outgoingSlotConfigs.getDict(),
         "pciDeviceConfigs": PciDeviceConfigs( configs, name ).getList()
      }

   def getDict( self ):
      return self.jsonDict

   def asJson( self ):
      return self.dumpJson( self.jsonDict )


class I2cDeviceConfigs( BaseConfigs ):
   def __init__( self, configs, nameFilter ):
      self.entities = configs.i2cDeviceConfigsDict
      self.entities = configs.filterEntities( nameFilter, self.entities )
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseI2cDeviceConfigs( entity ) )

   def parseI2cDeviceConfigs( self, entity ):
      busName = entity.get( "busName" )
      address = entity.get( "address" )
      kernelDeviceName = entity.get( "kernelDeviceName" )
      pmUnitScopedName = entity.get( "pmUnitScopedName" )
      deviceType = entity.get( "deviceType" )
      numOutgoingChannels = entity.get( "numOutgoingChannels" )
      hasBmcMac = entity.get( "hasBmcMac" )
      hasCpuMac = entity.get( "hasCpuMac" )
      hasSwitchAsicMac = entity.get( "hasSwitchAsicMac" )
      hasReservedMac = entity.get( "hasReservedMac" )
      isGpioChip = entity.get( "isGpioChip" )

      assert busName and address and kernelDeviceName and pmUnitScopedName\
            , "missing required details in I2cDeviceConfigs"

      return {
         "busName": busName,
         "address": address.lower(),
         "kernelDeviceName": kernelDeviceName,
         "pmUnitScopedName": pmUnitScopedName,
         **({ "deviceType": deviceType } if deviceType else {}),
         **({ "numOutgoingChannels": numOutgoingChannels }\
            if numOutgoingChannels else {}),
         **({ "hasBmcMac": bool( hasBmcMac ) } if hasBmcMac else {}),
         **({ "hasCpuMac": bool( hasCpuMac ) } if hasCpuMac else {}),
         **({ "hasSwitchAsicMac": hasSwitchAsicMac } if hasSwitchAsicMac else {}),
         **({ "hasReservedMac": hasReservedMac } if hasReservedMac else {}),
         **({ "isGpioChip": isGpioChip } if isGpioChip else {})
      }

   def getList( self ):
      return self.list


class OutgoingSlotConfigs( BaseConfigs ):
   def __init__( self, configs, nameFilter ):
      self.entities = configs.outgoingSlotConfigsDict
      self.entities = configs.filterEntities( nameFilter, self.entities )
      self.jsonDict = OrderedDict()
      for entity in self.entities:
         slotName = entity.get( "slotName" )
         self.jsonDict[slotName] = self.parseOutgoingSlotConfigs( entity )

   def parseOutgoingSlotConfigs( self, entity ):
      slotType = entity.get( "slotType" )
      presenceDevicePath = entity.get( "presenceDevicePath" )
      presenceFileName = entity.get( "presenceFileName" )
      outgoingI2cBusNames = entity.get( "outgoingI2cBusNames" )

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
         "outgoingI2cBusNames": json.loads( outgoingI2cBusNames )\
              if outgoingI2cBusNames else []
      }

   def getDict( self ):
      return self.jsonDict


class PciDeviceConfigs( BaseConfigs ):
   def __init__( self, configs, nameFilter ):
      self.entities = configs.pciDeviceConfigsDict
      self.entities = configs.filterEntities( nameFilter, self.entities )
      self.list = []
      for entity in self.entities:
         self.list.append( self.parsePciDeviceConfigs( entity, configs ) )

   def parsePciDeviceConfigs( self, entity, configs ):
      pmUnitScopedName = entity.get( "pmUnitScopedName" )
      vendorId = entity.get( "vendorId" )
      deviceId = entity.get( "deviceId" )
      subSystemVendorId = entity.get( "subSystemVendorId" )
      subSystemDeviceId = entity.get( "subSystemDeviceId" )

      assert pmUnitScopedName and vendorId and deviceId and subSystemVendorId\
            and subSystemDeviceId, "missing details in PciDeviceConfigs"

      return {
         "pmUnitScopedName": pmUnitScopedName,
         "vendorId": vendorId,
         "deviceId": deviceId,
         "subSystemVendorId": subSystemVendorId,
         "subSystemDeviceId": subSystemDeviceId,
         "i2cAdapterConfigs": \
            I2cAdapterConfigs( configs, pmUnitScopedName ).getList(),
         "spiMasterConfigs": SpiMasterConfigs( configs, pmUnitScopedName ).getList(),
         "ledCtrlConfigs": LedCtrlConfigs( configs, pmUnitScopedName ).getList(),
         "xcvrCtrlConfigs": XcvrCtrlConfigs( configs, pmUnitScopedName ).getList()
      }

   def getList( self ):
      return self.list


class I2cAdapterConfigs( BaseConfigs ):
   def __init__( self, configs, nameFilter ):
      self.entities = configs.i2cAdapterConfigsDict
      self.entities = configs.filterEntities( nameFilter, self.entities )
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseI2cAdapterConfigs( entity ) )

   def parseI2cAdapterConfigs( self, entity ):
      pmUnitScopedName = entity.get( "pmUnitScopedName" )
      deviceName = entity.get( "deviceName" )
      iobufOffset = str( entity.get( "iobufOffset" ) ).lower()
      csrOffset = str( entity.get( "csrOffset" ) ).lower()
      numberOfAdapters = entity.get( "numberOfAdapters" )

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
   def __init__( self, configs, nameFilter ):
      self.entities = configs.spiMasterConfigsDict
      self.entities = configs.filterEntities( nameFilter, self.entities )
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseSpiMasterConfigs( entity ) )

   def parseSpiMasterConfigs( self, entity ):
      pmUnitScopedName = entity.get( "pmUnitScopedName" )
      deviceName = entity.get( "deviceName" )
      iobufOffset = str( entity.get( "iobufOffset" ) ).lower()
      csrOffset = str( entity.get( "csrOffset" ) ).lower()
      numberOfCsPins = entity.get( "numberOfCsPins" )

      assert pmUnitScopedName and deviceName and iobufOffset and csrOffset\
            and numberOfCsPins is not None, "missing details in SpiMasterConfigs"
      
      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": pmUnitScopedName,
            "deviceName": deviceName,
            **({ "iobufOffset": str( int( iobufOffset, 16 ) ) }\
               if iobufOffset and iobufOffset != "-1" else {}),            
            "csrOffset": csrOffset
         },
         "numberOfCsPins": numberOfCsPins
      }

   def getList( self ):
      return self.list


class LedCtrlConfigs( BaseConfigs ):
   def __init__( self, configs, nameFilter ):
      self.list = []
      self.entities = configs.filterEntities( nameFilter, configs.xcvrConfigsDict )
      for entity in self.entities:
         portLeds = [ *self.parseXcvrLeds( entity ) ]
         for led in portLeds:
            self.list.append( led )

      self.entities = configs.filterEntities( nameFilter, configs.ledConfigsDict )
      for entity in self.entities :
         self.list.append( self.parseStatusLeds( entity ) )

   def parseXcvrLeds( self, entity ):
      returnList = []
      portNumber = entity.get( "portNumber" )
      portType = entity.get( "portType" )
      ledList = [led for i in range( 1, 5 )\
                 if (led := entity.get( f"led{i}Offset" ))]
      ledIdx = 1

      assert portNumber and portType and len( ledList ) >= 2,\
            "missing details in xcvr leds"
      
      for idx, ledOffset in enumerate( ledList ):
         returnList.append( {
            "fpgaIpBlockConfig": {
               "pmUnitScopedName": f'{portType}_PORT{portNumber}_LED{idx+1}'.upper(),
               "deviceName": f'{portType}_led',
               "csrOffset": ledOffset.lower()
            },
            "portNumber": portNumber,
            "ledId": ledIdx
         } )
         ledIdx += 1

      return returnList

   def parseStatusLeds( self, entity ):
      name = entity.get( "ledName" ).upper()
      offset = entity.get( "offset" ).lower()

      assert name and offset, "missing details in status leds"
      
      led = {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": name,
            "deviceName": 'status_led',
            "csrOffset": offset
         },
         "portNumber": -1,
         "ledId": 1
      }
   
      return led

   def getList( self ):
      return self.list


class XcvrCtrlConfigs( BaseConfigs ):
   def __init__( self, configs, nameFilter):
      self.entities = configs.xcvrConfigsDict
      self.entities = configs.filterEntities( nameFilter, self.entities )
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseXcvrCtrlConfig( entity ) )

   def parseXcvrCtrlConfig( self, entity ):
      portNumber = entity.get( "portNumber" )
      portType = entity.get( "portType" )
      xcvrCtrlOffset = entity.get( "xcvrCtrlOffset" ).lower()

      assert portNumber and portType and xcvrCtrlOffset,\
            "missing details in xcvr file"
         
      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": f'{portType}_PORT{portNumber}_XCVR'.upper(),
            "deviceName": f'{portType}_xcvr',
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


class SymbolicLinkToDevicePath( BaseConfigs ):
   def __init__( self, configs ):
      self.entities = configs.symbolicLinkToDevicePathDict
      self.jsonDict = OrderedDict()
      for entity in self.entities:
         symbolicLink = entity.get( "symbolicLink" )
         devicePath = entity.get( "devicePath" )
         self.jsonDict[symbolicLink] = devicePath

   def getDict( self ):
      return self.jsonDict


def main():
   if len( sys.argv ) < 2:
      print( f'Usage: {sys.argv[ 0 ]} <spreadsheet id>' )
      sys.exit( 1 )

   spreadsheetId = sys.argv[ 1 ]
   pmconfigs = PlatformConfigs( spreadsheetId )
   print( pmconfigs.asJson() )

if __name__ == '__main__':
   main()