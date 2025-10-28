# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from GenerateConfigsAndDiagrams.BaseConfigs import (
   enumerateFANSlotConfigs,
   EmbeddedSensorConfig,
   FANUnit,
   FANCpld,
   FanServiceConfig,
   Flash,
   I2cMux,
   PciDeviceConfig,
   PlatformConfig,
   PSUUnit,
   Sensor,
   SensorConfig,
   SensorType,
   SCMUnit,
   SlotConfig,
   SMBCpld,
   SMBUnit,
   SpiMasterConfig,
   Thresholds,
)


class ThrasherSCM( SCMUnit ):
   def __init__( self ):
      super().__init__()

      self.setSlotTypeConfig(
         idPromConfigBusName="Synopsys DesignWare I2C adapter",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360,
         createIdpromSymlink=True,
      )

      # Note that the PCIe device ID for the Thrasher SCM FPGA is currently the
      # same as Fairywren.
      self.scmFpga = PciDeviceConfig( "SCM_FPGA", "0x3475", "0x0001",
                                      "0x3475", "0x0008",
                                      symlinkDeviceName="SCM_FPGA")
      self.scmFpga.addInfoRomConfigs( "0x100" )
      self.addPciDeviceConfigs( [ self.scmFpga ] )

      self.scmFpga.addI2cAdapterConfigs( 2, "SCM_I2C_MASTER{}", "0x8000" )
      self.scmI2cMaster0 = self.scmFpga.i2cAdapterConfigs[ 0 ]
      self.scmI2cMaster1 = self.scmFpga.i2cAdapterConfigs[ 1 ]

      acpiTemp = EmbeddedSensorConfig(
                        pmUnitScopedName="ACPI_TEMP",
                        sysfsPath="/sys/class/thermal/thermal_zone0"
      )
      acpiTemp.addSensorConfigs( [
         SensorConfig( "ACPI_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                           upperCriticalVal=105.0, maxAlarmVal=95.0
                       ) )
      ] )

      nvmeTemp = EmbeddedSensorConfig( pmUnitScopedName="NVME_TEMP",
                                       sysfsPath="/sys/class/nvme/nvme0" )
      nvmeTemp.addSensorConfigs( [
         SensorConfig( "NVME_COMPOSITE_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0", prependPmUnit=False,
                       thresholds=Thresholds(
                          upperCriticalVal=80.0
                       ) )
      ] )
      self.addEmbeddedSensorConfigs( [ acpiTemp, nvmeTemp ] )

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

