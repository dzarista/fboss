# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from ..BaseConfigs import (
   enumerateFANSlotConfigs,
   EmbeddedSensorConfig,
   FANUnit,
   FANCpld,
   GpioChip,
   I2cAdapterConfig,
   I2cDeviceConfig,
   I2cIdProm,
   LedConfig,
   PciDeviceConfig,
   PlatformConfig,
   PmUnitConfig,
   PSUUnit,
   Sensor,
   SensorConfig,
   SensorType,
   SlotConfig,
   Thresholds,
   SpiMasterConfig,
   Flash
)


class RookCpld( PciDeviceConfig ):
   def __init__( self ):
      super().__init__( 'ROOK_CPU_CPLD', '0x8086', '0x6f76', '0x0000', '0x0000',
                        symlinkDeviceName='ROOK_CPU_CPLD', symlinkDir='cplds' )
      self.addI2cAdapters()

   def addI2cAdapters( self ):
      baseAccelOffset = 0x8000
      accelStride = 0x80
      i2cAdapterConfigs = [
            I2cAdapterConfig( self, f'ROOK_SMBUS{accelNum}', 'i2c_master', -1,
                              hex( baseAccelOffset + accelNum * accelStride ), 4,
                              busSymlinkPrefix='ROOK_SMBUS' )
            # Accel 1 is unused and really shouldn't be here, but PM can't handle
            # non-contiguous adapters correctly (the adapter names are incorrect).
            for accelNum in [ 0, 1, 2, 3 ]
      ]
      self.i2cAdapterConfigs = i2cAdapterConfigs

   @property
   def cpuSmbusAccel( self ):
      return self.i2cAdapterConfigs[ 0 ]

   @property
   def switchcardSmbusAccel( self ):
      return self.i2cAdapterConfigs[ 2 ]

   @property
   def fancardSmbusAccel( self ):
      return self.i2cAdapterConfigs[ 3 ]


class RackhawkScd( PciDeviceConfig ):
   def __init__( self ):
      super().__init__( 'SCD_FPGA', '0x3475', '0x0001', '0x3475', '0x0002',
                        symlinkDeviceName='SCD_FPGA' )
      self.addI2cAdapters()
      self.addLeds()
      self.addSpiMasterConfigs( [
         SpiMasterConfig( "SCD_SPI_MASTER", "spi_master", -1,
                           "0x7900",
                           spiDeviceConfigs=[ Flash(
                              pmUnitScopedName="SCD_SPI_MASTER_DEVICE1",
                              chipSelect=0,
                              modalias="spidev",
                              maxSpeedHz=25000000
                           ) ]
                        )
      ] )
   def addI2cAdapters( self ):
      baseAccelOffset = 0x8000
      accelStride = 0x80
      self.i2cAdapterConfigs = [
            I2cAdapterConfig( self, f'SCD_SMBUS{accelNum}', 'i2c_master', -1,
                              hex( baseAccelOffset + accelNum * accelStride ), 8,
                              busSymlinkPrefix='SCD_SMBUS' )
            # Accel 0 is unused and really shouldn't be here, but PM can't handle
            # non-contiguous adapters correctly (the adapter names are incorrect).
            for accelNum in [ 0, 1 ]
      ]

   def addLeds( self ):
      self.addLedCtrlConfigs( [
         LedConfig( ledName='SYSTEM_STATUS_LED', offset='0x6050' ),
         LedConfig( ledName='FAN_STATUS_LED', offset='0x6060' ),
         LedConfig( ledName='PSU_STATUS_LED', offset='0x6070' ),
      ] )

   @property
   def switchcardSmbusAccel( self ):
      return self.i2cAdapterConfigs[ 1 ]


class BlackhawkCpld( I2cDeviceConfig ):
   def __init__( self, *args, **kwargs ):
      super().__init__( '0x23', 'blackhawk_cpld', 'BLACKHAWK_CPLD' )
      self.symlinkPath = f'/run/devmap/cplds/{self.pmUnitScopedName}'


