# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from dataclasses import dataclass, fields

@dataclass
class DataClassWithFieldGetter:
   @classmethod
   def getFields( cls ):
      return fields( cls )

@dataclass
class StaticMapping( DataClassWithFieldGetter ):
   """
   Representation of the end-to-end connection from a system side to the XCVR.
   System side is A, Xcvr side is Z.
   """
   # Linecard slot Id, 1 for fixed systems
   A_SLOT_ID : int
   # ASIC id on the system slot, Viper only has one J3, so always 1
   A_CHIP_ID : int
   # NPU
   A_CHIP_TYPE : str
   # ASIC serdes core ID
   A_CORE_ID : int
   # ASIC serdes core type, FE/NIF
   A_CORE_TYPE : str
   # 0,numLanes - numLanes per core is 8 on J3, so this value goes from 0,7.
   A_CORE_LANE : int
   # Physical tx trace corresponding to serdes core lane.
   A_PHYSICAL_TX_LANE : int
   # Physical rx trace corresponding to serdes core lane.
   A_PHYSICAL_RX_LANE : int
   # bool, is polarity swapped for tx trace.
   A_TX_POLARITY_SWAP : str
   # bool, is polarity swapped for rx trace.
   A_RX_POLARITY_SWAP : str
   # Transceiver system slot Id, 1 for fixed systems.
   Z_SLOT_ID : int
   # Transceiver front panel slot Id.
   Z_CHIP_ID : int
   # TRANSCEIVER
   Z_CHIP_TYPE : str
   # Always 0, since we don't have external PHYs or cores within a single XCVR slot.
   Z_CORE_ID : int
   # OSFP for Viper/Whistler
   Z_CORE_TYPE : str
   # 0-7, lane within the XCVR slot.
   Z_CORE_LANE : int
   # Physical tx trace corresponding to XCVR lane.
   Z_PHYSICAL_TX_LANE : int
   # Physical rx trace corresponding to XCVR lane.
   Z_PHYSICAL_RX_LANE : int
   # bool, is polarity swapped for tx trace.
   Z_TX_POLARITY_SWAP : str
   # bool, is polarity swapped for rx trace.
   Z_RX_POLARITY_SWAP : str

@dataclass
class PortProfileMapping( DataClassWithFieldGetter ):
   """
   Various mappings for a port in the system.
   """
   # Global port ID across all ASICs in the system.
   Global_PortID : int
   # Logical port ID used in the bcm soc properties.
   Logical_PortID : int
   # Port name used in the platform mapping.
   Port_Name : str
   # FBOSS Port profile (speed and other L1 attributes) supported by the port.
   # enum PortProfileID defined in fboss/agent/switch_config.thrift
   Supported_Port_Profiles : str
   # CoreId on ASIC that the port is attached to.
   Attached_CoreID: int
   # Core local portID assigned to this port.
   Attached_Core_PortID : int
   # NOTE: For Fabric ports, there is no core binding, the corresponding Attached_CoreId and Attached_Core_PortID can be left empty.
   # Virtual device ID for FE ASICs.
   Virtual_Device_ID : int

@dataclass
class SISettings( DataClassWithFieldGetter ):
   """
   SI settings for each logical lane.
   """
   # Linecard slot Id, 1 for fixed systems
   SLOT_ID : int
   # ASIC id on the system slot, Viper only has one J3, so always 1
   CHIP_ID : int
   # NPU
   CHIP_TYPE : str
   # ASIC serdes core ID
   CORE_ID : int
   # ASIC serdes core type, FE/NIF
   CORE_TYPE : str
   # 0,numLanes - numLanes per core is 8 on J3, so this value goes from 0,7.
   CORE_LANE : int
   # Lane speed in Mbps
   LANE_SPEED_mbps: int
   # Media type
   MEDIA_TYPE : str
   # Optics Vendor
   OPTICS_VENDOR : str
   # NIC Vendor
   NIC_VENDOR : str
   # Cable length (in meters)
   CABLE_LENGTH_m : float
   # TX Tap Settings
   TX_PRE3 : int
   TX_PRE2 : int
   TX_PRE1 : int
   TX_MAIN : int
   TX_POST1 : int
   TX_POST2 : int
   TX_POST3 : int
   # RX Settings
   RX_CTLE_CODE : str
   RX_DSP_MODE : str
   RX_AFE_TRIM : str
