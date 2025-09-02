# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from ..BaseConfigs import (
   enumerateFANSlotConfigs,
   enumeratePciDeviceConfigs,
   FANCpld,
   FANUnit,
   FanServiceConfig,
   Flash,
   InitRegSettings,
   LedConfig,
   OpticConfig,     
   PlatformConfig,
   PSUUnit,
   SCMFairywren,
   Sensor,
   SensorConfig,
   SensorType,
   SlotConfig,
   SMBCpld,
   SMBUnit,
   SpiMasterConfig,
   Thresholds
)


class WhistlerSCM( SCMFairywren ):
   def __init__( self ):
      super().__init__()

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="SMB_SLOT@0",
            outgoingI2cBuses=[
               self.scmI2cMaster1.buses[ 0 ],
               self.scmI2cMaster1.buses[ 1 ],
               self.scmI2cMaster1.buses[ 2 ],
               self.scmI2cMaster1.buses[ 3 ]
            ]
         )
      ] )


class WhistlerSMB( SMBUnit ):
   def __init__( self ):
      super().__init__()

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=4,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x52",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360
      )

      smbCpld = SMBCpld( "0x23", "decker_cpld", "SMB_CPLD", incomingBusIndex=0 )

      smbMax = Sensor( "0x4D", "max6581", "SMB_MAX6581", incomingBusIndex=0,
                       initRegSettings=InitRegSettings( [
                           ( 75, 31 ),
                           ( 76, 3 )
                       ] )
                     )
      smbMax.addSensorConfigs( [
         SensorConfig( "BOARD_TOP_CENTER_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "R3_0_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=125.0, maxAlarmVal=110.0
                       ) ),
         SensorConfig( "R3_1_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=125.0, maxAlarmVal=110.0
                       ) ),
         SensorConfig( "BOARD_REAR_RIGHT_TEMP", "temp5_input", SensorType.TEMP,
                       compute="@/1000.0", thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "BOARD_FRONT_RIGHT_TEMP", "temp6_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "BOARD_REAR_LEFT_TEMP", "temp7_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=90.0
                       ) ),
         SensorConfig( "BOARD_FRONT_LEFT_TEMP", "temp8_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=90.0
                       ) )
      ] )

      smbTmp = Sensor( "0x48", "lm75", "SMB_TMP75", incomingBusIndex=0 )
      smbTmp.addSensorConfigs( [
         SensorConfig( "INLET_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=85.0
                       ) )
      ] )

      smbRaa0 = Sensor( "0x60", "raa228228", "SMB_RAA228926_R3R0_CORE",
                       incomingBusIndex=1 )
      smbRaa0.addSensorConfigs( [
         SensorConfig( "VRM_R3R0_CORE_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_R3R0_CORE_VOUT_0V75", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.008, lowerCriticalVal=0.504
                       ) ),
         SensorConfig( "VRM_R3R0_CORE_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbIslR3R0Analog0 = Sensor( "0x50", "bp4a_isl68226", "SMB_ISL68226_R3R0_ANLG0",
                                incomingBusIndex=1 )
      smbIslR3R0Analog0.addSensorConfigs( [
         SensorConfig( "VRM_R3R0_ANLG0_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG0_VOUT_0V9", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.08, lowerCriticalVal=0.72
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG0_VOUT_0V75", "in4_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=0.9, lowerCriticalVal=0.6
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG0_VOUT_1V2", "in5_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.44, lowerCriticalVal=0.96
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG0_TEMP_0V9", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG0_TEMP_0V75", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG0_TEMP_1V2", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbIslR3R0Analog1 = Sensor( "0x51", "bp4a_isl68226", "SMB_ISL68226_R3R0_ANLG1",
                                incomingBusIndex=1 )
      smbIslR3R0Analog1.addSensorConfigs( [
         SensorConfig( "VRM_R3R0_ANLG1_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG1_VOUT_0V9", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.08, lowerCriticalVal=0.72
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG1_VOUT_0V75", "in4_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=0.9, lowerCriticalVal=0.6
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG1_VOUT_1V8", "in5_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=2.16, lowerCriticalVal=1.44
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG1_TEMP_0V9", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG1_TEMP_0V75", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM_R3R0_ANLG1_TEMP_1V8", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbRaa1 = Sensor( "0x61", "raa228228", "SMB_RAA228926_R3R1_CORE",
                        incomingBusIndex=1 )
      smbRaa1.addSensorConfigs( [
         SensorConfig( "VRM_R3R1_CORE_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_R3R1_CORE_VOUT_0V75", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.008, lowerCriticalVal=0.504
                       ) ),
         SensorConfig( "VRM_R3R1_CORE_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbIslR3R1Analog0 = Sensor( "0x52", "bp4a_isl68226", "SMB_ISL68226_R3R1_ANLG0",
                 incomingBusIndex=1 )
      smbIslR3R1Analog0.addSensorConfigs( [
         SensorConfig( "VRM_R3R1_ANLG0_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG0_VOUT_0V9", "in3_input",SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.08, lowerCriticalVal=0.72
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG0_VOUT_0V75", "in4_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=0.9, lowerCriticalVal=0.6
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG0_VOUT_1V2", "in5_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.44, lowerCriticalVal=0.96
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG0_TEMP_0V9", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG0_TEMP_0V75", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG0_TEMP_1V2", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbIslR3R1Analog1 = Sensor( "0x53", "bp4a_isl68226", "SMB_ISL68226_R3R1_ANLG1",
                                  incomingBusIndex=1 )
      smbIslR3R1Analog1.addSensorConfigs( [
         SensorConfig( "VRM_R3R1_ANLG1_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG1_VOUT_0V9", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.08, lowerCriticalVal=0.72
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG1_VOUT_0V75", "in4_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=0.9, lowerCriticalVal=0.6
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG1_VOUT_1V8", "in5_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=2.16, lowerCriticalVal=1.44
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG1_TEMP_0V9", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG1_TEMP_0V75", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "VRM_R3R1_ANLG1_TEMP_1V8", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbIslTopLeft = Sensor( "0x5A", "bp4a_isl68226", "SMB_ISL68226_OSFP_TL",
                              incomingBusIndex=1 )
      smbIslTopLeft.addSensorConfigs( [
         SensorConfig( "VRM_OSFP_TL_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_OSFP_TL_VOUT_3V3", "in3_input", SensorType.VOLTAGE,
                       compute="1.2*@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=3.7, lowerCriticalVal=2.64
                       ) ),
         SensorConfig( "VRM_OSFP_TL_TEMP_3V3", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbIslTopRight = Sensor( "0x5B", "bp4a_isl68226", "SMB_ISL68226_OSFP_TR",
                               incomingBusIndex=1 )
      smbIslTopRight.addSensorConfigs( [
         SensorConfig( "VRM_OSFP_TR_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_OSFP_TR_VOUT_3V3", "in3_input", SensorType.VOLTAGE,
                       compute="1.2*@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=3.7, lowerCriticalVal=2.64
                       ) ),
         SensorConfig( "VRM_OSFP_TR_TEMP_3V3", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbIslBackLeft = Sensor( "0x5C", "bp4a_isl68226", "SMB_ISL68226_OSFP_BL",
                               incomingBusIndex=1 )
      smbIslBackLeft.addSensorConfigs( [
         SensorConfig( "VRM_OSFP_BL_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_OSFP_BL_VOUT_3V3", "in3_input", SensorType.VOLTAGE,
                       compute="1.2*@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=3.7, lowerCriticalVal=2.64
                       ) ),
         SensorConfig( "VRM_OSFP_BL_TEMP_3V3", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbIslBackRight = Sensor( "0x5D", "bp4a_isl68226", "SMB_ISL68226_OSFP_BR",
                                incomingBusIndex=1 )
      smbIslBackRight.addSensorConfigs( [
         SensorConfig( "VRM_OSFP_BR_VIN", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "VRM_OSFP_BR_VOUT_3V3", "in3_input", SensorType.VOLTAGE,
                       compute="1.2*@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=3.7, lowerCriticalVal=2.64
                       ) ),
         SensorConfig( "VRM_OSFP_BR_TEMP_3V3", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=120.0, maxAlarmVal=115.0
                       ) )
      ] )

      smbUcd = Sensor( "0x11", "ucd90320", "SMB_UCD90320", incomingBusIndex=2 )
      smbUcd.addSensorConfigs( [
         SensorConfig( "DPM_12V", "in1_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=14.4, lowerCriticalVal=9.6
                       ) ),
         SensorConfig( "DPM_3V3_DKR", "in2_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=3.96, lowerCriticalVal=2.64
                       ) ),
         SensorConfig( "DPM_1V9_DKR", "in3_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=2.16, lowerCriticalVal=1.44
                       ) ),
         SensorConfig( "DPM_1V2_DKR", "in4_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=1.44, lowerCriticalVal=0.96
                       ) ),
         SensorConfig( "DPM_3V3", "in7_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=3.96, lowerCriticalVal=2.64
                       ) ),
         SensorConfig( "DPM_5V0", "in8_input", SensorType.VOLTAGE,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=6.0, lowerCriticalVal=4.0
                       ) )
      ] )

      smbFan0Tmp = Sensor( "0x48", "lm75", "FAN0_TMP75", incomingBusIndex=3 )
      smbFan0Tmp.addSensorConfigs( [
         SensorConfig( "FAN_BOARD0_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=85.0
                       ) )
      ] )

      smbFan0Cpld = FANCpld( "0x60", "fan_cpld0", "FAN0_CPLD", incomingBusIndex=3 )
      smbFan0Cpld.addFANRpms( 4, upperCriticalVal=14900.0, lowerCriticalVal=1100.0 )

      smbFan1Tmp = Sensor( "0x49", "lm75", "FAN1_TMP75", incomingBusIndex=3 )
      smbFan1Tmp.addSensorConfigs( [
         SensorConfig( "FAN_BOARD1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=85.0
                       ) )
      ] )

      smbFan1Cpld = FANCpld( "0x61", "fan_cpld1", "FAN1_CPLD", incomingBusIndex=3 )
      smbFan1Cpld.addFANRpms( 4, upperCriticalVal=14900.0, lowerCriticalVal=1100.0 )

      smbFan2Tmp = Sensor( "0x4A", "lm75", "FAN2_TMP75", incomingBusIndex=3 )
      smbFan2Tmp.addSensorConfigs( [
         SensorConfig( "FAN_BOARD2_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=95.0, maxAlarmVal=85.0
                       ) )
      ] )

      smbFan2Cpld = FANCpld( "0x62", "fan_cpld2", "FAN2_CPLD", incomingBusIndex=3 )
      smbFan2Cpld.addFANRpms( 4, upperCriticalVal=14900.0, lowerCriticalVal=1100.0 )

      self.addI2cDeviceConfigs( [
         smbCpld,
         smbMax,
         smbTmp,
         smbRaa0,
         smbIslR3R0Analog0,
         smbIslR3R0Analog1,
         smbRaa1,
         smbIslR3R1Analog0,
         smbIslR3R1Analog1,
         smbIslTopLeft,
         smbIslTopRight,
         smbIslBackLeft,
         smbIslBackRight,
         smbUcd,
         smbFan0Tmp,
         smbFan1Tmp,
         smbFan2Tmp,
         smbFan0Cpld,
         smbFan1Cpld,
         smbFan2Cpld
      ] )

      self.addPciDeviceConfigs( [
         *enumeratePciDeviceConfigs( 4, "SMB_FPGA{}", "0x3475", "0x0001", "0x3475",
                                     "0x0004" )
      ] )

      smbFpga0 = self.pciDeviceConfigs[ 0 ]
      smbFpga1 = self.pciDeviceConfigs[ 1 ]
      smbFpga2 = self.pciDeviceConfigs[ 2 ]
      smbFpga3 = self.pciDeviceConfigs[ 3 ]

      for fpgaNum, fpga in enumerate( self.pciDeviceConfigs ):
         fpga.addI2cAdapterConfigs( 5, "SMB_FPGA{}_I2C_MASTER{}", "0x8000" )
         fpga.addSpiMasterConfigs( [
            SpiMasterConfig(
               f"SMB_SPI{ fpgaNum }_MASTER0",
               "spi_master",
               -1,
               "0x7900",
               spiDeviceConfigs=[
                  Flash(
                     pmUnitScopedName=f"SMB_SPI{ fpgaNum }_MASTER0_DEVICE1",
                     chipSelect=0,
                     modalias="spidev",
                     maxSpeedHz=25000000
                  )
               ]
            )
         ] )

      smbFpga0.addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=1, portNumberSkipStep=4,
         smbusName="SMB_FPGA0_I2C_MASTER", smbusAccelStart=0, accelBusRange=( 0, 7 ),
         lanesCount=8
      )

      smbFpga1.addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=5, portNumberSkipStep=4,
         smbusName="SMB_FPGA1_I2C_MASTER", smbusAccelStart=0, accelBusRange=( 0, 7 ),
         lanesCount=8
      )

      smbFpga2.addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=65, portNumberSkipStep=4,
         smbusName="SMB_FPGA2_I2C_MASTER", smbusAccelStart=0, accelBusRange=( 0, 7 ),
         lanesCount=8
      )

      smbFpga3.addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=69, portNumberSkipStep=4,
         smbusName="SMB_FPGA3_I2C_MASTER", smbusAccelStart=0, accelBusRange=( 0, 7 ),
         lanesCount=8
      )

      smbFpga0.addInfoRomConfigs( "0x100" )
      smbFpga1.addInfoRomConfigs( "0x100" )
      smbFpga2.addInfoRomConfigs( "0x100" )
      smbFpga3.addInfoRomConfigs( "0x100" )

      smbFpga2.addLedCtrlConfigs( [
         LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
         LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
         LedConfig( ledName="PSU_STATUS_LED", offset="0x6070" ),
         LedConfig( ledName="SMB_STATUS_LED", offset="0x60a0" )
      ] )

      smbFpga2Master4 = smbFpga2.i2cAdapterConfigs[ 4 ]
      smbFpga3Master4 = smbFpga3.i2cAdapterConfigs[ 4 ]
      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="psu1_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbFpga3Master4.buses[ 0 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@1",
            presenceFileName="psu2_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbFpga2Master4.buses[ 0 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@2",
            presenceFileName="psu3_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbFpga3Master4.buses[ 1 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@3",
            presenceFileName="psu4_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbFpga2Master4.buses[ 1 ] ]
         ),
         *enumerateFANSlotConfigs( 12, "/SMB_SLOT@0/[FAN{}_CPLD]" )
      ] )


