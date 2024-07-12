# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from collections import OrderedDict
import re


class PlatformConfig:
   def __init__( self, platformName, rootPmUnitName="SCM", slotTypeConfigs=None,
                 pmUnitConfigs=None, i2cAdaptersFromCpu=None, kmodsSettings=None ):
      self.platformName = platformName
      self.rootPmUnitName = rootPmUnitName
      self.slotTypeConfigs = slotTypeConfigs
      self.pmUnitConfigs = pmUnitConfigs
      if i2cAdaptersFromCpu:
         self.i2cAdaptersFromCpu = i2cAdaptersFromCpu
      else:
         self.i2cAdaptersFromCpu =[ { "adapter" : "SMBus I801 adapter at 1000" } ]
      if kmodsSettings:
         self.kmodsSettings = kmodsSettings
      else:
         self.kmodsSettings = {
            "bspKmodsRpmName": "arista_bsp_kmods",
            "bspKmodsRpmVersion": "0.7.2-1",
            "bspKmodsToReload" : 
               "scd-xcvr, scd-spi, scd-leds, scd-smbus, dsf-fan-cpld",
            "sharedKmodsToReload": "scd",
            "upstreamKmodsToLoad": "spidev, i2c-i801" 
         }

   def addSlotTypeConfigs( self, newConfigs ):
      if self.slotTypeConfigs:
         self.slotTypeConfigs = [ *self.slotTypeConfigs, *newConfigs ]
      else:
         self.slotTypeConfigs = newConfigs

   def addPmUnitConfigs( self, newConfigs ):
      if self.pmUnitConfigs:
         self.pmUnitConfigs = [ *self.pmUnitConfigs, *newConfigs ]
      else:
         self.pmUnitConfigs = newConfigs


class PmUnitConfig:
   def __init__( self, pmUnitName, i2cDeviceConfigs=None, outgoingSlotConfigs=None, 
                 pciDeviceConfigs=None, embeddedSensorConfigs=None, 
                 symlinkToDevicePaths=None ):
      self.pmUnitName = pmUnitName
      self.i2cDeviceConfigs = i2cDeviceConfigs
      self.outgoingSlotConfigs = outgoingSlotConfigs
      self.pciDeviceConfigs = pciDeviceConfigs
      self.embeddedSensorConfigs = embeddedSensorConfigs
      self.symlinkToDevicePaths = symlinkToDevicePaths

   def addI2cDeviceConfigs( self, newConfigs ):
      if self.i2cDeviceConfigs:
         self.i2cDeviceConfigs = [ *self.i2cDeviceConfigs, *newConfigs ]
      else:
         self.i2cDeviceConfigs = newConfigs

   def addOutgoingSlotConfigs( self, newConfigs ):
      if self.outgoingSlotConfigs:
         self.outgoingSlotConfigs = [ *self.outgoingSlotConfigs, *newConfigs ]
      else:
         self.outgoingSlotConfigs = newConfigs

   def addPciDeviceConfigs( self, newConfigs ):
      if self.pciDeviceConfigs:
         self.pciDeviceConfigs = [ *self.pciDeviceConfigs, *newConfigs ]
      else:
         self.pciDeviceConfigs = newConfigs

   def addEmbeddedSensorConfigs( self, newConfigs ):
      if self.embeddedSensorConfigs:
         self.embeddedSensorConfigs = [ *self.embeddedSensorConfigs, *newConfigs ]
      else:
         self.embeddedSensorConfigs = newConfigs

   def populateSymlinkToDevicePaths( self, platform="meru800bia" ):
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
      if self.symlinkToDevicePaths:
         self.symlinkToDevicePaths = {
            **self.symlinkToDevicePaths,
            **addedPaths
         }
      else:
         self.symlinkToDevicePaths = addedPaths

   def addSymlinkToDevicePaths( self, newPaths ):
      if self.symlinkToDevicePaths:
         self.symlinkToDevicePaths = {
            **self.symlinkToDevicePaths,
            **newPaths
         }
      else:
         self.symlinkToDevicePaths = newPaths

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
                        f"{adapterConfig.pmUnitScopedName[-1]}_CH{adapterNo}" 
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
                  f"{pciConfig.pmUnitScopedName}"
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
                  ] = f"/{slotConfig.slotName}/[SMB_IDPROM]"
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


class InitRegSettings:
   def __init__( self, offsetBufPairs ):
      self.list = []
      for regOffset, ioBuf in offsetBufPairs:
         self.list.append( { "regOffset": regOffset, "ioBuf": [ ioBuf ] } )


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


class SlotConfig:
   def __init__( self, slotName, presenceFileName=None, presenceDevicePath=None, 
                 outgoingI2cBusNames=None ):
      self.slotName = slotName
      self.slotType = slotName.split("@")[ 0 ] 
      self.presenceFileName = presenceFileName
      self.presenceDevicePath = presenceDevicePath
      self.outgoingI2cBusNames = outgoingI2cBusNames


