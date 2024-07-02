class SlotTypeConfig:
   def __init__( self, slotName, numOutgoingI2cBuses, 
                idPromConfigBusName=None, idPromConfigAddress=None,
                idpromConfigKernelDeviceName=None, idPromConfigOffset=None ):
      self.slotName = slotName
      self.numOutgoingI2cBuses = numOutgoingI2cBuses
      self.idPromConfigBusName = idPromConfigBusName
      self.idPromConfigAddress = idPromConfigAddress
      self.idPromConfigKernelDeviceName = idpromConfigKernelDeviceName
      self.idPromConfigOffset = idPromConfigOffset
      self.pmUnitName = slotName.split('_')[0]

class IdPromConfig:
   def __init__( self, busName, address, kernelDeviceName, offset ):
      self.busName = busName
      self.address = address
      self.kernelDeviceName = kernelDeviceName
      self.offset = offset

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
   def __init__( self, slotName, presenceFileName, presenceDevicePath, 
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

class SpiMasterConfig:
   def __init__( self, pmUnitScopedName, deviceName, iobufOffset, 
                csrOffset, numberOfCsPins ):
      self.pmUnitScopedName = pmUnitScopedName
      self.deviceName = deviceName
      self.iobufOffset = iobufOffset
      self.csrOffset = csrOffset
      self.numberOfCsPins = numberOfCsPins

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

def enumerateXcvrConfigs( basePortNumber, portType, xcvrBaseOffset, led1BaseOffset, 
                         led2BaseOffset, led3BaseOffset, led4BaseOffset, numConfigs ):
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



