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

def readSheetToListOfDicts( spreadsheet_id, sheet_name ):
   # Helper function to parse a sheet into a list of dicts
   service = SsLib.Service()
   ss = service.getSpreadsheet( spreadsheet_id, sheetType=SsLib.SheetType.keyless )
   sheet = ss.sheet( sheet_name )
   cols = sheet.getColumns()

   dicts = []
   for row in sheet.getRows():
      row_dict = { col: row.get( col ) for col in cols }
      dicts.append( row_dict )

   return dicts

class CsvConfigs:
   def __init__( self, spId, platformConfigsSheet, slotTypeConfigsSheet,
                pmUnitConfigsSheet, pciDeviceConfigsSheet, i2cAdapterConfigsSheet,
                SpiMasterConfigsSheet, xcvrConfigsSheet, ledConfigsSheet,
                i2cDeviceConfigsSheet, outgoingSlotConfigsSheet,
                i2cAdaptersFromCpuSheet, symbolicLinkToDevicePathSheet ):
      self.platformConfigs = readSheetToListOfDicts( spId, platformConfigsSheet )
      self.slotTypeConfigs = readSheetToListOfDicts( spId, slotTypeConfigsSheet )
      self.pmUnitConfigs = readSheetToListOfDicts( spId, pmUnitConfigsSheet )
      self.pciDeviceConfigs = readSheetToListOfDicts( spId, pciDeviceConfigsSheet )
      self.i2cAdapterConfigs = readSheetToListOfDicts( spId, i2cAdapterConfigsSheet )
      self.spiMasterConfigs = readSheetToListOfDicts( spId, SpiMasterConfigsSheet )
      self.xcvrConfigs = readSheetToListOfDicts( spId, xcvrConfigsSheet )
      self.ledConfigs = readSheetToListOfDicts( spId, ledConfigsSheet )
      self.i2cDeviceConfigs = readSheetToListOfDicts( spId, i2cDeviceConfigsSheet )
      self.outgoingSlotConfigs = \
         readSheetToListOfDicts( spId, outgoingSlotConfigsSheet )
      self.i2cAdaptersFromCpu = \
         readSheetToListOfDicts( spId, i2cAdaptersFromCpuSheet )
      self.symbolicLinkToDevicePath = \
         readSheetToListOfDicts( spId, symbolicLinkToDevicePathSheet )

   def dumpJson( self, jsonDict ):
      return json.dumps( jsonDict, indent=3 )
   
   def filterEntities( self, name, entities ):
      return [ entity for entity in entities if entity.get("name") == name ]

class PlatformConfigs( CsvConfigs ):
   '''Models a PlatformConfig JSON object.'''

   def __init__( self, spreadsheetId ):
      self.csv = CsvConfigs( spreadsheetId, "PlatformConfig", "slotTypeConfigs",
                            "pmUnitConfigs", "pciDeviceConfigs", "i2cAdapterConfigs",
                            "SpiMasterConfigs", "XcvrConfigs", "LedConfigs",
                            "i2cDeviceConfigs", "outgoingSlotConfigs",
                            "i2cAdaptersFromCpu", "symbolicLinkToDevicePath" )
      self.entities = self.csv.platformConfigs

      self.platformName = self.entities[ 0 ].get( "platformName" )
      self.rootPmUnitName = self.entities[ 0 ].get( "rootPmUnitName" )
      assert self.platformName and self.rootPmUnitName,\
         "platformName and rootPmUnitName are required"

      self.slotTypeConfigs = SlotTypeConfigs( self )
      self.pmUnitConfigs = PmUnitConfigs( self )
      self.i2cAdaptersFromCpu = I2cAdaptersFromCpu( self )
      self.symbolicLinkToDevicePath = SymbolicLinkToDevicePath( self )

   def asJson( self ):
      jsonDict = OrderedDict()
      jsonDict[ "platformName" ] = self.platformName
      jsonDict[ "rootPmUnitName" ] = self.rootPmUnitName
      jsonDict[ "slotTypeConfigs" ] = self.slotTypeConfigs.getDict()
      jsonDict[ "pmUnitConfigs" ] = self.pmUnitConfigs.getDict()
      jsonDict[ "i2cAdaptersFromCpu" ] = self.i2cAdaptersFromCpu.getList()
      jsonDict[ "symbolicLinkToDevicePath" ] = \
         self.symbolicLinkToDevicePath.getDict()

      return self.dumpJson( jsonDict )


class SlotTypeConfigs( PlatformConfigs ):
   def __init__( self, config ):
      self.entities = config.csv.slotTypeConfigs
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
         "address": address,
         "kernelDeviceName": kernelDeviceName
      }

   def getDict( self ):
      return self.jsonDict

   def asJson( self ):
      return self.dumpJson( self.jsonDict )


