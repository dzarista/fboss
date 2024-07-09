# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from collections import OrderedDict


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
      self.pmUnitName = slotName.split('_')[0]


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
                outgoingI2cBusNames=[] ):
      self.slotName = slotName
      self.slotType = slotName.split("@")[0]
      self.presenceFileName = presenceFileName
      self.presenceDevicePath = presenceDevicePath
      self.outgoingI2cBusNames = outgoingI2cBusNames


class PciDeviceConfig:
   def __init__( self, pmUnitScopedName, vendorId, deviceId, subSystemVendorId,
                subSystemDeviceId ):
      self.pmUnitScopedName = pmUnitScopedName
      self.vendorId = vendorId
      self.deviceId = deviceId
      self.subSystemVendorId = subSystemVendorId
      self.subSystemDeviceId = subSystemDeviceId


class I2cAdapterConfig:
   def __init__( self, name, pmUnitScopedName, deviceName, iobufOffset, 
                csrOffset, numberOfAdapters ):
      self.name = name
      self.pmUnitScopedName = pmUnitScopedName
      self.deviceName = deviceName
      self.iobufOffset = iobufOffset
      self.csrOffset = csrOffset
      self.numberOfAdapters = numberOfAdapters


class SpiDeviceConfig:
   def __init__( self, pmUnitScopedName, chipSelect, modalias, maxSpeedHz ):
      self.dict = {
         "pmUnitScopedName": pmUnitScopedName,
         "chipSelect": chipSelect,
         "modalias": modalias,
         "maxSpeedHz": maxSpeedHz
      }


class SpiMasterConfig:
   def __init__( self, name, pmUnitScopedName, deviceName, iobufOffset, 
                csrOffset, spiDeviceConfigs=None ):
      self.name = name
      self.pmUnitScopedName = pmUnitScopedName
      self.deviceName = deviceName
      self.iobufOffset = iobufOffset
      self.csrOffset = csrOffset
      self.spiDeviceConfigs = spiDeviceConfigs


class XcvrConfig:
   def __init__( self, name, portNumber, portType,	xcvrCtrlOffset, led1Offset, \
                led2Offset, led3Offset, led4Offset ):
      self.name = name
      self.portNumber = portNumber
      self.portType = portType
      self.xcvrCtrlOffset = xcvrCtrlOffset
      self.led1Offset = led1Offset
      self.led2Offset = led2Offset
      self.led3Offset = led3Offset
      self.led4Offset = led4Offset


class LedConfig:
   def __init__( self, name, ledName, offset ):
      self.name = name
      self.ledName = ledName
      self.offset = offset


class EmbeddedSensorConfig:
   def __init__( self, pmUnitScopedName, sysfsPath ):
      self.pmUnitScopedName = pmUnitScopedName
      self.sysfsPath = sysfsPath


def enumerateXcvrConfigsViper( numConfigs, name, basePortNumber, portType, xcvrBaseOffset, 
                         led1BaseOffset, led2BaseOffset,led3BaseOffset=None, 
                         led4BaseOffset=None ):
   configs = []
   for i in range( numConfigs ):
      xcvrCtrlOffset = hex( int( xcvrBaseOffset, 16 ) + i * int( "0x10", 16 ) )
      led1Off = hex( int( led1BaseOffset, 16 ) + i * int( "0x20", 16 ) )
      led2Off = hex( int( led2BaseOffset, 16 ) + i * int( "0x20", 16 ) )
      led3Off = None
      if led3BaseOffset:
         led3Off = hex( int( led3BaseOffset, 16 ) + i * int( "0x20", 16 ) )
      led4Off = None
      if led4BaseOffset:
         led4Off = hex( int( led4BaseOffset, 16 ) + i * int( "0x20", 16 ) )
      configs.append( XcvrConfig(
         name=name,
         portNumber=basePortNumber + i,
         portType=portType,
         xcvrCtrlOffset=xcvrCtrlOffset,
         led1Offset=led1Off,
         led2Offset=led2Off,
         led3Offset=led3Off if led3Off else None,
         led4Offset=led4Off if led4Off else None
         ) )
   return configs


