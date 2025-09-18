# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from GenerateConfigsAndDiagrams.BaseConfigs import (
   enumerateFANSlotConfigs,
   FANCpld,
   FANUnit,
   FanServiceConfig,
   OpticConfig,
   PciDeviceConfig,
   PlatformConfig,
   SCMFairywren,
   SlotConfig,
   SMBCpld,
   SMBUnit,
   PSUUnit,
   LedConfig,
   Sensor,
   SensorConfig,
   SensorType,
   Thresholds,
   InitRegSettings,
   SpiMasterConfig,
   Flash
)


class QuicksilverPFbSCM( SCMFairywren ):
   def __init__( self ):
      self.supportsP1 = False
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

class QuicksilverPFbSMB( SMBUnit ):
   prefixSymlink = 'GLATH05A-64O'

   def __init__( self ):
      super().__init__( self.prefixSymlink )

      smbFanCpld = FANCpld( "0x60", "glath05a64o_fancpld", "FAN_CPLD",
                            incomingBusIndex=2 )
      smbFanCpld.addFANRpms( 4, upperCriticalVal=14900.0, lowerCriticalVal=1100.0 )

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=3,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )


      smbCpld = SMBCpld( "0x23", "glath05a-64o_cpld", "SMB_CPLD", incomingBusIndex=0 )

      smbFanTmp = Sensor( "0x48", "lm75", "FAN_TMP75", incomingBusIndex=2,
                          # Overtemperature threshold set to match EOS
                          initRegSettings = InitRegSettings( [ ( 3, 100 ) ] ) )
      smbFanTmp.addSensorConfigs( [
         SensorConfig( "FAN_BOARD_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=85.0
                       ) )
      ] )

      smbMgmtTemp = Sensor( "0x48", "lm75", "SMB_MGMT_TMP75",
                            # Overtemperature threshold set to match EOS
                            initRegSettings = InitRegSettings( [ ( 3, 110 ) ] ) )
      smbMgmtTemp.addSensorConfigs( [
         SensorConfig( "MGMT_INLET_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=105.0, maxAlarmVal=95.0
                       ) )
      ] )

      smbMax = Sensor( "0x4D", "max6581", "SMB_MAX6581" )
      smbMax.addSensorConfigs( [
         SensorConfig( "SCM_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=105.0, maxAlarmVal=95.0
                       ) ),
         SensorConfig( "TH5_AIR_BEHIND_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=105.0, maxAlarmVal=95.0
                       ) ),
         SensorConfig( "LEFT_EDGE_PCB_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=105.0, maxAlarmVal=95.0
                       ) ),
         SensorConfig( "AIR_INLET_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=105.0, maxAlarmVal=95.0
                       ) ),
         SensorConfig( "TH5_DIODE_1_TEMP", "temp7_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH5_DIODE_2_TEMP", "temp8_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbRaa = Sensor( "0x45", "raa228228", "SMB_RAA228926_TH5_CORE" )
      smbRaa.addSensorConfigs( [
         SensorConfig( "RAA_TH5_CORE_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=115.0, maxAlarmVal=105.0
                       ) ),
         SensorConfig( "RAA_TH5_CORE_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=15.0, lowerCriticalVal=9.0
                       ) ),
         SensorConfig( "RAA_TH5_CORE_VDD", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=1.0, lowerCriticalVal=0.6
                       ) )
      ] )

      smbIsl0V9 = Sensor( "0x46", "isl68226", "SMB_ISL68226_TH5_0V9_ANALOG" )
      smbIsl0V9.addSensorConfigs( [
         SensorConfig( "ISL_TH5_0V9_TEMP1", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=115.0, maxAlarmVal=105.0
                       ) ),
         SensorConfig( "ISL_TH5_0V9_TEMP2", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=115.0, maxAlarmVal=105.0
                       ) ),
         SensorConfig( "ISL_TH5_0V9_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=15.0, lowerCriticalVal=9.0
                       ) ),
         SensorConfig( "ISL_TH5_0V9_AVDD_0", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=1.08, lowerCriticalVal=0.675
                       ) ),
         SensorConfig( "ISL_TH5_0V9_AVDD_1", "in4_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=1.08, lowerCriticalVal=0.675
                       ) )
      ] )

      smbIsl0V75 = Sensor( "0x47", "isl68226", "SMB_ISL68226_TH5_0V75_ANALOG" )
      smbIsl0V75.addSensorConfigs( [
         SensorConfig( "ISL_TH5_0V75_TEMP1", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=115.0, maxAlarmVal=105.0
                       ) ),
         SensorConfig( "ISL_TH5_0V75_TEMP2", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=115.0, maxAlarmVal=105.0
                       ) ),
         SensorConfig( "ISL_TH5_0V75_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=15.0, lowerCriticalVal=9.0
                       ) ),
         SensorConfig( "ISL_TH5_0V75_AVDD_0", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=0.9375, lowerCriticalVal=0.5625
                       ) ),
         SensorConfig( "ISL_TH5_0V75_AVDD_1", "in4_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=0.9375, lowerCriticalVal=0.5625
                       ) )
      ] )

      smbIslOpticsA = Sensor( "0x4D", "isl68226", "SMB_ISL68226_OPTICS_A" )
      smbIslOpticsA.addSensorConfigs( [
         SensorConfig( "ISL_OPTICS_A_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=115.0, maxAlarmVal=105.0
                       ) ),
         SensorConfig( "ISL_OPTICS_A_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=15.0, lowerCriticalVal=9.0
                       ) ),
         SensorConfig( "ISL_OPTICS_A_VOUT_3V3", "in3_input", SensorType.VOLTAGE,
                       compute="1.2*@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=4.125, lowerCriticalVal=2.475
                       ) )
      ] )

      smbIslOpticsB = Sensor( "0x4C", "isl68226", "SMB_ISL68226_OPTICS_B" )
      smbIslOpticsB.addSensorConfigs( [
         SensorConfig( "ISL_OPTICS_B_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=115.0, maxAlarmVal=105.0
                       ) ),
         SensorConfig( "ISL_OPTICS_B_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=15.0, lowerCriticalVal=9.0
                       ) ),
         SensorConfig( "ISL_OPTICS_B_VOUT_3V3", "in3_input", SensorType.VOLTAGE,
                       compute="1.2@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=4.125, lowerCriticalVal=2.475
                       ) )
      ] )

      self.addI2cDeviceConfigs( [
         smbCpld,
         smbFanCpld,
         smbFanTmp,
         smbMgmtTemp,
         smbMax,
         smbRaa,
         smbIsl0V9,
         smbIsl0V75,
         smbIslOpticsA,
         smbIslOpticsB
      ] )

      self.addPciDeviceConfigs( [
         PciDeviceConfig( "SMB_FPGA", "0x3475", "0x0001", "0x3475", "0x0009",
                         symlinkDeviceName="GLATH05A-64O_SMB_FPGA" )
      ] )

      smbFpga = self.pciDeviceConfigs[ 0 ]
      smbFpga.addInfoRomConfigs( "0x100" )
      smbFpga.addI2cAdapterConfigs( 11, "SMB_I2C_MASTER{}", "0x8080" )
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

      smbFpga.addXcvrCtrlConfigs( numConfigs=64, basePortNumber=1, ledsPerXcvr=2,
                                  smbusAccelStart=2, smbusName="SMB_I2C_MASTER",
                                  xcvrBaseOffset="0xA000", accelBusRange=( 0, 7 ),
                                  lanesCount=8 )

      smbFpga.addLedCtrlConfigs( [
         LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
         LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
         LedConfig( ledName="PSU1_STATUS_LED", offset="0x6070" ),
      ] )

      smbI2cMaster0 = self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 0 ]
      smbI2cMaster1 = self.pciDeviceConfigs[ 0 ].i2cAdapterConfigs[ 1 ]

      smbI2cMaster0.buses[ 5 ].addI2cDevices( [ smbMgmtTemp ] )
      smbI2cMaster0.buses[ 0 ].addI2cDevices( [ smbMax ] )
      smbI2cMaster1.buses[ 0 ].addI2cDevices( [ smbRaa ] )
      smbI2cMaster1.buses[ 1 ].addI2cDevices( [ smbIsl0V9 ] )
      smbI2cMaster1.buses[ 2 ].addI2cDevices( [ smbIsl0V75 ] )
      smbI2cMaster1.buses[ 3 ].addI2cDevices( [ smbIslOpticsA ] )
      smbI2cMaster1.buses[ 4 ].addI2cDevices( [ smbIslOpticsB ] )

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="psu1_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ smbI2cMaster0.buses[ 3 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@1",
            presenceFileName="psu2_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA]",
            outgoingI2cBuses=[ smbI2cMaster0.buses[ 4 ] ]
         ),
         *enumerateFANSlotConfigs( 4, "/SMB_SLOT@0/[FAN_CPLD]" ),
      ] )