class RackhawkSwitch( PmUnitConfig ):
   def __init__( self, hasPem=True ):
      super().__init__( 'SMB' )

      self.hasPem = hasPem
      self.setSlotTypeConfig( numOutgoingI2cBuses=0 )
      self.pciDevices = []
      self.i2cDevices = []

      # CPU card devices.
      self.cpuCpld = RookCpld()
      self.pciDevices.append( self.cpuCpld )
      self.addEmbeddedSensors()
      self.addCpuCardTempSensors()
      self.addCpuCardVrms()
      self.addCpuCardDpm()

      # Fan card devices.
      self.addFanCpld()

      # Switchcard devices.
      self.switchcardScd = RackhawkScd()
      self.pciDevices.append( self.switchcardScd )
      self.addSwitchcardCpld()
      self.addSwitchcardTempSensors()
      self.addSwitchcardDpm()
      self.addSwitchcardVrms()

      self.addPciDeviceConfigs( self.pciDevices )
      self.addI2cDeviceConfigs( self.i2cDevices )

      # Slots to Rackmon and PEM/PSU.
      outgoingSlotConfigs = [
         SlotConfig(
            slotName=f'RACKMON_SLOT@0',
            outgoingI2cBuses=[
               self.switchcardScd.switchcardSmbusAccel.buses[ 4 ]
            ]
         ),
         *enumerateFANSlotConfigs( 5, '/[FAN_CPLD]', fansPerCpld=5 )
      ]
      if hasPem:
         outgoingSlotConfigs.append(
            SlotConfig(
               slotName='PEM_SLOT@0',
               outgoingI2cBuses=[
                  self.switchcardScd.switchcardSmbusAccel.buses[ 3 ]
               ]
            )
         )
      else:
         outgoingSlotConfigs.append(
            SlotConfig(
               slotName='PSU_SLOT@0',
               presenceFileName='pem_present',
               presenceDevicePath='/[SCD_FPGA]',
               outgoingI2cBuses=[
                  self.switchcardScd.switchcardSmbusAccel.buses[ 3 ]
               ]
            )
         )
      self.addOutgoingSlotConfigs( outgoingSlotConfigs )

   def addEmbeddedSensors( self ):
      # Sensors directly connected to the CPU
      cpuCoreTemp = EmbeddedSensorConfig(
            pmUnitScopedName='CPU_CORE_TEMP',
            sysfsPath='/sys/bus/platform/devices/coretemp.0'
      )
      cpuCoreTemp.addSensorConfigs( [
            SensorConfig( "CPU_PHYS_ID_0", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=105.0
                          ) ),
            SensorConfig( "CPU_CORE0_TEMP", "temp2_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=105.0
                          ) ),
            SensorConfig( "CPU_CORE1_TEMP", "temp3_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=105.0
                          ) ),
            SensorConfig( "CPU_CORE2_TEMP", "temp4_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=105.0
                          ) ),
            SensorConfig( "CPU_CORE3_TEMP", "temp5_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=105.0
                          ) ),
      ] )

      pchThermal = EmbeddedSensorConfig(
            pmUnitScopedName='PCH_THERMAL',
            sysfsPath='/sys/devices/virtual/thermal/thermal_zone0'
      )
      pchThermal.addSensorConfigs( [
            SensorConfig( "PCH_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                             upperCriticalVal=85.0
                          ) ),
      ] )

      self.addEmbeddedSensorConfigs( [
            pchThermal,
            cpuCoreTemp
      ] )

   def addCpuCardTempSensors( self ):
      # Board / back temp sensors.
      cpuBoardTempSensor = Sensor( '0x4C', 'bp4a_max6658', 'CPU_BOARD_TEMP_MAX6658' )
      cpuBoardTempSensor.addSensorConfigs( [
            SensorConfig( "CPU_BOARD_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=85.0
                          ) ),
            SensorConfig( "BACK_PANEL_TEMP", "temp2_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=75.0
                          ) ),
      ] )
      cpuBoardTempSmbus = self.cpuCpld.cpuSmbusAccel.buses[ 0 ]
      cpuBoardTempSmbus.addI2cDevices( [ cpuBoardTempSensor ] )
      self.i2cDevices.append( cpuBoardTempSensor )

      # Front temp sensor on separate smbus.
      cpuFrontTempSensor = Sensor( '0x48', 'lm73', 'CPU_FP_TEMP_LM73' )
      cpuFrontTempSensor.addSensorConfigs( [
            SensorConfig( "FRONT_PANEL_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=85.0
                          ) ),
      ] )
      cpuFrontTempSmbus = self.cpuCpld.fancardSmbusAccel.buses[ 2 ]
      cpuFrontTempSmbus.addI2cDevices( [ cpuFrontTempSensor ] )
      self.i2cDevices.append( cpuFrontTempSensor )

   def addCpuCardDpm( self ):
      # UCD90160 on the CPU card.
      cpuDpm = Sensor( '0x4E', 'ucd90160', 'CPU_POS_UCD90160' )
      cpuDpm.addSensorConfigs( [
            SensorConfig( "POS_1V7_VCCIN_VRRDY", "in1_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.875,
                              lowerCriticalVal=1.12
                          ) ),
            SensorConfig( "POS_0V6_VTT", "in2_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=0.69,
                              lowerCriticalVal=0.51
                          ) ),
            SensorConfig( "POS_1V2_VDDQ", "in3_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.38,
                              lowerCriticalVal=1.02
                          ) ),
            SensorConfig( "POS_2V5_VPP", "in4_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=2.99,
                              lowerCriticalVal=2.21
                          ) ),
            SensorConfig( "POS_1V5_PCH", "in5_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.725,
                              lowerCriticalVal=1.27
                          ) ),
            SensorConfig( "POS_1V05_COM", "in6_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.208,
                              lowerCriticalVal=0.89
                          ) ),
            SensorConfig( "POS_1V3_KRHV", "in7_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.495,
                              lowerCriticalVal=1.1
                          ) ),
            SensorConfig( "POS_1V7_SCFUSE", "in8_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.955,
                              lowerCriticalVal=1.44
                          ) ),
            SensorConfig( "POS_3V3", "in9_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=3.795,
                              lowerCriticalVal=2.8
                          ) ),
            SensorConfig( "POS_5V0", "in10_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=5.75,
                              lowerCriticalVal=4.25
                          ) ),
            SensorConfig( "POS_1V2_ALW", "in11_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.38,
                              lowerCriticalVal=1.02
                          ) ),
            SensorConfig( "POS_3V3_ALW", "in12_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=3.795,
                              lowerCriticalVal=2.8
                          ) ),
            SensorConfig( "POS_12V", "in13_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=13.8,
                              lowerCriticalVal=9.72
                          ) ),
            SensorConfig( "POS_1V2_LAN1", "in14_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.38,
                              lowerCriticalVal=1.02
                          ) ),
            SensorConfig( "POS_1V2_LAN2", "in15_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.38,
                              lowerCriticalVal=1.02
                          ) ),
      ] )
      dpmSmbus = self.cpuCpld.cpuSmbusAccel.buses[ 1 ]
      dpmSmbus.addI2cDevices( [ cpuDpm ] )
      self.i2cDevices.append( cpuDpm )

   def addCpuCardVrms( self ):
      # CPU VRMs.
      cpuVrm1 = Sensor( '0x21', 'pmbus', 'CPU_MPS1_PMBUS' )
      cpuVrm1.addSensorConfigs( [
            SensorConfig( "MPS1_VIN", "in1_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=14.0,
                              lowerCriticalVal=9.0
                          ) ),
            SensorConfig( "MPS1_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=110.0
                          ) ),
            SensorConfig( "MPS1_IIN", "curr1_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=85.0
                          ) ),
            SensorConfig( "MPS1_IOUT", "curr2_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=45.0
                          ) ),
      ] )
      cpuVrm2 = Sensor( '0x27', 'pmbus', 'CPU_MPS2_PMBUS' )
      cpuVrm2.addSensorConfigs( [
            SensorConfig( "MPS2_VIN", "in1_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=14.0,
                              lowerCriticalVal=9.0
                          ) ),
            SensorConfig( "MPS2_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=110.0
                          ) ),
            SensorConfig( "MPS2_IIN", "curr1_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=85.0
                          ) ),
            SensorConfig( "MPS2_IOUT", "curr2_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=35.0
                          ) ),
      ] )
      vrmSmbus = self.cpuCpld.cpuSmbusAccel.buses[ 2 ]
      vrmSmbus.addI2cDevices( [ cpuVrm1, cpuVrm2 ] )
      self.i2cDevices.extend( [ cpuVrm1, cpuVrm2 ] )

   def addFanCpld( self ):
      # I2C Fan CPLD.
      fanCpld = FANCpld( '0x60', 'tehama_cpld', 'FAN_CPLD' )
      fanCpld.addFANRpms( 5, upperCriticalVal=29500.0, lowerCriticalVal=2600.0 )
      fanSmbus = self.cpuCpld.fancardSmbusAccel.buses[ 0 ]
      fanSmbus.addI2cDevices( [ fanCpld ] )
      self.i2cDevices.append( fanCpld )

   def addSwitchcardCpld( self ):
      # Switchcard CPLD and IDPROM.
      switchcardCpld = BlackhawkCpld()
      switchcardIdSmbusDevices = [ switchcardCpld ]
      if not self.hasPem:
         switchcardIdProm = I2cIdProm( '0x50', '24c16', 'CHASSIS_EEPROM' )
         switchcardIdSmbusDevices.append( switchcardIdProm )
      switchcardIdSmbus = self.cpuCpld.switchcardSmbusAccel.buses[ 0 ]
      switchcardIdSmbus.addI2cDevices( switchcardIdSmbusDevices )
      self.i2cDevices.extend( switchcardIdSmbusDevices )

   def addSwitchcardTempSensors( self ):
      # Switchcard temp sensors.
      switchcardMax6581 = Sensor( '0x4D', 'max6581', 'SC_BOARD_TEMP_MAX6581' )
      switchcardMax6581.addSensorConfigs( [
            SensorConfig( "SC_BOARD_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=85.0
                          ) ),
            SensorConfig( "SC_BOARD_MIDDLE_TEMP", "temp2_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=75.0
                          ) ),
            SensorConfig( "SC_BOARD_LEFT_TEMP", "temp3_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=75.0
                          ) ),
            SensorConfig( "SC_FRONT_PANEL_TEMP", "temp4_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=75.0
                          ) ),
            SensorConfig( "SC_TH3_DIODE1_TEMP", "temp7_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=125.0
                          ) ),
            SensorConfig( "SC_TH3_DIODE2_TEMP", "temp8_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=125.0
                          ) ),
      ] )
      switchcardTempSmbus = self.switchcardScd.switchcardSmbusAccel.buses[ 0 ]
      switchcardTempSmbus.addI2cDevices( [ switchcardMax6581 ] )
      self.i2cDevices.append( switchcardMax6581 )

   def addSwitchcardDpm( self ):
      # Switchcard DPM.
      switchcardDpm = Sensor( '0x11', 'ucd90320', 'SC_POS_UCD90320' )
      switchcardDpm.addSensorConfigs( [
            SensorConfig( "SC_POS_12V_TH3_A", "in1_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=13.8,
                              lowerCriticalVal=9.5
                          ) ),
            SensorConfig( "SC_POS_12V_TH3_B", "in2_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=13.8,
                              lowerCriticalVal=9.5
                          ) ),
            SensorConfig( "SC_POS_12V_STDBY", "in3_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=13.8,
                              lowerCriticalVal=9.5
                          ) ),
            SensorConfig( "SC_POS_5V0", "in4_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=5.75,
                              lowerCriticalVal=4.25
                          ) ),
            SensorConfig( "SC_POS_3V3", "in5_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=3.795,
                              lowerCriticalVal=2.805
                          ) ),
            SensorConfig( "SC_POS_3V3_QSFPDD_A", "in6_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=3.795,
                              lowerCriticalVal=2.805
                          ) ),
            SensorConfig( "SC_POS_3V3_QSFPDD_B", "in7_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=3.795,
                              lowerCriticalVal=2.805
                          ) ),
            SensorConfig( "SC_POS_3V3_STDBY", "in8_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=3.795,
                              lowerCriticalVal=2.475
                          ) ),
            SensorConfig( "SC_POS_2V5_LT", "in9_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=5.1,
                              lowerCriticalVal=0.5
                          ) ),
            SensorConfig( "SC_POS_2V5_RT", "in10_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=5.1,
                              lowerCriticalVal=0.5
                          ) ),
            SensorConfig( "SC_POS_1V8", "in11_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=2.07,
                              lowerCriticalVal=1.53
                          ) ),
            SensorConfig( "SC_POS_1V5_A", "in12_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.725,
                              lowerCriticalVal=1.275
                          ) ),
            SensorConfig( "SC_POS_1V5_B", "in13_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.38,
                              lowerCriticalVal=1.02
                          ) ),
            SensorConfig( "SC_POS_1V2", "in14_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.38,
                              lowerCriticalVal=1.02
                          ) ),
            SensorConfig( "SC_POS_0V8_AVDD", "in15_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=0.92,
                              lowerCriticalVal=0.72
                          ) ),
            SensorConfig( "SC_POS_0V9_VDD", "in16_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=1.35,
                              lowerCriticalVal=0.38
                          ) ),
      ] )
      switchcardDpmSmbus = self.cpuCpld.switchcardSmbusAccel.buses[ 2 ]
      switchcardDpmSmbus.addI2cDevices( [ switchcardDpm ] )
      self.i2cDevices.append( switchcardDpm )

   def addSwitchcardVrms( self ):
      # Switchcard voltage sensors
      th3CoreIr35223 = Sensor( '0x40', 'pmbus', 'SC_TH3_CORE_IR35223' )
      th3CoreIr35223.addSensorConfigs( [
            SensorConfig( "TH3_VRD1_VIN", "in1_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=14.5,
                              lowerCriticalVal=9.0
                          ) ),
            SensorConfig( "TH3_VRD1_VOUT", "in2_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=None
                        ),
            SensorConfig( "TH3_VRD1_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=125.0
                          ) ),
            SensorConfig( "TH3_VRD1_POUT", "power2_input", SensorType.POWER,
                          compute="@/1000000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=400.0
                          ) ),
            SensorConfig( "TH3_VRD1_IIN", "curr1_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=60.5
                          ) ),
            SensorConfig( "TH3_VRD1_IOUT", "curr2_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=464
                          ) ),
      ] )
      th3CoreSmbus = self.switchcardScd.switchcardSmbusAccel.buses[ 5 ]
      th3CoreSmbus.addI2cDevices( [ th3CoreIr35223 ] )
      self.i2cDevices.append( th3CoreIr35223 )

      th3AnlgIr35223 = Sensor( '0x41', 'pmbus', 'SC_TH3_ANLG_IR35223' )
      th3AnlgIr35223.addSensorConfigs( [
            SensorConfig( "TH3_VRD2_VIN", "in1_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=14.5,
                              lowerCriticalVal=9.0
                          ) ),
            SensorConfig( "TH3_VRD2_VOUT", "in2_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=None
                        ),
            SensorConfig( "TH3_VRD2_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=125.0
                          ) ),
            SensorConfig( "TH3_VRD2_POUT", "power2_input", SensorType.POWER,
                          compute="@/1000000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=400.0
                          ) ),
            SensorConfig( "TH3_VRD2_IIN", "curr1_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=60.5
                          ) ),
            SensorConfig( "TH3_VRD2_IOUT", "curr2_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=124
                          ) ),
      ] )
      th3AnlgSmbus = self.switchcardScd.switchcardSmbusAccel.buses[ 6 ]
      th3AnlgSmbus.addI2cDevices( [ th3AnlgIr35223 ] )
      self.i2cDevices.append( th3AnlgIr35223 )

      qsfpDdIr35223 = Sensor( '0x42', 'pmbus', 'SC_QSFPDD_IR35223' )
      qsfpDdIr35223.addSensorConfigs( [
            SensorConfig( "QSFPDD_VRD_VIN", "in1_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=14.5,
                              lowerCriticalVal=9.0
                          ) ),
            SensorConfig( "QSFPDD_VRD_VOUT_A", "in2_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=None
                        ),
            SensorConfig( "QSFPDD_VRD_VOUT_B", "in3_input", SensorType.VOLTAGE,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=None
                        ),
            SensorConfig( "QSFPDD_VRD_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=125.0
                          ) ),
            SensorConfig( "QSFPDD_VRD_POUT_A", "power2_input", SensorType.POWER,
                          compute="@/1000000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=400.0
                          ) ),
            SensorConfig( "QSFPDD_VRD_POUT_B", "power3_input", SensorType.POWER,
                          compute="@/1000000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=400.0
                          ) ),
            SensorConfig( "QSFPDD_VRD_IIN", "curr1_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=60.5
                          ) ),
            SensorConfig( "QSFPDD_VRD_IOUT_A", "curr2_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=120
                          ) ),
            SensorConfig( "QSFPDD_VRD_IOUT_B", "curr3_input", SensorType.CURRENT,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=120
                          ) ),
      ] )
      qsfpDdSmbus = self.switchcardScd.switchcardSmbusAccel.buses[ 7 ]
      qsfpDdSmbus.addI2cDevices( [ qsfpDdIr35223 ] )
      self.i2cDevices.append( qsfpDdIr35223 )