def enumerateXcvrConfigsWhistler( numDevices, configsPerDevice, baseDeviceName, 
                                 portType, xcvrBaseOffset, led1BaseOffset, 
                                 led2BaseOffset, led3BaseOffset=None, led4BaseOffset=None ):
   configs = []
   starPos = baseDeviceName.find('*')
   for i in range( numDevices ):
      if i % 2 == 0:
         baseIndex = i * configsPerDevice + 1
      else:
         baseIndex = (i - 1) * configsPerDevice + 4 + 1
      deviceName = f"{baseDeviceName[:starPos]}{i}{baseDeviceName[starPos+1:]}"
      currIndex = baseIndex
      for j in range( configsPerDevice ):
         xcvrCtrlOffset = hex( int( xcvrBaseOffset, 16 ) + j * int( "0x10", 16 ) )
         led1Off = hex( int( led1BaseOffset, 16 ) + j * int( "0x20", 16 ) )
         led2Off = hex( int( led2BaseOffset, 16 ) + j * int( "0x20", 16 ) )
         led3Off = None
         if led3BaseOffset:
            led3Off = hex( int( led3BaseOffset, 16 ) + j * int( "0x20", 16 ) )
         led4Off = None
         if led4BaseOffset:
            led4Off = hex( int( led4BaseOffset, 16 ) + j * int( "0x20", 16 ) )
         configs.append( XcvrConfig(
            name=deviceName,
            portNumber=currIndex,
            portType=portType,
            xcvrCtrlOffset=xcvrCtrlOffset,
            led1Offset=led1Off,
            led2Offset=led2Off,
            led3Offset=led3Off if led3Off else None,
            led4Offset=led4Off if led4Off else None
            ) )
         if currIndex % 4 == 0:
            currIndex += 4
         currIndex += 1

   configs.sort(key=lambda x: x.portNumber)
   return configs


def generateI2cAdapterSymlinks( i2cAdapterConfig, pmUnit, platform="Viper" ):
   symlinkToDevicePaths = OrderedDict()
   pathPrefix = ""
   if pmUnit == "SCM":
      basePath = "/run/devmap/i2c-busses/MERU_SCM_CPLD_SMBUS"
   elif pmUnit == "SMB":
      if platform == "Viper":
         basePath = "/run/devmap/i2c-busses/MERU800BIA_SMB_FPGA_SMBUS"
      elif platform == "Whistler":
         basePath = "/run/devmap/i2c-busses/MERU800BFA_"
      pathPrefix = "/SMB_SLOT@0"
   for i, config in enumerate( i2cAdapterConfig ):
      for adapterNum in range( config.numberOfAdapters ):
         if platform == "Viper":
            symlinkToDevicePaths[ f"{basePath}{i}_CH{adapterNum}" ] = \
               f"{pathPrefix}/[{config.pmUnitScopedName}@{adapterNum}]"
         elif platform == "Whistler":
            symlinkToDevicePaths[ f"{basePath}{config.name}_SMBUS{config.pmUnitScopedName[-1]}_CH{adapterNum}" ] = \
               f"{pathPrefix}/[{config.pmUnitScopedName}@{adapterNum}]"
   return symlinkToDevicePaths


def generateSensorSymlinks( embeddedSensorsConfig, i2cDeviceConfig, pmUnit ):
   symlinkToDevicePaths = OrderedDict()
   if pmUnit == "SCM":
      basePath = "/run/devmap/sensors/CPU_"
      for config in embeddedSensorsConfig:
         name = config.pmUnitScopedName
         symlinkToDevicePaths[ f"{basePath}{name.split('_', 1)[1]}" ] = f"/[{ name }]"
      for config in i2cDeviceConfig:
         name = config.pmUnitScopedName
         if "IDPROM" in name or "PCA" in name:
            continue
         symlinkToDevicePaths[ f"{basePath}{name.split('_', 1)[1]}" ] = f"/[{ name }]"
   elif pmUnit == "SMB":
      basePath = "/run/devmap/sensors/"
      for config in embeddedSensorsConfig:
         name = config.pmUnitScopedName
         symlinkToDevicePaths[ f"{ basePath }{ name }" ] = f"/SMB_SLOT@0/[{ name }]"
      for config in i2cDeviceConfig:
         name = config.pmUnitScopedName
         if "IDPROM" in name or "PCA" in name:
            continue
         symlinkToDevicePaths[ f"{ basePath }{ name }" ] = f"/SMB_SLOT@0/[{ name }]"
   return symlinkToDevicePaths


