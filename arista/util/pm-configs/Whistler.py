# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from BaseConfigs import (
   PlatformConfig,
   SlotTypeConfig, 
   I2cDeviceConfig, 
   SlotConfig, 
   LedConfig,
   SpiMasterConfig, 
   SpiDeviceConfig,
   enumerateFANSlotConfigs, 
   enumeratePciDeviceConfigs
)

from BaseConfigs import SCMUnit, SMBUnit, PSUUnit, FANUnit


class Whistler( PlatformConfig ): 

   def __init__( self ):
      super().__init__( "meru800bfa" )

      self.addSlotTypeConfigs( [
         SlotTypeConfig( 
            slotName="SCM_SLOT", 
            idPromConfigBusName="SMBus I801 adapter at 1000",
            idPromConfigAddress="0x50",
            idpromConfigKernelDeviceName="24c512",
            idPromConfigOffset=15360
         ),
         SlotTypeConfig(
            slotName="SMB_SLOT",
            numOutgoingI2cBuses=4,
            idPromConfigBusName="INCOMING@0",
            idPromConfigAddress="0x52",
            idpromConfigKernelDeviceName="24c512",
            idPromConfigOffset=15360
         ),
         SlotTypeConfig(
            slotName="PSU_SLOT",
            numOutgoingI2cBuses=1
         ),
         SlotTypeConfig(
            slotName="FAN_SLOT"
         )
      ] )

      self.addPmUnitConfigs( [
         SCMUnit(),
         SMBUnit(),
         PSUUnit(),
         FANUnit()
      ] )

      self.kmodsSettings[ "bspKmodsToReload" ] = \
         "scd-xcvr, scd-spi, scd-leds, scd-smbus, dsf-fan-cpld, decker-cpld"

      self.pmUnitConfigs[ 0 ].outgoingSlotConfigs[ 0 ].outgoingI2cBusNames = [ 
         "SCM_I2C_MASTER1@0", 
         "SCM_I2C_MASTER1@1",
         "SCM_I2C_MASTER1@2",
         "SCM_I2C_MASTER1@3" 
      ]

      self.pmUnitConfigs[ 1 ].addI2cDeviceConfigs( [
         I2cDeviceConfig( "INCOMING@0", "0x23", "decker_cpld", "SMB_CPLD" ),
         I2cDeviceConfig( "INCOMING@0", "0x4D", "max6581", "SMB_MAX6581" ),
         I2cDeviceConfig( "INCOMING@0", "0x48", "tmp75", "SMB_TMP75" ),
         I2cDeviceConfig( "INCOMING@1", "0x60", "raa228228", 
                          "SMB_RAA228926_R3R0_CORE" ),
         I2cDeviceConfig( "INCOMING@1", "0x50", "isl68226", 
                          "SMB_ISL68226_R3R0_ANLG0" ),
         I2cDeviceConfig( "INCOMING@1", "0x51", "isl68226", 
                          "SMB_ISL68226_R3R0_ANLG1" ),
         I2cDeviceConfig( "INCOMING@1", "0x61", "raa228228", 
                          "SMB_RAA228926_R3R1_CORE" ),
         I2cDeviceConfig( "INCOMING@1", "0x52", "isl68226", 
                          "SMB_ISL68226_R3R1_ANLG0" ),
         I2cDeviceConfig( "INCOMING@1", "0x53", "isl68226", 
                          "SMB_ISL68226_R3R1_ANLG1" ),
         I2cDeviceConfig( "INCOMING@1", "0x5A", "isl68226", "SMB_ISL68226_OSFP_TL" ),
         I2cDeviceConfig( "INCOMING@1", "0x5B", "isl68226", "SMB_ISL68226_OSFP_TR" ),
         I2cDeviceConfig( "INCOMING@1", "0x5C", "isl68226", "SMB_ISL68226_OSFP_BL" ),
         I2cDeviceConfig( "INCOMING@1", "0x5D", "isl68226", "SMB_ISL68226_OSFP_BR" ),
         I2cDeviceConfig( "INCOMING@2", "0x11", "ucd90320", "SMB_UCD90320" ),
         I2cDeviceConfig( "INCOMING@3", "0x48", "tmp75", "FAN0_TMP75" ),
         I2cDeviceConfig( "INCOMING@3", "0x60", "oasis_cpld0", "FAN0_CPLD" ),
         I2cDeviceConfig( "INCOMING@3", "0x49", "tmp75", "FAN1_TMP75" ),
         I2cDeviceConfig( "INCOMING@3", "0x61", "oasis_cpld1", "FAN1_CPLD" ),
         I2cDeviceConfig( "INCOMING@3", "0x4A", "tmp75", "FAN2_TMP75" ),
         I2cDeviceConfig( "INCOMING@3", "0x62", "oasis_cpld2", "FAN2_CPLD" )
      ] )

      self.pmUnitConfigs[ 1 ].addOutgoingSlotConfigs( [
         SlotConfig(
            slotName="PSU_SLOT@0",
            presenceFileName="psu1_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBusNames=[ "SMB_FPGA3_I2C_MASTER4@0" ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@1",
            presenceFileName="psu2_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBusNames=[ "SMB_FPGA2_I2C_MASTER4@0" ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@2",
            presenceFileName="psu3_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBusNames=[ "SMB_FPGA3_I2C_MASTER4@1" ]
         ),
         SlotConfig(
            slotName="PSU_SLOT@3",
            presenceFileName="psu4_prsnt",
            presenceDevicePath="/SMB_SLOT@0/[SMB_FPGA0]",
            outgoingI2cBusNames=[ "SMB_FPGA2_I2C_MASTER4@1" ]
         ),
         *enumerateFANSlotConfigs( 12, "/SMB_SLOT@0/[FAN*_CPLD]" )
      ] )

      self.pmUnitConfigs[ 1 ].addPciDeviceConfigs( [
         *enumeratePciDeviceConfigs( 4, "SMB_FPGA*", "0x3475", "0x0001", "0x3475", 
                                     "0x0004" )
      ] )

      for pciConfig in self.pmUnitConfigs[ 1 ].pciDeviceConfigs:
         pciConfig.addI2cAdapterConfigs( 5, "SMB_FPGA*_I2C_MASTER*", "0x8000" )
         pciConfig.addSpiMasterConfigs( [
            SpiMasterConfig( 
               "SMB_SPI_MASTER0", 
               "spi_master", 
               -1, 
               "0x7900",
               spiDeviceConfigs=[ 
                  SpiDeviceConfig(
                     pmUnitScopedName="SMB_SPI_MASTER0_DEVICE1",
                     chipSelect=0,
                     modalias="spidev",
                     maxSpeedHz=25000000
                  ) 
               ]
            )
         ] )

      self.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 0 ].addXcvrCtrlConfigs( 
         numConfigs=32, basePortNumber=1, whistler=True
      )
      self.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 1 ].addXcvrCtrlConfigs( 
         numConfigs=32, basePortNumber=5, whistler=True
      )
      self.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 2 ].addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=65, whistler=True
      )
      self.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 3 ].addXcvrCtrlConfigs(
         numConfigs=32, basePortNumber=69, whistler=True
      )

      self.pmUnitConfigs[ 1 ].pciDeviceConfigs[ 2 ].addLedCtrlConfigs( [
         LedConfig( ledName="SYSTEM_STATUS_LED", offset="0x6050" ),
         LedConfig( ledName="FAN_STATUS_LED", offset="0x6060" ),
         LedConfig( ledName="PSU_STATUS_LED", offset="0x6070" ),
         LedConfig( ledName="SMB_STATUS_LED", offset="0x60a0" )
      ] )

      self.pmUnitConfigs[ 2 ].addI2cDeviceConfigs( [
         I2cDeviceConfig( "INCOMING@0", "0x58", "pmbus", "PSU_PMBUS" )
      ] )

      for pmConfig in self.pmUnitConfigs:
         pmConfig.populateSymlinkToDevicePaths( self.platformName )