class QuicksilverPFb( PlatformConfig ):
   codename = 'glath05a-64o'

   def __init__( self ):
      super().__init__( self.codename )

      self.addPmUnitConfigs( [
         QuicksilverPFbSCM(),
         QuicksilverPFbSMB(),
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
      # 1. Set global PWM and control interval parameters
      fanServiceConfig.setPwmConfig(  pwmBoostOnNumDeadFan=1,
                                       pwmBoostOnNumDeadSensor=0,
                                       pwmBoostOnNoQsfpAfterInSec=31,
                                       pwmBoostValue=75,
                                       pwmTransitionValue=75,
                                       pwmLowerThreshold=54,
                                       pwmUpperThreshold=100 )
      fanServiceConfig.setControlInterval(
                                       sensorReadInterval=5, 
                                       pwmUpdateInterval=5 )
      # 2. Define the optics group with its specific temp-to-PWM map
      opticConfig = fanServiceConfig.addOpticConfig( "osfp_group_1", "QSFP" )
      opticConfig.addTempToPwmMap( 800, {
            "5": 54,
            "66": 58,
            "67": 60,
            "68": 62,
            "69": 75,
            "70": 95,
            "71": 100
      } )
      # 3. Define the sensor(s) to be used in zones
      # Note: We use the unresolved name "TH5_DIODE_1_TEMP" from QuicksilverPFbSMB
      fanServiceConfig.addSensor( "TH5_DIODE_1_TEMP", "THRIFT", {
            "15": 54,
            "110": 100
      } )
      # 4. Define the thermal control zone
      fanServiceConfig.addZone(
         zoneName="zone1",
         sensorNames=[ "TH5_DIODE_1_TEMP", "osfp_group_1" ],
         fanNumbers=range( 1, 5 ),  # Fans 1 through 4
         slope=3
      )
      self.PlatformFanServiceConfig = fanServiceConfig