def generateXcvrSymlinks( xcvrConfigList ):
   symlinkToDevicePaths = OrderedDict()
   for config in xcvrConfigList:
      portNumber = config.portNumber
      portType = config.portType
      symlinkToDevicePaths[ f"/run/devmap/xcvrs/xcvr_{portNumber}" ] = \
         f"/SMB_SLOT@0/[{portType.upper()}_PORT{portNumber}_XCVR]"
   return symlinkToDevicePaths


def enumerateFANSlotConfigs( numConfigs, generalPath ):
   configs = []
   for i in range( numConfigs ):
      if '*' in generalPath:
         pos = generalPath.find('*')
         presenceDevicePath = \
            f"{generalPath[:pos]}{i // 4}{generalPath[pos+1:]}"
      else:
         presenceDevicePath = generalPath
      configs.append( SlotConfig(
         slotName=f"FAN_SLOT@{i}",
         presenceFileName=f"fan{(i % 4) + 1}_present",
         presenceDevicePath=presenceDevicePath
      ) )
   return configs


def enumeratePciDeviceConfigs( numConfigs, deviceBaseName, vendorId, \
                              deviceId, subSystemVendorId, subSystemBaseDeviceId ):
   configs = []
   for i in range( numConfigs ):
      if '*' in deviceBaseName:
         pos = deviceBaseName.find('*')
         deviceName = f"{deviceBaseName[:pos]}{i}{deviceBaseName[pos+1:]}"
      else:
         deviceName = deviceBaseName
      configs.append( PciDeviceConfig(
         pmUnitScopedName=deviceName,
         vendorId=vendorId,
         deviceId=deviceId,
         subSystemVendorId=subSystemVendorId,
         subSystemDeviceId=hex( int( subSystemBaseDeviceId, 16 ) + i )
      ))
   return configs


def enumerateI2cAdapterConfigs( numDevices, numAdapters, deviceBaseName, \
                               adapterBaseName, baseCsrOffset ):
   configs = []
   deviceStarCount = deviceBaseName.count('*')
   adapterStarCount = adapterBaseName.count('*')
   for i in range( numDevices ):
      if deviceStarCount == 1:
         pos = deviceBaseName.find('*')
         deviceName = f"{deviceBaseName[:pos]}{i}{deviceBaseName[pos+1:]}"
      else:
         deviceName = deviceBaseName
      for j in range( numAdapters ):
         if adapterStarCount == 2:
            pos = adapterBaseName.find('*')
            rpos = adapterBaseName.rfind('*')
            adapterName = \
               f"{adapterBaseName[:pos]}{i}{adapterBaseName[pos+1:rpos]}{j}{adapterBaseName[rpos+1:]}"
         elif adapterStarCount == 1:
            pos = adapterBaseName.find('*')
            adapterName = f"{adapterBaseName[:pos]}{j}{adapterBaseName[pos+1:]}"
         else:
            adapterName = adapterBaseName
         csrOffset = hex( int( baseCsrOffset, 16 ) + j * int( "0x80", 16 ) )
         configs.append( I2cAdapterConfig( deviceName, adapterName, "i2c_master", \
                                          -1, csrOffset, 8 ) )
   return configs


def enumerateSpiMasterConfigs( pciDeviceConfigs ):
   configs = []
   for entity in pciDeviceConfigs:
      name = entity.pmUnitScopedName
      configs.append( SpiMasterConfig( name, "SMB_SPI_MASTER0", "spi_master", -1, 
                        "0x7900",
                        spiDeviceConfigs=[ SpiDeviceConfig(
                           pmUnitScopedName="SMB_SPI_MASTER0_DEVICE1",
                           chipSelect=0,
                           modalias="spidev",
                           maxSpeedHz=25000000
                        ) ] ) )
   return configs

