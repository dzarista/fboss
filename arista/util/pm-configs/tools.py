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
   def __init__( self, pmUnitScopedName, vendorId, deviceId, subSustemVendorId,
                subSystemDeviceId ):
      self.pmUnitScopedName = pmUnitScopedName
      self.vendorId = vendorId
      self.deviceId = deviceId
      self.subSystemVendorId = subSustemVendorId
      self.subSystemDeviceId = subSystemDeviceId

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
   def __init__( self, portNumber, portType,	xcvrCtrlOffset, led1Offset, led2Offset,
                led3Offset, led4Offset ):
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

def enumerateXcvrConfigs( numConfigs, basePortNumber, portType, xcvrBaseOffset, 
                         led1BaseOffset, led2BaseOffset,led3BaseOffset=None, 
                         led4BaseOffset=None ):
   configs = []
   for i in range(numConfigs):
      xcvrCtrlOffset = hex( int( xcvrBaseOffset, 16 ) + i * int( "0x10", 16 ) )
      led1Off = hex( int( led1BaseOffset, 16 ) + i * int( "0x20", 16 ) )
      led2Off = hex( int( led2BaseOffset, 16 ) + i * int( "0x20", 16 ) )
      led3Off = None
      if led3BaseOffset:
         led3Off = hex( int( led3BaseOffset, 16 ) + i * int( "0x20", 16 ) )
      led4Off = None
      if led4BaseOffset:
         led4Off = hex( int( led4BaseOffset, 16 ) + i * int( "0x20", 16 ) )
      configs.append( XcvrConfig( portNumber=basePortNumber + i,
                                  portType=portType,
                                  xcvrCtrlOffset=xcvrCtrlOffset,
                                  led1Offset=led1Off,
                                  led2Offset=led2Off,
                                  led3Offset=led3Off if led3Off else None,
                                  led4Offset=led4Off if led4Off else None
                                 ) )
   return configs

def generateI2cAdapterSymlinks( i2cAdapterConfig, pmUnit ):
   symlinkToDevicePaths = OrderedDict()
   pathPrefix = ""
   if pmUnit == "SCM":
      basePath = "/run/devmap/i2c-busses/MERU_SCM_CPLD_SMBUS"
   elif pmUnit == "SMB":
      basePath = "/run/devmap/i2c-busses/MERU800BIA_SMB_FPGA_SMBUS"
      pathPrefix = "/SMB_SLOT@0"
   i2cAdapterList = i2cAdapterConfig[ f"{pmUnit}_FPGA" ]
   for i, config in enumerate( i2cAdapterList ):
      for adapterNum in range( config.numberOfAdapters ):
         symlinkToDevicePaths[ f"{basePath}{i}_CH{adapterNum}" ] = \
            f"{pathPrefix}/[{config.pmUnitScopedName}@{adapterNum}]"
   return symlinkToDevicePaths

def generateSensorSymlinks( embeddedSensorsConfig, i2cDeviceConfig, pmUnit ):
   symlinkToDevicePaths = OrderedDict()
   embeddedSensorsList = embeddedSensorsConfig[ pmUnit ] \
      if pmUnit in embeddedSensorsConfig.keys() else []
   i2cDeviceList = i2cDeviceConfig[ pmUnit ] \
      if pmUnit in i2cDeviceConfig.keys() else []
   if pmUnit == "SCM":
      basePath = "/run/devmap/sensors/CPU_"
      for config in embeddedSensorsList:
         name = config.pmUnitScopedName
         symlinkToDevicePaths[ f"{basePath}{name.split('_', 1)[1]}" ] = f"/[{ name }]"
      for config in i2cDeviceList:
         name = config.pmUnitScopedName
         if "IDPROM" in name or "PCA" in name:
            continue
         symlinkToDevicePaths[ f"{basePath}{name.split('_', 1)[1]}" ] = f"/[{ name }]"
   elif pmUnit == "SMB":
      basePath = "/run/devmap/sensors/"
      for config in embeddedSensorsList:
         name = config.pmUnitScopedName
         symlinkToDevicePaths[ f"{ basePath }{ name }" ] = f"/SMB_SLOT@0/[{ name }]"
      for config in i2cDeviceList:
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