class RackhawkRackmon( PmUnitConfig ):
   def __init__( self, eepromOffset ):
      super().__init__( 'RACKMON' )

      # TODO: Need PM to be able to handle other EEPROM formats
      self.setSlotTypeConfig(
         numOutgoingI2cBuses=1,
         idPromConfigBusName='INCOMING@0',
         idPromConfigAddress='0x52',
         idPromConfigKernelDeviceName='24c512',
         idPromConfigOffset=eepromOffset
      )

      aslg4f4527 = Sensor( '0x08', 'aslg4f4527', 'FS_FAN_SLG4F4527',
                           incomingBusIndex=0 )
      aslg4f4527.addSensorConfigs( [
            SensorConfig( "FS_FAN_RPM", "fan1_input", SensorType.FAN_SPEED,
                          prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=29500,
                              lowerCriticalVal=2600
                          ) )
      ] )
      pcaGpio = GpioChip( '0x74', 'pca9539', 'RACKMON_PLS', incomingBusIndex=0 )
      fanspinnerIdProm = I2cIdProm( '0x50', '24c512', 'FANSPINNER_EEPROM',
                                    incomingBusIndex=0 )
      self.addI2cDeviceConfigs( [
         aslg4f4527,
         pcaGpio,
         fanspinnerIdProm,
      ] )

   def populateSymlinkToDevicePaths( self ):
      # Override this method to account for special-case Rackmon EEPROM.
      addedPaths = {
         "/run/devmap/eeproms/RACKMON_EEPROM": "/RACKMON_SLOT@0/[IDPROM]",
         **self.generateI2cDeviceSymlinks(),
      }
      self.symlinkToDevicePaths.update( addedPaths )


