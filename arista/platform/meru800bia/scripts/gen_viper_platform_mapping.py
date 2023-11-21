#!/bin/env python3
# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

"""
Author : seerpini@arista.com
Script for generating the Viper vendor mappings.
Assumptions:
    - Each fabric serdes is enumerated as a 100G port. Supported profiles 36, 37 correspond to 100G optical and copper.
    - Each front panel port is enumerated as 400G-4 or 2x400G-4.
Output:
    - Vendor mappings (static and port profile mapping) and bcm configuration is
      generated.
"""

# Variables to control the behavior for this script.
# Existing mappings at a port level are not replaced if preserveExistingMappings=True
preserveExistingMappings = True
# Number of ASICs in the system
numAsics = 1
# Number of serdes per serdes core. Peregrine 8x100G serdes core on J3.
numSerdesPerCore = 8
# Logical port base in the SDK for NIF ports.
nifPortBase = 2
# Total number of NIF ports. Since we are operating in either 400G-4 or 800G-8 and we
# only plan to use the first port in the slot in 400G-4 mode, we have a total of 18
# front panel NIF ports.
numNifSerdesCores = 18
# Logical port base in the SDK for fabric ports.
fabricPortBase = 1024
# Total number of fabric ports assuming that each fabric serdes is enumerated as a
# separate port.
numFabricSerdesCores = 20
# Print debug information
debug = False

# Viper has a non-linear front panel slot to port type mapping.
def frontPanelSlotToPortType( slot ):
   assert 1 <= slot <= 38
   if 11 <= slot <= 28:
      # The 18 ports in between are ethernet ports.
      return "eth"
   else:
      # First 10 ports and last 10 ports on the front panel are fabric ports.
      return "fab"

nifSerdesCoreToAsicCore = {
      # serdes Octet : J3 core
      0 : 0,
      1 : 0,
      2 : 0,
      3 : 0,
      4 : 0,
      5 : 1,
      6 : 1,
      7 : 1,
      8 : 1,
      9 : 2,
      10 : 2,
      11 : 2,
      12 : 2,
      13 : 3,
      14 : 3,
      15 : 3,
      16 : 3,
      17 : 3,
}

# Assuming 100G lanes, number of lanes required by each supported port profile.
numLanesFromSupportedProfile = {
      "11" : 1,
      "24" : 4,
      "36" : 1,
      "37" : 1,
      "38" : 4,
      "39" : 8,
      "41" : 1,
      "42" : 1,
}

supportedProfilesByPortType = {
      'eth' :  [ '24', '38', '39', ],
      'fab' :  [ '36', '37', '41', '42'],
}

asicSerdesMappings = []
for asic in range( numAsics ):
   asicSerdesMappings.append( {} )