class BanffSMB( SMBUnit ):
   def __init__( self ):
      super().__init__()

      self.fanServiceSensorConfigs = {}

      self.setSlotTypeConfig(
         numOutgoingI2cBuses=3,
         idPromConfigBusName="INCOMING@0",
         idPromConfigAddress="0x50",
         idPromConfigKernelDeviceName="24c512",
         idPromConfigOffset=15360,
         createIdpromSymlink=True,
      )

      smbCpld = SMBCpld( "0x23", "glath06a-64o_cpld", "SMB_CPLD",
                         incomingBusIndex=0 )

      smbTempSensor = Sensor( "0x4D", "max6581", "SMB_MAX6581",
                              incomingBusIndex=0 )
      smbTempSensor.addSensorConfigs( [
         SensorConfig( "SMB_BOARD_FRONT_BOTTOM_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=80.0
                       ) ),
         SensorConfig( "TH6_DIODE_1_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=115.0
                       ) ),
         SensorConfig( "TH6_DIODE_2_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=115.0
                       ) ),
         # temp4_input is unused
         SensorConfig( "SMB_BOARD_FRONT_1_TEMP", "temp5_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=80.0
                       ) ),
         SensorConfig( "SMB_BOARD_FRONT_2_TEMP", "temp6_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=80.0
                       ) ),
         SensorConfig( "SMB_BOARD_REAR_1_TEMP", "temp7_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=80.0
                       ) ),
         SensorConfig( "SMB_BOARD_REAR_2_TEMP", "temp8_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=80.0
                       ) )
      ] )

      pwrTempSensor = Sensor( "0x4D", "max6581", "SMB_PWR_MAX6581",
                              incomingBusIndex=1 )
      pwrTempSensor.addSensorConfigs( [
         # TODO: BUG1304496: Add Sundance descriptions and limits when available.
         SensorConfig( "SMB_PWR_BOARD_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=80.0
                       ) ),
         SensorConfig( "SMB_PWR_BOARD_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=115.0, maxAlarmVal=105.0
                       ) ),
         SensorConfig( "SMB_PWR_BOARD_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=115.0, maxAlarmVal=105.0
                       ) ),
         # temp4_input is unused
         SensorConfig( "SMB_PWR_BOARD_4_TEMP", "temp5_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=80.0
                       ) ),
         SensorConfig( "SMB_PWR_BOARD_5_TEMP", "temp6_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=80.0
                       ) ),
         SensorConfig( "SMB_PWR_BOARD_6_TEMP", "temp7_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=90.0, maxAlarmVal=80.0
                       ) ),
         SensorConfig( "SMB_PWR_BOARD_7_TEMP", "temp8_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                           upperCriticalVal=110.0, maxAlarmVal=100.0
                       ) )
      ] )

      th6CoreVrm = Sensor( "0x70", "xdpe1a2g5b", "SMB_XDPE_TH6_POS0V75_CORE",
                           incomingBusIndex=1 )
      th6CoreVrm.addSensorConfigs( [
         SensorConfig( "TH6_POS0V75_CORE_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V75_CORE_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V75_CORE_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_CORE_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_CORE_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_CORE_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_CORE_PIN", "power1_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_CORE_POUT", "power3_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_CORE_IIN", "curr1_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "TH6_POS0V75_CORE_IOUT", "curr3_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )

      th6PhyCoreVrm1 = Sensor( "0x58", "xdpe1b284b",
                               "SMB_XDPE_TH6_POS0V75_PHYCORE_01",
                               incomingBusIndex=1 )
      th6PhyCoreVrm1.addSensorConfigs( [
         SensorConfig( "TH6_POS0V75_PHYCORE_01_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_0_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_1_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V75_PHYCORE_01_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_01_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_01_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_01_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_0_POUT", "power3_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_1_POUT", "power4_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_0_IOUT", "curr3_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_1_IOUT", "curr4_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )

      th6PhyCoreVrm2 = Sensor( "0x5A", "xdpe1b284b",
                               "SMB_XDPE_TH6_POS0V75_PHYCORE_23",
                               incomingBusIndex=1 )
      th6PhyCoreVrm2.addSensorConfigs( [
         SensorConfig( "TH6_POS0V75_PHYCORE_23_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_2_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_3_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V75_PHYCORE_23_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_23_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_23_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_23_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_2_POUT", "power3_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_3_POUT", "power4_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_2_IOUT", "curr3_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_3_IOUT", "curr4_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )

      th6PhyCoreVrm3 = Sensor( "0x5C", "xdpe1b284b",
                               "SMB_XDPE_TH6_POS0V75_PHYCORE_45",
                               incomingBusIndex=1 )
      th6PhyCoreVrm3.addSensorConfigs( [
         SensorConfig( "TH6_POS0V75_PHYCORE_45_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_4_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_5_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V75_PHYCORE_45_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_45_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_45_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_45_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_4_POUT", "power3_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_5_POUT", "power4_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_4_IOUT", "curr3_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_5_IOUT", "curr4_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )

      th6PhyCoreVrm4 = Sensor( "0x5E", "xdpe1b284b",
                               "SMB_XDPE_TH6_POS0V75_PHYCORE_67",
                               incomingBusIndex=1 )
      th6PhyCoreVrm4.addSensorConfigs( [
         SensorConfig( "TH6_POS0V75_PHYCORE_67_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_6_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_7_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V75_PHYCORE_67_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_67_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_67_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_67_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_PHYCORE_6_POUT", "power3_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_7_POUT", "power4_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_6_IOUT", "curr3_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "TH6_POS0V75_PHYCORE_7_IOUT", "curr4_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )
      th6TrvddVrm1 = Sensor( "0x60", "xdpe1b284b",
                             "SMB_XDPE_TH6_POS0V72_TRVDD_01",
                             incomingBusIndex=1 )
      th6TrvddVrm1.addSensorConfigs( [
         SensorConfig( "TH6_POS0V72_TRVDD_01_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_0_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=880, lowerCriticalVal=720
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_1_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=880, lowerCriticalVal=720
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V72_TRVDD_01_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_01_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_01_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_01_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) )
      ] )

      th6TrvddVrm2 = Sensor( "0x62", "xdpe1b284b",
                             "SMB_XDPE_TH6_POS0V72_TRVDD_23",
                             incomingBusIndex=1 )
      th6TrvddVrm2.addSensorConfigs( [
         SensorConfig( "TH6_POS0V72_TRVDD_23_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_2_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=880, lowerCriticalVal=720
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_3_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=880, lowerCriticalVal=720
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V72_TRVDD_23_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_23_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_23_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_23_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) )
      ] )

      th6TrvddVrm3 = Sensor( "0x64", "xdpe1b284b",
                             "SMB_XDPE_TH6_POS0V72_TRVDD_45",
                             incomingBusIndex=1 )
      th6TrvddVrm3.addSensorConfigs( [
         SensorConfig( "TH6_POS0V72_TRVDD_45_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_4_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=880, lowerCriticalVal=720
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_5_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=880, lowerCriticalVal=720
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V72_TRVDD_45_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_45_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_45_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_45_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) )
      ] )

      th6TrvddVrm4 = Sensor( "0x66", "xdpe1b284b",
                             "SMB_XDPE_TH6_POS0V72_TRVDD_67",
                             incomingBusIndex=1 )
      th6TrvddVrm4.addSensorConfigs( [
         SensorConfig( "TH6_POS0V72_TRVDD_67_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_6_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=880, lowerCriticalVal=720
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_7_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=880, lowerCriticalVal=720
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V72_TRVDD_67_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_67_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_67_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V72_TRVDD_67_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) )
      ] )

      th6TrvddVrm5 = Sensor( "0x68", "xdpe1b284b",
                             "SMB_XDPE_TH6_POS0V75_TRVDD_01",
                             incomingBusIndex=1 )
      th6TrvddVrm5.addSensorConfigs( [
         SensorConfig( "TH6_POS0V75_TRVDD_01_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V75_TRVDD_0_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=825, lowerCriticalVal=675
                       ) ),
         SensorConfig( "TH6_POS0V75_TRVDD_1_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=825, lowerCriticalVal=675
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TH6_POS0V75_TRVDD_01_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_TRVDD_01_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_TRVDD_01_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V75_TRVDD_01_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) )
      ] )

      th6TrvddVrm6 = Sensor( "0x6A", "xdpe1b284b",
                             "SMB_XDPE_TH6_POS0V9_TRVDD_01",
                             incomingBusIndex=1 )
      th6TrvddVrm6.addSensorConfigs( [
         SensorConfig( "TH6_POS0V9_TRVDD_01_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS0V9_TRVDD_0_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=990, lowerCriticalVal=810
                       ) ),
         SensorConfig( "TH6_POS0V9_TRVDD_1_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=990, lowerCriticalVal=810
                       ) ),
         # TODO: BUG1304496: update temp limits when available.
         SensorConfig( "TTH6_POS0V9_TRVDD_01_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V9_TRVDD_01_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V9_TRVDD_01_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V9_TRVDD_01_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS0V9_TRVDD_0_POUT", "power3_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V9_TRVDD_1_POUT", "power4_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "TH6_POS0V9_TRVDD_0_IOUT", "curr3_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "TH6_POS0V9_TRVDD_1_IOUT", "curr4_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )
      th6RvddVrm1 = Sensor( "0x48", "tda38740a", "SMB_TDA_TH6_POS1V5_RVDD_0",
                            incomingBusIndex=1 )
      th6RvddVrm1.addSensorConfigs( [
         SensorConfig( "TH6_POS1V5_RVDD_0_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS1V5_RVDD_0_VOUT", "in2_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=1650, lowerCriticalVal=1350
                       ) ),
         SensorConfig( "TH6_POS1V5_RVDD_0_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS1V5_RVDD_0_IIN", "curr1_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "TH6_POS1V5_RVDD_0_IOUT", "curr2_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )

      th6RvddVrm2 = Sensor( "0x49", "tda38740a", "SMB_TDA_TH6_POS1V5_RVDD_1",
                            incomingBusIndex=1 )
      th6RvddVrm2.addSensorConfigs( [
         SensorConfig( "TH6_POS1V5_RVDD_1_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "TH6_POS1V5_RVDD_1_VOUT", "in2_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=1650, lowerCriticalVal=1350
                       ) ),
         SensorConfig( "TH6_POS1V5_RVDD_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "TH6_POS1V5_RVDD_1_IIN", "curr1_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "TH6_POS1V5_RVDD_1_IOUT", "curr2_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )

      opticsLeftVrm = Sensor( "0x72", "xdpe1a2g5b", "SMB_TDA_POS3V3_OPTICS_LEFT",
                              incomingBusIndex=1 )
      opticsLeftVrm.addSensorConfigs( [
         SensorConfig( "POS3V3_OPTICS_LEFT_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "POS3V3_OPTICS_LEFT_VOUT", "in3_input", SensorType.VOLTAGE,
                       compute="2.071*@",
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) ),
         SensorConfig( "POS3V3_OPTICS_LEFT_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "POS3V3_OPTICS_LEFT_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "POS3V3_OPTICS_LEFT_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "POS3V3_OPTICS_LEFT_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "POS3V3_OPTICS_LEFT_PIN", "power1_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "POS3V3_OPTICS_LEFT_POUT", "power3_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "POS3V3_OPTICS_LEFT_IIN", "curr1_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "POS3V3_OPTICS_LEFT_IOUT", "curr3_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )

      opticsRightVrm = Sensor( "0x74", "xdpe1a2g5b", "SMB_TDA_POS3V3_OPTICS_RIGHT",
                               incomingBusIndex=1 )
      opticsRightVrm.addSensorConfigs( [
         SensorConfig( "POS3V3_OPTICS_RIGHT_VIN", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "POS3V3_OPTICS_RIGHT_VOUT", "in3_input", SensorType.VOLTAGE,
                       compute="2.071*@",
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) ),
         SensorConfig( "POS3V3_OPTICS_RIGHT_1_TEMP", "temp1_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "POS3V3_OPTICS_RIGHT_2_TEMP", "temp2_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "POS3V3_OPTICS_RIGHT_3_TEMP", "temp3_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "POS3V3_OPTICS_RIGHT_4_TEMP", "temp4_input", SensorType.TEMP,
                       compute="@/1000.0",
                       thresholds=Thresholds(
                          upperCriticalVal=125.0, maxAlarmVal=115.0
                       ) ),
         SensorConfig( "POS3V3_OPTICS_RIGHT_PIN", "power1_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "POS3V3_OPTICS_RIGHT_POUT", "power3_input", SensorType.POWER,
                       compute="@/1000000.0"
                       ),
         SensorConfig( "POS3V3_OPTICS_RIGHT_IIN", "curr1_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       ),
         SensorConfig( "POS3V3_OPTICS_RIGHT_IOUT", "curr3_input", SensorType.CURRENT,
                       compute="@/1000.0"
                       )
      ] )

      smbUcd = Sensor( "0x11", "glath06a_aucd90320", "SMB_UCD90320",
                       incomingBusIndex=2 )
      smbUcd.addSensorConfigs( [
         SensorConfig( "DPM_POS12V_VOUT", "in1_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=13200, lowerCriticalVal=10800
                       ) ),
         SensorConfig( "DPM_POS3V3_VOUT", "in2_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) ),
         SensorConfig( "DPM_POS1V8_VOUT", "in3_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=1980, lowerCriticalVal=1620
                       ) ),
         SensorConfig( "DPM_POS0V75_TRVDD_0_VOUT", "in4_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=825, lowerCriticalVal=675
                       ) ),
         SensorConfig( "DPM_POS0V75_TRVDD_1_VOUT", "in5_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=825, lowerCriticalVal=675
                       ) ),
         SensorConfig( "DPM_POS0V9_TRVDD_0_VOUT", "in6_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=990, lowerCriticalVal=810
                       ) ),
         SensorConfig( "DPM_POS0V9_TRVDD_1_VOUT", "in7_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=990, lowerCriticalVal=810
                       ) ),
         SensorConfig( "DPM_POS1V5_RVDD_0_VOUT", "in8_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=1650, lowerCriticalVal=1350
                       ) ),
         SensorConfig( "DPM_POS1V5_RVDD_1_VOUT", "in9_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=1650, lowerCriticalVal=1350
                       ) ),
         SensorConfig( "DPM_POS3V3_OPTICS_LEFT_VOUT", "in10_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) ),
         SensorConfig( "DPM_POS3V3_OPTICS_RIGHT_VOUT", "in11_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) ),
         SensorConfig( "DPM_POS5V_VOUT", "in12_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=5500, lowerCriticalVal=4500
                       ) ),
         SensorConfig( "DPM_POS0V75_CORE_VOUT", "in13_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         SensorConfig( "DPM_POS0V75_PHYCORE_7_VOUT", "in14_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=975, lowerCriticalVal=525
                       ) ),
         SensorConfig( "DPM_POS0V72_TRVDD_7_VOUT", "in15_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=880, lowerCriticalVal=720
                       ) ),
         SensorConfig( "DPM_POS3V3_RUNDLE_VOUT", "in16_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) ),
         SensorConfig( "DPM_POS5V0_SNOWFRONT_VOUT", "in17_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=5500, lowerCriticalVal=4500
                       ) ),
         SensorConfig( "DPM_POS3V3_SNOWFRONT_VOUT", "in18_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) ),
         SensorConfig( "DPM_POS5V0_SUNDANCE_VOUT", "in19_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=5500, lowerCriticalVal=4500
                       ) ),
         SensorConfig( "DPM_POS3V3_SUNDANCE_VOUT", "in20_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) ),
         SensorConfig( "DPM_POS5V0_SUNSHINE_A_VOUT", "in21_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=5500, lowerCriticalVal=4500
                       ) ),
         SensorConfig( "DPM_POS3V3_SUNSHINE_A_VOUT", "in22_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) ),
         SensorConfig( "DPM_POS5V0_SUNSHINE_B_VOUT", "in23_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=5500, lowerCriticalVal=4500
                       ) ),
         SensorConfig( "DPM_POS3V3_SUNSHINE_B_VOUT", "in24_input", SensorType.VOLTAGE,
                       thresholds=Thresholds(
                          upperCriticalVal=3630, lowerCriticalVal=2970
                       ) )
      ] )

      smbMux = I2cMux( "0x75", "pca9548", "SMB_MUX", incomingBusIndex=2,
                       numOutgoingChannels=8 )

      smbFanCpld = FANCpld( "0x60", "glath06a64o_fancpld", "FAN_CPLD",
                            incomingBusIndex=3 )
      # BUG1262914: Banff fans are capable of 15400 RPM, however, the Banff
      # CPLD limits them to ~10000 RPM. Apply this cap in SW, so the fans
      # can still be driven to "100%"
      smbFanCpld.addFANRpms( 8, upperCriticalVal=10000.0, lowerCriticalVal=2000.0 )

      self.addI2cDeviceConfigs( [
         smbCpld,
         smbTempSensor,
         pwrTempSensor,
         th6CoreVrm,
         th6PhyCoreVrm1,
         th6PhyCoreVrm2,
         th6PhyCoreVrm3,
         th6PhyCoreVrm4,
         th6TrvddVrm1,
         th6TrvddVrm2,
         th6TrvddVrm3,
         th6TrvddVrm4,
         th6TrvddVrm5,
         th6TrvddVrm6,
         th6RvddVrm1,
         th6RvddVrm2,
         opticsLeftVrm,
         opticsRightVrm,
         smbUcd,
         smbMux,
         smbFanCpld,
      ] )

      self.addPciDeviceConfigs( [
         PciDeviceConfig( "SMB_FPGA0", "0x3475", "0x0001", "0x3475", "0x0010",
                         symlinkDeviceName="SMB_FPGA0" ),
         PciDeviceConfig( "SMB_FPGA1", "0x3475", "0x0001", "0x3475", "0x0011",
                         symlinkDeviceName="SMB_FPGA1" ),
      ] )

      smbFpga0 = self.pciDeviceConfigs[ 0 ]
      smbFpga0.addInfoRomConfigs( "0x100" )
      smbFpga0.addI2cAdapterConfigs( 9, "SMB_FPGA{}_I2C_MASTER{}", "0x8000",
                                     numChannelsPerAdapter=4 )
      smbFpga0.addSpiMasterConfigs( [
         SpiMasterConfig( "SMB_SPI0_MASTER0", "spi_master", -1,
                           "0x7900",
                           spiDeviceConfigs=[ Flash(
                              pmUnitScopedName="SMB_SPI0_MASTER0_DEVICE1",
                              chipSelect=0,
                              modalias="spidev",
                              maxSpeedHz=25000000
                           ) ]
                        )
      ] )
      smbFpga0.addXcvrCtrlConfigs( numConfigs=32, basePortNumber=1,
                                  portNumberSkipStep=4, ledsPerXcvr=2,
                                  smbusAccelStart=0,
                                  smbusName="SMB_FPGA0_I2C_MASTER",
                                  xcvrBaseOffset="0xA010", accelBusRange=( 0, 3 ),
                                  lanesCount=8 )

      smbFpga1 = self.pciDeviceConfigs[ 1 ]
      smbFpga1.addInfoRomConfigs( "0x100" )
      smbFpga1.addI2cAdapterConfigs( 8, "SMB_FPGA{}_I2C_MASTER{}", "0x8000",
                                     numChannelsPerAdapter=4 )
      smbFpga1.addSpiMasterConfigs( [
         SpiMasterConfig( "SMB_SPI1_MASTER0", "spi_master", -1,
                           "0x7900",
                           spiDeviceConfigs=[ Flash(
                              pmUnitScopedName="SMB_SPI1_MASTER0_DEVICE1",
                              chipSelect=0,
                              modalias="spidev",
                              maxSpeedHz=25000000
                           ) ]
                        ),
         SpiMasterConfig( "SMB_SPI1_MASTER1", "spi_master", -1,
                           "0x7A00",
                           spiDeviceConfigs=[ Flash(
                              pmUnitScopedName="SMB_SPI1_MASTER1_DEVICE1",
                              chipSelect=0,
                              modalias="spidev",
                              maxSpeedHz=25000000
                           ) ]
                        )
      ] )
      smbFpga1.addXcvrCtrlConfigs( numConfigs=32, basePortNumber=5,
                                  portNumberSkipStep=4, ledsPerXcvr=2,
                                  smbusAccelStart=0,
                                  smbusName="SMB_FPGA1_I2C_MASTER",
                                  xcvrBaseOffset="0xA010", accelBusRange=( 0, 3 ),
                                  lanesCount=8 )

      self.addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="psu1_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbMux.buses[ 0 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@1",
            presenceFileName="psu2_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbMux.buses[ 1 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@2",
            presenceFileName="psu3_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbMux.buses[ 2 ] ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@3",
            presenceFileName="psu4_present",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBuses=[ smbMux.buses[ 3 ] ]
         ),
         *enumerateFANSlotConfigs( 8, "/SMB_SLOT@0/[FAN_CPLD]", fansPerCpld=8 ),
      ] )


class Banff( PlatformConfig ):
   # TODO: this is due to the current dmidecode output on Thrasher; there's no
   # Aboot18 support for aconfctl to override the default value.
   codename = 'REDSTART-RMB'

   def __init__( self ):
      super().__init__( self.codename )
      self.addPmUnitConfigs( [
         ThrasherSCM(),
         BanffSMB(),
         PSUUnit(),
         FANUnit()
      ] )

      self.addI2cAdaptersFromCpu( [ "Synopsys DesignWare I2C adapter" ] )
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
      
      fanServiceConfig = FanServiceConfig()
      self.PlatformFanServiceConfig = fanServiceConfig