class PmUnitConfigs( PlatformConfigs ):
   def __init__( self, config ):
      self.entities = config.csv.pmUnitConfigs
      self.jsonDict = OrderedDict()
      for entity in self.entities:
         name = entity.get( "name" )
         self.jsonDict[name] = self.parsePmUnitConfig( entity, config )

   def parsePmUnitConfig( self, entity, config):
      name = entity.get( "name" )
      pluggedInSlotType = entity.get( "pluggedInSlotType" )
      outgoingSlotConfigs = OutgoingSlotConfigs( config, name )

      assert name and pluggedInSlotType, "name and pluggedInSlotType are required"

      return {
         "pluggedInSlotType": pluggedInSlotType,
         "i2cDeviceConfigs": I2cDeviceConfigs( config, name ).getList(),
         "outgoingSlotConfigs": outgoingSlotConfigs.getDict(),
         "pciDeviceConfigs": PciDeviceConfigs( config, name ).getList()
      }

   def getDict( self ):
      return self.jsonDict

   def asJson( self ):
      return self.dumpJson( self.jsonDict )


class I2cDeviceConfigs( PlatformConfigs ):
   def __init__( self, config, nameFilter ):
      self.entities = config.csv.i2cDeviceConfigs
      self.entities = config.csv.filterEntities( nameFilter, self.entities )
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

      assert busName and address and kernelDeviceName and pmUnitScopedName\
            , "missing required details in I2cDeviceConfigs"

      return {
         "busName": busName,
         "address": address,
         "kernelDeviceName": kernelDeviceName,
         "pmUnitScopedName": pmUnitScopedName,
         **({ "deviceType": deviceType } if deviceType else {}),
         **({ "numOutgoingChannels": numOutgoingChannels }\
            if numOutgoingChannels else {}),
         **({ "hasBmcMac": bool( hasBmcMac ) } if hasBmcMac else {}),
         **({ "hasCpuMac": bool( hasCpuMac ) } if hasCpuMac else {}),
         **({ "hasSwitchAsicMac": hasSwitchAsicMac } if hasSwitchAsicMac else {}),
         **({ "hasReservedMac": hasReservedMac } if hasReservedMac else {})
      }

   def getList( self ):
      return self.list


class OutgoingSlotConfigs( PlatformConfigs ):
   def __init__( self, config, nameFilter ):
      self.entities = config.csv.outgoingSlotConfigs
      self.entities = config.csv.filterEntities( nameFilter, self.entities )
      self.jsonDict = OrderedDict()
      for entity in self.entities:
         slotName = entity.get( "slotName" )
         self.jsonDict[slotName] = self.parseOutgoingSlotConfigs( entity )

   def parseOutgoingSlotConfigs( self, entity ):
      slotType = entity.get( "slotType" )
      presenceDetection = entity.get( "presenceDetection" )
      outgoingI2cBusNames = entity.get( "outgoingI2cBusNames" )

      assert slotType, "missing slotType in OutgoingSlotConfigs"

      return {
         "slotType": slotType,
         **({ "presenceDetection": json.loads( presenceDetection ) }\
             if presenceDetection else {}),
         "outgoingI2cBusNames": json.loads( outgoingI2cBusNames )\
              if outgoingI2cBusNames else []
      }

   def getDict( self ):
      return self.jsonDict


class PciDeviceConfigs( PlatformConfigs ):
   def __init__( self, config, nameFilter ):
      self.entities = config.csv.pciDeviceConfigs
      self.entities = config.csv.filterEntities( nameFilter, self.entities )
      self.list = []
      for entity in self.entities:
         self.list.append( self.parsePciDeviceConfigs( entity, config ) )

   def parsePciDeviceConfigs( self, entity, config ):
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
            I2cAdapterConfigs( config, pmUnitScopedName ).getList(),
         "spiMasterConfigs": SpiMasterConfigs( config, pmUnitScopedName ).getList(),
         "ledCtrlConfigs": LedCtrlConfigs( config, pmUnitScopedName ).getList(),
         "xcvrCtrlConfigs": XcvrCtrlConfigs( config, pmUnitScopedName ).getList()
      }

   def getList( self ):
      return self.list


class I2cAdapterConfigs( PlatformConfigs ):
   def __init__( self, config, nameFilter ):
      self.entities = config.csv.i2cAdapterConfigs
      self.entities = config.csv.filterEntities( nameFilter, self.entities )
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseI2cAdapterConfigs( entity ) )

   def parseI2cAdapterConfigs( self, entity ):
      pmUnitScopedName = entity.get( "pmUnitScopedName" )
      deviceName = entity.get( "deviceName" )
      iobufOffset = str( entity.get( "iobufOffset" ) )
      csrOffset = str( entity.get( "csrOffset" ) )
      numberOfAdapters = entity.get( "numberOfAdapters" )

      assert pmUnitScopedName and deviceName and iobufOffset and csrOffset\
            and numberOfAdapters, "missing details in I2cAdapterConfigs"
      
      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": pmUnitScopedName,
            "deviceName": deviceName,
            "iobufOffset": int( iobufOffset, 16 ),
            "csrOffset": int( csrOffset, 16 )
         },
         "numberOfAdapters": numberOfAdapters
      }

   def getList( self ):
      return self.list