class RackhawkPEM( PmUnitConfig ):
   def __init__( self ):
      super().__init__( 'PEM' )

      # TODO: Need PM to be able to handle other EEPROM formats
      self.setSlotTypeConfig(
         numOutgoingI2cBuses=1,
         idPromConfigBusName='INCOMING@0',
         idPromConfigAddress='0x50',
         idPromConfigKernelDeviceName='24c512',
         idPromConfigOffset=0
      )

      pemEcb = Sensor( '0x3A', 'amax5970', 'PEM_ECB_MAX5970', incomingBusIndex=0 )
      pemEcb.addSensorConfigs( [
            SensorConfig( "PEM_ECB_VOUT_CH1", "in1_input", SensorType.VOLTAGE,
                          compute="(15.5*@)/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=14.0
                          ) ),
            SensorConfig( "PEM_ECB_VOUT_CH2", "in2_input", SensorType.VOLTAGE,
                          compute="(15.5*@)/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=14.0
                          ) ),
            SensorConfig( "PEM_ECB_IOUT_CH1", "curr1_input", SensorType.CURRENT,
                          compute="(48390/343)*@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=60.0,
                              lowerCriticalVal=0.5
                          ) ),
            SensorConfig( "PEM_ECB_IOUT_CH2", "curr2_input", SensorType.CURRENT,
                          compute="(48390/343)*@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=60.0,
                              lowerCriticalVal=0.5
                          ) ),
      ] )

      pemAdc = Sensor( '0x36', 'bp4a_max11645', 'PEM_ADC_MAX11645',
                       incomingBusIndex=0 )
      pemAdc.addSensorConfigs( [
            SensorConfig( "PEM_ADC_VIN", "in_voltage1_raw", SensorType.VOLTAGE,
                          compute="@*2.048*7.64/4096", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=13.5,
                              lowerCriticalVal=10.9
                          ) ),
            SensorConfig( "PEM_ADC_VOUT", "in_voltage0_raw", SensorType.VOLTAGE,
                          compute="@*2.048*7.64/4096", prependPmUnit=False,
                          thresholds=Thresholds(
                              lowerCriticalVal=10.8
                          ) ),
            SensorConfig( "PEM_ADC_VDROP", "in_voltage1-voltage0_raw",
                          SensorType.VOLTAGE, compute="@/1000.0",
                          prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=0.08,
                              lowerCriticalVal=0
                          ) ),
      ] )

      pemTempSensor = Sensor( '0x4C', 'bp4a_max6658', 'PEM_TEMP_MAX6658',
                              incomingBusIndex=0 )
      pemTempSensor.addSensorConfigs( [
            SensorConfig( "PEM_INTERNAL_TEMP", "temp1_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=85.0
                          ) ),
            SensorConfig( "PEM_EXTERNAL_TEMP", "temp2_input", SensorType.TEMP,
                          compute="@/1000.0", prependPmUnit=False,
                          thresholds=Thresholds(
                              upperCriticalVal=85.0
                          ) ),
      ] )
      self.addI2cDeviceConfigs( [ pemEcb, pemAdc, pemTempSensor ] )