class PciDeviceConfig:
   def __init__( self, pmUnitScopedName, vendorId, deviceId, subSystemVendorId,
                 subSystemDeviceId, i2cAdapterConfigs=None, spiMasterConfigs=None, 
                 ledCtrlConfigs=None, xcvrCtrlConfigs=None ):
      self.pmUnitScopedName = pmUnitScopedName
      self.vendorId = vendorId
      self.deviceId = deviceId
      self.subSystemVendorId = subSystemVendorId
      self.subSystemDeviceId = subSystemDeviceId
      self.i2cAdapterConfigs = i2cAdapterConfigs
      self.spiMasterConfigs = spiMasterConfigs
      self.ledCtrlConfigs = ledCtrlConfigs
      self.xcvrCtrlConfigs = xcvrCtrlConfigs

   def addI2cAdapterConfigs( self, numAdapters, adapterBaseName, baseCsrOffset ):
      configs = []
      adapterStarCount = adapterBaseName.count( '*' )
      for i in range( numAdapters ):
         if adapterStarCount == 2:
            pos = adapterBaseName.find( '*' )
            rpos = adapterBaseName.rfind( '*' )
            deviceNum = self.pmUnitScopedName[ -1 ]
            adapterName = (
               f"{ adapterBaseName[ :pos ] }{ deviceNum }"
               f"{ adapterBaseName[ pos+1:rpos ]}{ i }{ adapterBaseName[ rpos+1: ]}"
            )
         elif adapterStarCount == 1:
            pos = adapterBaseName.find( '*' )
            adapterName = (
               f"{ adapterBaseName[ :pos ] }{ i }"
               f"{ adapterBaseName[ pos+1: ] }"
            )
         else:
            adapterName = adapterBaseName
         csrOffset = hex( int( baseCsrOffset, 16 ) + i * 0x80 )
         configs.append( 
            I2cAdapterConfig( adapterName, "i2c_master", -1, csrOffset, 8 )
         )
      if self.i2cAdapterConfigs:
         self.i2cAdapterConfigs = [ *self.i2cAdapterConfigs, *configs ]
      else:
         self.i2cAdapterConfigs = configs

   def addSpiMasterConfigs( self, newConfigs ):
      if self.spiMasterConfigs:
         self.spiMasterConfigs = [ *self.spiMasterConfigs, *newConfigs ]
      else:
         self.spiMasterConfigs = newConfigs

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
      if self.xcvrCtrlConfigs:
         self.xcvrCtrlConfigs = [ *self.xcvrCtrlConfigs, *newConfigs ]
      else:
         self.xcvrCtrlConfigs = newConfigs

   def addLedCtrlConfigs( self, newConfigs ):
      if self.ledCtrlConfigs:
         self.ledCtrlConfigs = [ *self.ledCtrlConfigs, *newConfigs ]
      else:
         self.ledCtrlConfigs = newConfigs


class I2cAdapterConfig:
   def __init__( self, pmUnitScopedName, deviceName, iobufOffset, 
                 csrOffset, numberOfAdapters ):
      self.pmUnitScopedName = pmUnitScopedName
      self.deviceName = deviceName
      self.iobufOffset = iobufOffset
      self.csrOffset = csrOffset
      self.numberOfAdapters = numberOfAdapters


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


class SpiMasterConfig:
   def __init__( self, pmUnitScopedName, deviceName, iobufOffset, 
                 csrOffset, spiDeviceConfigs=None ):
      self.pmUnitScopedName = pmUnitScopedName
      self.deviceName = deviceName
      self.iobufOffset = iobufOffset
      self.csrOffset = csrOffset
      self.spiDeviceConfigs = spiDeviceConfigs


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


class LedConfig:
   def __init__( self, ledName, offset ):
      self.ledName = ledName
      self.offset = offset


class EmbeddedSensorConfig:
   def __init__( self, pmUnitScopedName, sysfsPath ):
      self.pmUnitScopedName = pmUnitScopedName
      self.sysfsPath = sysfsPath

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
      if '*' in generalPath:
         pos = generalPath.find( '*' )
         presenceDevicePath = (
            f"{ generalPath[ :pos ]}{ i // 4 }{ generalPath[ pos+1: ] }"
         )
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
      if '*' in deviceBaseName:
         pos = deviceBaseName.find( '*' )
         deviceName = f"{ deviceBaseName[ :pos ] }{ i }{ deviceBaseName[ pos+1: ] }"
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

      self.pciDeviceConfigs[ 0 ].addI2cAdapterConfigs( 2, "SCM_I2C_MASTER*", 
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