class Whistler( PlatformConfig ):
   def __init__( self ):
      super().__init__( "meru800bfa" )

      self.addPmUnitConfigs( [
         WhistlerSCM(),
         WhistlerSMB(),
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
   
      # 1. Set global PWM parameters from the JSON config
      fanServiceConfig.setPwmConfig(  pwmBoostOnNumDeadFan=1,
                                       pwmBoostOnNumDeadSensor=0,
                                       pwmBoostOnNoQsfpAfterInSec=31,
                                       pwmBoostValue=65,
                                       pwmTransitionValue=50,
                                       pwmLowerThreshold=7,
                                       pwmUpperThreshold=100 )

      # 2. Define the optics group with its specific temp-to-PWM map
      opticConfig = fanServiceConfig.addOpticConfig( "osfp_group_1", "QSFP" )
      opticConfig.addTempToPwmMap( 800, {
          "5": 40,
          "67": 41,
          "68": 50,
          "69": 67,
          "70": 80,
          "71": 100
      } )

      # 3. Define the sensors and their temp-to-PWM maps
      # Note: We use the unresolved names defined in WhistlerSMB (e.g., "INLET_TEMP")
      fanServiceConfig.addSensor( "INLET_TEMP", "THRIFT", {
          "15": 40,
          "110": 80
      } )
      fanServiceConfig.addSensor( "R3_0_TEMP", "THRIFT", {
          "15": 7,
          "70": 10,
          "80": 100
      } )
      fanServiceConfig.addSensor( "R3_1_TEMP", "THRIFT", {
          "15": 7,
          "70": 10,
          "80": 100
      } )
      fanServiceConfig.addSensor( "CPU_PACKAGE_TEMP", "THRIFT", {
         "15": 40,
         "80": 60,
         "90": 100
      } )

      # 4. Define the thermal control zones
      # An ASIC zone that controls fans 1-4
      fanServiceConfig.addZone(
         zoneName="asic_zone",
         sensorNames=[ "R3_0_TEMP", "R3_1_TEMP" ],
         fanNumbers=range( 1, 5 ),  # Fans 1 through 4
         slope=3
      )
      # A system-wide zone that controls fans 5-12
      fanServiceConfig.addZone(
         zoneName="system_zone",
         sensorNames=[ "CPU_PACKAGE_TEMP", "INLET_TEMP", "osfp_group_1" ],
         fanNumbers=range( 5, 13 ),  # Fans 5 through 12
         slope=3
      )
      self.PlatformFanServiceConfig = fanServiceConfig
