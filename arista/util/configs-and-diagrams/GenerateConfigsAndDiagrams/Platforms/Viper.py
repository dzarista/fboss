# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from ..BaseConfigs import (
   enumerateFANSlotConfigs,
   FANUnit,
   FANCpld,
   FanServiceConfig,
   Flash,
   GpioChip,
   I2cDeviceConfig,
   InitRegSettings,
   LedConfig,
   MiscConfig,
   OpticConfig,
   PciDeviceConfig,
   PlatformConfig,
   PSUUnit,
   Sensor,
   SCMFairywren,
   SensorConfig,
   SensorType,
   SlotConfig,
   SMBUnit,
   SpiMasterConfig,
   Thresholds,
)


class ViperSCM( SCMFairywren ):
   def __init__( self ):
      super().__init__()

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="SMB_SLOT@0",
            outgoingI2cBuses=[
               self.scmI2cMaster1.buses[ 0 ],
               self.scmI2cMaster1.buses[ 2 ],
               self.scmI2cMaster1.buses[ 3 ]
            ]
         )
      ] )


class ViperSMB( SMBUnit ):
   prefixSymlink = 'MERU800BIA'

   def __init__( self ):
      super().__init__( self.prefixSymlink )
      self.fanServiceSensorConfigs = {}

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=3,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )

      # Initial I2c register values are implicitly cast to 8-bit unsigned integer
      # values when creating a device, but Python uses two's complement.
      # -121 in 8-bit two's complement has the same binary representation as
      # 135 in 8-bit unsigned. Register values represent temperature in Celsius and
      # are used to overwrite the default temperature settings.
      scdVcpld = I2cDeviceConfig( "0x23", "scd_vcpld", "SCD_VCPLD", incomingBusIndex=0 )

      smbPca = GpioChip( "0x74", "pca9539", "SMB_PCA", incomingBusIndex=0 )

      smbTmp75Front = Sensor( "0x49", "lm75", "SMB_TMP75_FRONT", incomingBusIndex=1,
                              initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) )

      smbTmp75Front.addSensorConfigs([ SensorConfig( "BOARD_FRONT_TEMP", 
                                        "temp1_input", 
                                        SensorType.TEMP,
                                        compute="@/1000.0",
                                        thresholds=Thresholds(
                                        upperCriticalVal=85.0, maxAlarmVal=80.0 )
                                       ) ] )

      smbTmp75Back = Sensor( "0x4A", "lm75", "SMB_TMP75_REAR",
                             incomingBusIndex=1,
                             initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) )
      smbTmp75Back.addSensorConfigs( [
         SensorConfig( "BOARD_REAR_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=85.0, maxAlarmVal=80.0
                       ) )
      ] )

      smbMax = Sensor( "0x4D", "max6581", "SMB_MAX6581", incomingBusIndex=1,
                       initRegSettings=InitRegSettings( [
                           ( 32, 110 ),
                           ( 33, -121 ),
                           ( 34, -121 ),
                           ( 35, -121 ),
                           ( 36, -121 ),
                           ( 37, -121 ),
                           ( 38, -121 ),
                           ( 39, -121 ),
                           ( 75, 31 ),
                           ( 76, 127 )
                        ] )
                     )
      smbMax.addSensorConfigs( [
         SensorConfig( "J3_BOARD_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=85.0
                       ) ),
         SensorConfig( "J3_DIODE_CORE_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=104.0, maxAlarmVal=99.0
                       ) ),
         SensorConfig( "J3_DIODE_FAB0_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=104.0, maxAlarmVal=99.0
                       ) ),
         SensorConfig( "J3_DIODE_FAB1_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=104.0, maxAlarmVal=99.0
                       ) ),
         SensorConfig( "J3_DIODE_NIF0_TEMP", "temp5_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=104.0, maxAlarmVal=99.0
                       ) ),
         SensorConfig( "J3_DIODE_NIF1_TEMP", "temp6_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=104.0, maxAlarmVal=99.0
                       ) ),
         SensorConfig( "J3_DIODE_HBM0_TEMP", "temp7_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=94.0, maxAlarmVal=89.0
                       ) ),
         SensorConfig( "J3_DIODE_HBM1_TEMP", "temp8_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=94.0, maxAlarmVal=89.0
                       ) )
      ] )

      smbFanTmp = Sensor( "0x48", "lm75", "FAN_TMP75", incomingBusIndex=2,
                          initRegSettings=InitRegSettings( [ ( 3, 95 ) ] ) )
      smbFanTmp.addSensorConfigs( [
         SensorConfig( "FAN_BOARD_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=85.0, maxAlarmVal=80.0
                       ) )
      ] )

      smbFanCpld = FANCpld( "0x60", "fan_cpld", "FAN_CPLD", incomingBusIndex=2 )
      smbFanCpld.addFANRpms( 4, upperCriticalVal=14900.0, lowerCriticalVal=1100.0 )

      smbRaa = Sensor( "0x45", "raa228228", "SMB_RAA228926_J3" )
      smbRaa.addSensorConfigs( [
         SensorConfig( "VRM1_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM1_VOUT_J3_0V85_CORE", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=0.93, lowerCriticalVal=0.62
                       ) ),
         SensorConfig( "VRM1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
      ] )

      smbIsl = Sensor( "0x54", "isl68226", "SMB_ISL68226_J3" )
      smbIsl.addSensorConfigs( [
         SensorConfig( "VRM2_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM2_VOUT_J3_0V9", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.08, lowerCriticalVal=0.72
                       ) ),
         SensorConfig( "VRM2_VOUT_J3_0V75", "in4_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=0.9, lowerCriticalVal=0.6
                       ) ),
         SensorConfig( "VRM2_VOUT_J3_1V2", "in5_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.44, lowerCriticalVal=0.96
                       ) ),
         SensorConfig( "VRM2_TEMP1", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM2_TEMP2", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM2_TEMP3", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbIslOptics = Sensor( "0x55", "isl68226", "SMB_ISL68226_OPTICS" )
      smbIslOptics.addSensorConfigs( [
         SensorConfig( "VRM3_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM3_VOUT_OPTICS_3V3", "in3_input", SensorType.VOLTAGE,
                       compute="1.2*@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=3.96, lowerCriticalVal=2.64
                       ) ),
         SensorConfig( "VRM3_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbMgmtTemp = Sensor( "0x48", "lm75", "SMB_MGMT_TMP75" )
      smbMgmtTemp.addSensorConfigs( [
         SensorConfig( "MGMT_INLET_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=75.0, maxAlarmVal=70.0
                       ) )
      ] )

      self.addI2cDeviceConfigs( [
         scdVcpld,
         smbPca,
         smbTmp75Front,
         smbTmp75Back,
         smbMax,
         smbFanTmp,
         smbRaa,
         smbIsl,
         smbIslOptics,
         smbMgmtTemp,
         smbFanCpld
      ] )

      self.addPciDeviceConfigs( [
         PciDeviceConfig( "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0003",
                         symlinkDeviceName="MERU800BIA_SMB_FPGA" )
      ] )

      smbFpga = self.pciDeviceConfigs[ 0 ]
      smbFpga.addI2cAdapterConfigs( 6, "SMB_I2C_MASTER{}", "0x8000" )
      smbFpga.addSpiMasterConfigs( [
         SpiMasterConfig( "SMB_SPI_MASTER0", "spi_master", -1,
                           "0x7900",
                           spiDeviceConfigs=[ Flash(
                              pmUnitScopedName="SMB_SPI_MASTER0_DEVICE1",
                              chipSelect=0,
                              modalias="spidev",
                              maxSpeedHz=25000000
                           ) ]
                        )
      ] )

      smbFpga.addXcvrCtrlConfigs( numConfigs=32, basePortNumber=1,
                                  smbusName="SMB_I2C_MASTER", smbusAccelStart=1,
                                  accelBusRange=( 0, 7 ), lanesCount=8 )

      smbFpga.addXcvrCtrlConfigs( numConfigs=6, basePortNumber=33,
                                  xcvrBaseOffset="0xA210", ledBaseOffset="0x6500",
                                  smbusName="SMB_I2C_MASTER",
                                  smbusAccelStart=5, accelBusRange=( 0, 5 ),
                                  lanesCount=8 )

      smbFpga.addXcvrCtrlConfigs( numConfigs=1, basePortNumber=39,
                                  portType="qsfp", xcvrBaseOffset="0xA290",
                                  ledBaseOffset="0x65C0", ledsPerXcvr=4,
                                  smbusName="SMB_I2C_MASTER", smbusAccelStart=0,
                                  accelBusRange=( 4, 4 ), lanesCount=4
                                 )

      smbFpga.addInfoRomConfigs( "0x100" )
      smbFpga.addMiscCtrlConfigs( [
         MiscConfig( name="SMB_ADC", deviceName="adc", offset="0x7300" )
      ] )
      smbFpga.addLedCtrlConfigs( [
         LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
         LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
         LedConfig( ledName="PSU_STATUS_LED", offset="0x6070" ),
         LedConfig( ledName="SMB_STATUS_LED", offset="0x6090" )
      ] )

      smbI2cMaster0 = self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 0 ]
      smbI2cMaster0.buses[ 0 ].addI2cDevices( [ smbRaa, smbIsl, smbIslOptics ] )
      smbI2cMaster0.buses[ 2 ].addI2cDevices( [ smbMgmtTemp ] )

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="psu1_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ smbI2cMaster0.buses[ 5 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@1",
            presenceFileName="psu2_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ smbI2cMaster0.buses[ 6 ] ]
         ),
         *enumerateFANSlotConfigs( 4, "/SMB_SLOT@0/[FAN_CPLD]" )
      ] )