class Rackhawk( PlatformConfig ):
   codename = 'darwin'
   hasPem = True
   eepromOffset = 0

   def __init__( self ):
      super().__init__( self.codename, rootPmUnitName='SMB' )

      pmUnits = [
            RackhawkSwitch( self.hasPem ),
            FANUnit(),
            RackhawkRackmon( self.eepromOffset ),
      ]
      if self.hasPem:
         pmUnits.append( RackhawkPEM() )
      else:
         pmUnits.append( PSUUnit( singlePSU=True ) )
      self.addPmUnitConfigs( pmUnits )

      self.addI2cAdaptersFromCpu( [ 'SMBus I801 adapter at 1020' ] )

      kmods = [
         'scd',
         'scd-leds',
         'scd-smbus',
         'scd-spi',
         'rook-fan-cpld',
         'blackhawk-cpld',
         'aslg4f4527',
         'bp4a_lm90',
      ]
      if self.hasPem:
         kmods.append( 'amax5970' )
         kmods.append( 'bp4a_max1363' )
      self.addKmodsSettings(
         {
            'bspKmodsToReload': kmods,
            'sharedKmodsToReload': [ 'scd' ],
            'upstreamKmodsToLoad': [ 'i2c-i801' ]
         }
      )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()


class RackhawkORv3( Rackhawk ):
   codename = 'darwin48v'
   hasPem = False
   eepromOffset = 15360