class SpiMasterConfigs( PlatformConfigs ):
   def __init__( self, config, nameFilter ):
      self.entities = config.csv.spiMasterConfigs
      self.entities = config.csv.filterEntities( nameFilter, self.entities )
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseSpiMasterConfigs( entity ) )

   def parseSpiMasterConfigs( self, entity ):
      pmUnitScopedName = entity.get( "pmUnitScopedName" )
      deviceName = entity.get( "deviceName" )
      iobufOffset = str( entity.get( "iobufOffset" ) )
      csrOffset = str( entity.get( "csrOffset" ) )
      numberOfCsPins = entity.get( "numberOfCsPins" )

      assert pmUnitScopedName and deviceName and iobufOffset and csrOffset\
            and numberOfCsPins is not None, "missing details in SpiMasterConfigs"
      
      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": pmUnitScopedName,
            "deviceName": deviceName,
            "iobufOffset": int( iobufOffset, 16 ),
            "csrOffset": int( csrOffset, 16 )
         },
         "numberOfCsPins": numberOfCsPins
      }

   def getList( self ):
      return self.list


class LedCtrlConfigs( PlatformConfigs ):
   def __init__( self, config, nameFilter ):
      self.list = []
      self.ledId = 1
      self.entities = config.csv.filterEntities( nameFilter, config.csv.xcvrConfigs )
      for entity in self.entities:
         portLeds = [ *self.parseXcvrLeds( entity ) ]
         for led in portLeds:
            self.list.append( led )

      self.entities = config.csv.filterEntities( nameFilter, config.csv.ledConfigs )
      for entity in self.entities :
         self.list.append( self.parseStatusLeds( entity ) )

   def parseXcvrLeds( self, entity ):
      returnList = []
      portNumber = entity.get( "portNumber" )
      portType = entity.get( "portType" )
      ledList = [led for i in range( 1, 5 )\
                 if (led := entity.get( f"led{i}Offset" ))]

      assert portNumber and portType and len( ledList ) >= 2,\
            "missing details in xcvr leds"
      
      for idx, ledOffset in enumerate( ledList ):
         returnList.append( {
            "fpgaIpBlockConfig": {
               "pmUnitScopedName": f'{portType}_PORT{portNumber}_LED{idx+1}'.upper(),
               "deviceName": f'{portType}_led',
               "iobufOffset": -1,
               "csrOffset": int( ledOffset, 16 )
            },
            "portNumber": portNumber,
            "ledId": self.ledId
         } )
         self.ledId += 1
   
      return returnList

   def parseStatusLeds( self, entity ):
      name = entity.get( "ledName" )
      offset = entity.get( "offset" )

      assert name and offset, "missing details in status leds"
      
      led = {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": name.upper(),
            "deviceName": 'status_led',
            "iobufOffset": -1,
            "csrOffset": int( offset, 16 )
         },
         "portNumber": -1,
         "ledId": self.ledId
      }
      self.ledId += 1
   
      return led

   def getList( self ):
      return self.list


class XcvrCtrlConfigs( PlatformConfigs ):
   def __init__( self, config, nameFilter):
      self.entities = config.csv.xcvrConfigs
      self.entities = config.csv.filterEntities( nameFilter, self.entities )
      self.list = []
      for entity in self.entities:
         self.list.append( self.parseXcvrCtrlConfig( entity ) )

   def parseXcvrCtrlConfig( self, entity ):
      portNumber = entity.get( "portNumber" )
      portType = entity.get( "portType" )
      xcvrCtrlOffset = entity.get( "xcvrCtrlOffset" )

      assert portNumber and portType and xcvrCtrlOffset,\
            "missing details in xcvr file"
         
      return {
         "fpgaIpBlockConfig": {
            "pmUnitScopedName": f'{portType}_PORT{portNumber}_XCVR'.upper(),
            "deviceName": f'{portType}_xcvr',
            "iobufOffset": -1,
            "csrOffset": int( xcvrCtrlOffset, 16 )
         },
         "portNumber": portNumber,
      }

   def getList( self ):
      return self.list


class I2cAdaptersFromCpu( PlatformConfigs ):
   def __init__( self, config ):
      self.entities = config.csv.i2cAdaptersFromCpu
      self.list = []
      for entity in self.entities:
         adapter = entity.get( "adapter" )
         self.list.append( adapter )

   def getList( self ):
      return self.list


class SymbolicLinkToDevicePath( PlatformConfigs ):
   def __init__( self, config ):
      self.entities = config.csv.symbolicLinkToDevicePath
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