class Viper( PlatformConfig ):
   codename = 'meru800bia'

   def __init__( self ):
      super().__init__( self.codename )
      self.addPmUnitConfigs( [
         ViperSCM(),
         ViperSMB(),
         PSUUnit( initRegSettings=InitRegSettings( [ ( 16, -128 ) ] ) ),
         FANUnit()
      ] )

      self.addI2cAdaptersFromCpu( [ "SMBus I801 adapter at 1000" ] )

      self.addKmodsSettings(
         {
            "requiredKmodsToLoad": [ "spidev",
                                     "i2c_i801", 
                                     "scd",
                                     "ledtrig_timer" ]
         }
      )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths()


      # Fan Service Config
      fanServiceConfig = FanServiceConfig()
      # Creates top variables
      fanServiceConfig.setPwmConfig(  pwmBoostOnNumDeadFan = 1,
                                       pwmBoostOnNumDeadSensor = 0,
                                       pwmBoostOnNoQsfpAfterInSec = 0,
                                       pwmBoostValue = 60,
                                       pwmTransitionValue = 50,
                                       pwmLowerThreshold = 30,
                                       pwmUpperThreshold = 100 )
      # Handles Optics
      opticConfig = fanServiceConfig.addOpticConfig( "osfp_group_1", "QSFP" )
      opticLookupTable = {
         "5": 43,
         "69": 56,
         "70": 73,
         "71": 100
      }
      opticConfig.addTempToPwmMap( 800, opticLookupTable )
      # Handles sensors
      sensorLookupTable = {
        "15": 30,
        "110": 100
      }
      fanServiceConfig.addSensor( "BOARD_FRONT_TEMP", "THRIFT", sensorLookupTable )
      # Only define zones at the end
      fanServiceConfig.addZone(
         zoneName="zone1",
         sensorNames=[ "BOARD_FRONT_TEMP", "osfp_group_1" ],
         fanNumbers=range( 1, 5 ),  # Defines fans 1, 2, 3, and 4
         slope=3
      )
      self.PlatformFanServiceConfig = fanServiceConfig