# For Viper, since each serdes core maps to a single OSFP port, we can figure out the
# lanes from reverse mapping the line side lane to the system side serdes lane.
# This also means that the logical lanes on the ASIC side always match the OSFP front
# panel lanes. The lane maps tell us how a logical lane maps to rx, tx physical
# lanes.
with open( "AsicToXcvrTraceInfoP1.csv" ) as fh:
   for line in fh:
      if line.startswith( "System" ):
         continue
      asic, systemSerdesId, frontPanelSlot, lineSideLane, _, connectionType, polaritySwap = line.rstrip().split(",")
      asic = int( asic )
      systemSerdesId = int( systemSerdesId )
      systemSideLane = systemSerdesId
      frontPanelSlot = int( frontPanelSlot )
      lineSideLane = int( lineSideLane )
      lineSideSerdes = ( ( systemSerdesId // 8 ) * 8 ) + lineSideLane
      assert asic < numAsics
      asicMapping = asicSerdesMappings[ asic ]
      if lineSideSerdes not in asicMapping:
         asicMapping[ lineSideSerdes ] = {}
      asicMapping[ lineSideSerdes ][ connectionType ] = ( frontPanelSlot,
               systemSideLane, polaritySwap )


asicId = 0

# Port Attributes by profile
portAttrsByProfile = {
      #profileId : ( speed, numLanes, modulation, fec, medium, interfaceMode )
      11 : ( 10000, 1, 1, 1, 1, 10 ),
      24 : ( 200000, 4, 2, 11, 1, 12 ),
      36 : ( 53125, 1, 2, 545, 1, 41 ),
      37 : ( 53125, 1, 2, 545, 3, 41 ),
      38 : ( 400000, 4, 2, 11, 2, 21 ),
      39 : ( 800000, 8, 2, 11, 2, 23 ),
      41 : ( 106250, 1, 2, 544, 1, 41 ),
      42 : ( 106250, 1, 2, 544, 3, 41 ),
}

numFrontPanelPorts = numFabricSerdesCores + numNifSerdesCores
nifFrontPanelSlotToAsicCoreAndSerdesCore = {}
fabFrontPanelLaneToLogicalLane = {}
with open( "viper_static_mapping.csv", "w" ) as fh, open( "bcm_config", "w" ) as bcmConfigFh:
   # Description of attributes for front panel serdes in the order of their
   # occurence.
   # A_SLOT_ID : Linecard slot Id, 1 for fixed systems
   # A_CHIP_ID : ASIC id on the system slot, Viper only has one J3, so always 1
   # A_CHIP_TYPE : NPU
   # A_CORE_ID : ASIC serdes core ID
   # A_CORE_TYPE : ASIC serdes core type, FE/NIF
   # A_CORE_LANE : 0,numLanes - numLanes per core is 8 on J3, so this value
   # goes from 0,7.
   # A_PHYSICAL_TX_LANE : Physical tx trace corresponding to serdes core lane.
   # A_PHYSICAL_RX_LANE : Physical rx trace corresponding to serdes core lane.
   # A_TX_POLARITY_SWAP : bool, is polarity swapped for tx trace.
   # A_RX_POLARITY_SWAP : bool, is polarity swapped for rx trace.
   # Z_SLOT_ID : Transceiver system slot Id, 1 for fixed systems.
   # Z_CHIP_ID : Transceiver front panel slot Id.
   # Z_CHIP_TYPE : TRANSCEIVER
   # Z_CORE_ID : Always 0, since we don't have external PHYs or cores within a
   # single XCVR slot.
   # Z_CORE_TYPE : OSFP for Viper/Whistler
   # Z_CORE_LANE : 0-7, lane within the XCVR slot.
   # Z_PHYSICAL_TX_LANE : Physical tx trace corresponding to XCVR lane.
   # Z_PHYSICAL_RX_LANE : Physical rx trace corresponding to XCVR lane.
   # Z_TX_POLARITY_SWAP : bool, is polarity swapped for tx trace.
   # Z_RX_POLARITY_SWAP : bool, is polarity swapped for rx trace.

   # Special entry for recycle port, which is attached to J3 with a special serdes
   # core Id 55 (this serdes core Id is derived from a reverse calculation of the bcm
   # soc property for recycle port base).
   fh.write( "1,1,NPU,55,J3_RCY,0,,,,,,,,,,,,,,\n" )
   for serdesCore in range( numNifSerdesCores+numFabricSerdesCores ):
      tempProps = {}
      tempBcmLaneMapProps = {}
      tempBcmPolSwapProps = {}
      for lane in range( numSerdesPerCore ):
         serdesId = serdesCore * numSerdesPerCore + lane
         frontPanelSlot, rxLane, rxPolSwap = asicSerdesMappings[ asicId ][ serdesId
               ][ "rx" ]
         _frontPanelSlot, txLane, txPolSwap = asicSerdesMappings[ asicId ][ serdesId
               ][ "tx" ]
         assert frontPanelSlot == _frontPanelSlot
         frontPanelLane = lane
         if serdesCore < numNifSerdesCores:
            logicalLane = lane
            nifFrontPanelSlotToAsicCoreAndSerdesCore[ frontPanelSlot ] = (
                  nifSerdesCoreToAsicCore[ serdesCore ], serdesCore )
         else:
            # For fabric ports, logical lane is the same as the serdes pysical Rx
            # Lane.
            logicalLane = rxLane % numSerdesPerCore

         rxPolSwap = rxPolSwap[ 0 ]
         txPolSwap = txPolSwap[ 0 ]
         if rxPolSwap == "Y":
            rxPolSwapProp = "1"
         elif rxPolSwap == "N":
            rxPolSwapProp = "0"
         else:
            assert False
         if txPolSwap == "Y":
            txPolSwapProp = "1"
         elif txPolSwap == "N":
            txPolSwapProp = "0"
         else:
            assert False
         if serdesCore < numNifSerdesCores:
            serdesCoreByType = serdesCore
            asicCoreType = "J3_NIF"
            laneMapType = "nif"
            polaritySwapType = "phy"
         else:
            serdesCoreByType = serdesCore - numNifSerdesCores
            asicCoreType = "J3_FE"
            laneMapType = "fabric"
            polaritySwapType = "fabric"
            txLane -= ( numNifSerdesCores * numSerdesPerCore )
            rxLane -= ( numNifSerdesCores * numSerdesPerCore )
         # For fabric ports, the logicalLane need not match lane, so if we write it
         # here we will be out of order. We will stash them here so that we can write
         # them to the relevant files in the order of logical lanes.
         tempProps[ logicalLane ] = \
               f"1,1,NPU,{serdesCoreByType},{asicCoreType},{logicalLane},{txLane},{rxLane},{txPolSwap},{rxPolSwap},1,{frontPanelSlot},TRANSCEIVER,0,OSFP,{frontPanelLane},{frontPanelLane},{frontPanelLane},N,N\n"
         # bcm logicalLane is a global lane number that is in range (0,144) for NIF
         # and (0,160) for Fabric.
         bcmLogicalLane = logicalLane + serdesCoreByType * numSerdesPerCore
         if serdesCore >= numNifSerdesCores:
            fabFrontPanelLaneToLogicalLane[ frontPanelSlot * 8 + frontPanelLane ] = bcmLogicalLane

         # BCM soc properties for lane maps and polarity swaps.
         tempBcmLaneMapProps[ logicalLane ] = f"\"lane_to_serdes_map_{laneMapType}_lane{bcmLogicalLane}.BCM8886X\": \"rx{rxLane}:tx{txLane}\",\n"
         tempBcmPolSwapProps[ logicalLane ] = (
               f"\"phy_rx_polarity_flip_{polaritySwapType}{bcmLogicalLane}.BCM8886X\": \"{rxPolSwapProp}\",\n",
               f"\"phy_tx_polarity_flip_{polaritySwapType}{bcmLogicalLane}.BCM8886X\": \"{txPolSwapProp}\",\n" )

      for lane in range( numSerdesPerCore ):
         fh.write( tempProps[ lane ] )
         for prop in tempBcmLaneMapProps[ lane ]:
            bcmConfigFh.write( prop )
         for prop in tempBcmPolSwapProps[ lane ]:
            bcmConfigFh.write( prop )

with open( "viper_port_profile_mapping.csv", "w" ) as fh, open( "bcm_config", "a" ) as bcmConfigFh:
   # Description of fields in the order of their appearance:
   # Global PortID : Global port ID across all ASICs in the system.
   # Logical_PortID : Logical port ID used in the bcm soc properties.
   # Port_Name : Port name used in the platform mapping.
   # Attached_CoreId : CoreId on ASIC that the port is attached to.
   # Attached_Core_PortID : Core local portID assigned to this port.
   # NOTE : For Fabric ports, there is no core binding, the corresponding
   # Attached_CoreId and Attached_Core_PortID can be left empty.
   # Virtual_Device_ID : Virtual device ID for FE ASICs.
   # Recycle port is a special port with port id 1, it is given internal serdes core
   # ID 55.
   fh.write("1,1,rcy1/1/55,11,0,1\n")
   # CPU port is 0, RCY port is 1, NIF ports start from logical port Id 2.
   # Fabric ports start from logical port Id 1024.
   nifLogicalPortIdBase = 2
   fabLogicalPortIdBase = 1024
   fabSupportedProfiles = '-'.join( supportedProfilesByPortType[ 'fab' ] )
   nifSupportedProfilesMain = '-'.join( supportedProfilesByPortType[ 'eth' ] )
   nifSupportedProfilesSubPort = '-'.join( supportedProfilesByPortType[ 'eth' ][ : -1
      ] )
   # Since fabric serdes on J3 don't have a core mapping and the notion of Virtual
   # Devices does not exist on J3, always set this to 0.
   virtualDeviceId = 0
   for port in range( numFrontPanelPorts ):
      frontPanelSlot = port+1
      frontPanelPortType = frontPanelSlotToPortType( frontPanelSlot )
      portStrPrefix = f"{frontPanelPortType}1/{frontPanelSlot}"
      if frontPanelPortType == "fab":
         for subPort in range( 1,9 ):
            portStr = f"{portStrPrefix}/{subPort}"
            fabLogicalPortId = fabLogicalPortIdBase + fabFrontPanelLaneToLogicalLane[
                  frontPanelSlot * 8 + ( subPort - 1 ) ]
            fh.write(
                  f"{fabLogicalPortId},{fabLogicalPortId},{portStr},{fabSupportedProfiles},,,{virtualDeviceId}\n" )
      elif frontPanelPortType == "eth":
         for subPort in ( "1", "5" ):
            portStr = f"{portStrPrefix}/{subPort}"
            # fapPortId
            attachedCoreId, serdesCoreId = nifFrontPanelSlotToAsicCoreAndSerdesCore[ frontPanelSlot ]
            # 400G-4 CDGE core Id
            if subPort == "1":
               cdgeCore_4 = serdesCoreId * 2
               nifLogicalPortId = nifLogicalPortIdBase + cdgeCore_4
               nifSupportedProfiles = nifSupportedProfilesMain
            elif subPort == "5":
               # We are only publishing the /1 port for now and skipping /5, however
               # to allow for /5 to be added with little changes in the future, lets
               # skip writing the static mapping entry, but increment the logical
               # port Id. Uncomment the code below to start adding the /5 to the
               # static mapping.
               nifLogicalPortId += 1
               continue
               # cdgeCore_4 = serdesCoreId * 2 + 1
               # nifLogicalPortId = nifLogicalPortIdBase + cdgeCore_4
               # nifSupportedProfiles = nifSupportedProfilesSubPort
            attachedCorePortId = nifLogicalPortId
            assert nifLogicalPortId - nifLogicalPortIdBase < numNifSerdesCores*2
            bcmConfigFh.write( f"\"ucode_port_{nifLogicalPortId}.BCM8886X\": \"CDGE4_{cdgeCore_4}:core_{attachedCoreId}.{attachedCorePortId}\",\n" )
            fh.write(
                  f"{nifLogicalPortId},{nifLogicalPortId},{portStr},{nifSupportedProfiles},{attachedCoreId},{attachedCorePortId},{virtualDeviceId}\n" )
            nifLogicalPortId += 1
      else:
         assert False, "Invalid frontPanelPortType"
