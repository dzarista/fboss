# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
from collections import OrderedDict
import csv

"""
Author : seerpini@arista.com
Script for generating the Whistler fabric port platform mapping.
Assumptions:
    - Each fabric serdes is enumerated as a 100G port. Supported profiles 36, 37 correspond to 100G optical and copper.
Input:
    - Whistler_port_mapping_v1_meta.csv - mapping from fabric serdes 
Output:
    - Generated platform is written to whistler_platform_mapping.json
Instructions:
    - Please update the following variables to control how fabric port mappings are generated.
    - Port speed and breakout are not currently configurable.
TODO
    - Accept platform settings from input/config file and generate mapping
      accordingly.
"""

# Variables to control the behavior for this script.
# Existing mappings at a port level are not replaced if preserveExistingMappings=True
preserveExistingMappings = False
# Logical port base in the SDK for fabric ports.
fabricPortBase = 0
# Whistler has two Ramon3 ASICs with 512x100G serdes on each ASIC.
numAsics = 2
# Print debug information
debug = False
numNifPorts = 0
# Number of fabric serdes cores per ASIC.
numFabricSerdesCoresPerAsic = 64
# Number of serdes per serdes core. Peregrine 8x100G serdes core on R3.
numSerdesPerCore = 8
# Total serdes in the system
numSystemSerdes = numFabricSerdesCoresPerAsic * numAsics * numSerdesPerCore
# Since each front panel slot has 8 lanes, total front panel ports is :
numFrontPanelPorts = numSystemSerdes // 8
# Total number of fabric ports assuming that each fabric serdes is enumerated as a
# separate port.
numFabricPorts = numSystemSerdes

# Assuming 100G lanes, number of lanes required by each supported port profile.
numLanesFromSupportedProfile = {
      "36" : 1,
      "37" : 1,
      "41" : 1,
      "42" : 1,
}

def getBasePortMapping( portId=0, serdesCore="", frontPanelPort="", numLanes=1,
      firstSerdesCoreLane=0, firstFrontPanelLane=0, supportedProfiles=None,
      attachedCoreId=0, attachedCorePortIndex=0,
      portType=0 ):
   # Front panel port would be et1/X or fab1/X and based on the first lane, this can
   # be et1/X/Y (or fab1/X/Y) where Y is firstFrontPanelLane+1.
   name=f"{frontPanelPort}/{firstFrontPanelLane+1}"
   portMapping = OrderedDict( {
      "mapping": OrderedDict( {
         "id": portId,
         "name": name,
         "controllingPort": portId,
         "pins": [],
         "portType": portType,
         "attachedCoreId": attachedCoreId,
         "attachedCorePortIndex": attachedCorePortIndex
      } ),
      "supportedProfiles": OrderedDict()
   } )
   for lane in range( numLanes ):
      pinMapping = OrderedDict( {
         "a" : OrderedDict( {
            "chip" : serdesCore,
            "lane" : firstSerdesCoreLane+lane
         } ),
         "z" : OrderedDict( {
            "end" : OrderedDict( {
               "chip" : frontPanelPort,
               "lane" : firstFrontPanelLane+lane
            } )
         } )
      } )
      portMapping[ "mapping" ][ "pins" ].append( pinMapping )

   templateSuppProfiles = portMapping[ "supportedProfiles" ]
   # numLanes is the total lanes that this port can use. However, based on the port
   # profile, we might not need to use all the lanes. For eg, for 400G-4, we will
   # only need the first 4 lanes. 800G-8 will need all 8 lanes.
   if supportedProfiles is None:
      supportedProfiles = []
   for suppProfile in supportedProfiles:
      if suppProfile not in templateSuppProfiles:
         templateSuppProfiles[ suppProfile ] = OrderedDict(
               { "pins" : OrderedDict(
                  {
                     "iphy" : [],
                     "transceiver" : [],
                  } )
               } )
      reqLanes = numLanesFromSupportedProfile[ suppProfile ]
      assert reqLanes <= numLanes
      for lane in range(reqLanes ):
         pinIPhyMapping = OrderedDict( {
            "id" : OrderedDict( {
               "chip" : serdesCore,
               "lane" : firstSerdesCoreLane+lane
            } )
         } )
         xcvrMapping = OrderedDict( {
            "id" : OrderedDict( {
               "chip" : frontPanelPort,
               "lane" : firstFrontPanelLane+lane
            } )
         } )
         templateSuppProfiles[ suppProfile ][ "pins" ][ "iphy" ].append(
               pinIPhyMapping )
         templateSuppProfiles[ suppProfile ][ "pins" ][ "transceiver" ].append(
               xcvrMapping )
   return portMapping

def getFabricPortMapping( portId, serdesCore, frontPanelPort, firstSerdesCoreLane,
                          firstFrontPanelLane, supportedProfiles=None ):
   portMapping = getBasePortMapping( portId=portId, serdesCore=serdesCore,
         frontPanelPort=frontPanelPort, numLanes=1,
         firstSerdesCoreLane=firstSerdesCoreLane,
         firstFrontPanelLane=firstFrontPanelLane,
         supportedProfiles=supportedProfiles, portType=1 )
   del portMapping[ "mapping" ][ "attachedCoreId" ]
   return portMapping

platMapping = OrderedDict()
platMapping[ "ports" ] = OrderedDict()

fabricFrontPanelMap = OrderedDict()
# Build fabric port mappings from CSV file.
with open( "Whistler_port_mapping_v1_meta.csv" ) as csvFile:
   reader = csv.reader( csvFile )
   for row in reader:
      if not row[ 0 ].isdigit():
         continue
      fabricFrontPanelMap[ row[ 0 ] ] = row[ 1: ]

# Map ASIC physical rx and tx serdes/lanes to front panel slot, lane.
asicSerdesToFrontPanelMap = []
# Map front panel port to ASIC physical rx and tx serdes.
# X/Y => {chipId, rxPhysicalLane, txPhysicalLane}
frontPanelToAsicSerdesMap = {}
# Map ASIC logical lanes to physical rx and tx serdes/lanes.
asicLogicalLaneToSerdesMap = []
# Map ASIC physical rx and tx serdes/lanes to logical lanes.
asicSerdesToLogicalLaneMap = []
for asic in range( numAsics ):
   asicSerdesToFrontPanelMap.append( { "rx" : {}, "tx" : {} } )
   asicSerdesToLogicalLaneMap.append( { "rx" : {}, "tx" : {} } )
   asicLogicalLaneToSerdesMap.append( {} )

# On whistler each serdes is a port, we cannot derive the lane maps just by parsing
# the system side serdes to line side lane mapping information.
# For now we will just use the pre-generated lane mapping CSV to map logical lanes to
# rx, tx physical lanes. We can then look up the system serdes id (which would be the
# rx, tx physical lane) to map it to a front panel slot and lane.
# The result of all this is that unlike Viper, on Whistler, the front panel lane will
# not always match the ASIC logical lane.
with open( "SocPropertiesP1.csv" ) as fh:
   for line in fh:
      if line.startswith( "chipId" ):
         continue
      chipId, propKey, propVal = line.rstrip().split( "," )
      if not propKey.startswith( "lane_to" ):
         continue
      chipId = int( chipId )
      logicalLane = int( propKey.removeprefix( "lane_to_serdes_map_fabric_lane" ) )
      rxPhysicalSerdes = 0
      txPhysicalSerdes = 0
      for physicalSerdes in propVal.rstrip().split( ":" ):
         if physicalSerdes.startswith( "rx" ):
            rxPhysicalSerdes = int( physicalSerdes.removeprefix( "rx" ) )
         elif physicalSerdes.startswith( "tx" ):
            txPhysicalSerdes = int( physicalSerdes.removeprefix( "tx" ) )
         else:
            assert False
      # We should only see one line per logical lane per chip
      assert logicalLane not in asicLogicalLaneToSerdesMap[ chipId ]
      asicLogicalLaneToSerdesMap[ chipId ][ logicalLane ] = {}
      asicLogicalLaneToSerdesMap[ chipId ][ logicalLane ][ "rx" ]  = rxPhysicalSerdes
      asicLogicalLaneToSerdesMap[ chipId ][ logicalLane ][ "tx" ]  = txPhysicalSerdes
      asicSerdesToLogicalLaneMap[ chipId ][ "rx" ][ rxPhysicalSerdes ] = logicalLane
      asicSerdesToLogicalLaneMap[ chipId ][ "tx" ][ txPhysicalSerdes ] = logicalLane

# Map system side physical serdes to front panel OSFP slot and lane.
with open( "Trace_whistler_1.0_Ramon3ToOSFP-800G.csv" ) as fh:
   for line in fh:
      if line.startswith( "System" ):
         continue
      chipId, physicalSerdesId, frontPanelSlot, frontPanelLane, _, direction, polaritySwap = line.rstrip().split(",")
      chipId = int( chipId )
      physicalSerdesId = int( physicalSerdesId )
      frontPanelSlot = int( frontPanelSlot )
      frontPanelLane = int( frontPanelLane )
      assert chipId < numAsics
      asicSerdesToFrontPanelMap[ chipId ][ direction ][ physicalSerdesId ] = ( frontPanelSlot,
            frontPanelLane, polaritySwap )
      frontPanelPortStrKey = f"{frontPanelSlot}/{frontPanelLane+1}"
      if frontPanelPortStrKey not in frontPanelToAsicSerdesMap:
         frontPanelToAsicSerdesMap[ frontPanelPortStrKey ] = {}
      frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "chipId" ] = chipId
      frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ direction ] = physicalSerdesId


# Append the fabric ports.
# Each serdes is described as a fabric port, so the enumeration here is somewhat
# different from the NIF ports.
for asicId in range( numAsics ):
   fabricPortBase = ( asicId * numFabricSerdesCoresPerAsic * numSerdesPerCore )
   for fabSerdesCore in range( numFabricSerdesCoresPerAsic ):
      port = fabSerdesCore * numSerdesPerCore
      for serdes in range( numSerdesPerCore ):
         # Globally unique logical port Id
         logicalPortId = port + fabricPortBase
         portStr = str( logicalPortId )
         if portStr in platMapping[ 'ports' ] and preserveExistingMappings:
            continue
         supportedProfiles = [ '36', '37', ]
         serdesCore = f"BC{fabSerdesCore}"
         # Since each serdes is a port, "port" is the logical lane on the ASIC side
         # Map from port, which is the logicalLane to physical rx and tx lanes and
         # then map those to front panel slot and lane.
         rxPhysicalLane = asicLogicalLaneToSerdesMap[ asicId ][ port ][ "rx" ]
         txPhysicalLane = asicLogicalLaneToSerdesMap[ asicId ][ port ][ "tx" ]
         frontPanelSlot, frontPanelLane, _ = asicSerdesToFrontPanelMap[ asicId ][ "rx" ][
               rxPhysicalLane ]
         frontPanelSlotComp, frontPanelLaneComp, _ = asicSerdesToFrontPanelMap[ asicId ][
               "tx" ][ txPhysicalLane ]
         assert frontPanelSlot == frontPanelSlotComp
         assert frontPanelLane == frontPanelLaneComp
         frontPanelPort = f"fab1/{frontPanelSlot}"
         portMapping = getFabricPortMapping( portId=logicalPortId, serdesCore=serdesCore,
               frontPanelPort=frontPanelPort, firstFrontPanelLane=frontPanelLane,
               firstSerdesCoreLane=serdes, supportedProfiles=supportedProfiles )
         platMapping[ 'ports' ][ portStr ] = portMapping
         if debug:
            print( portMapping )
         port += 1

# Append the chips enumeration.
platMapping[ "chips" ] = []
for core in range( numFabricSerdesCoresPerAsic ):
   platMapping[ "chips" ].append( OrderedDict(
      {
         "name": f"BC{core}",
         "type" : 1,
         "physicalID": core
      } ) )
for port in range( numFrontPanelPorts ):
   frontPanelSlot = port + 1
   platMapping[ "chips" ].append( OrderedDict(
      {
         "name": f"fab1/{frontPanelSlot}",
         "type" : 3,
         "physicalID": port 
      } ) )

platMapping[ "platformSettings" ] = OrderedDict()
platMapping[ "portConfigOverrides" ] = []
platMapping[ "platformSupportedProfiles" ] = []
# Port Attributes by profile
portAttrsByProfile = {
      #profileId : ( speed, numLanes, modulation, fed, medium, interfaceMode )
      11 : ( 10000, 1, 1, 1, 1, 10 ),
      36 : ( 53125, 1, 2, 545, 1, 41 ),
      37 : ( 53125, 1, 2, 545, 3, 41 ),
      38 : ( 400000, 4, 2, 11, 2, 21 ),
      39 : ( 800000, 8, 2, 11, 2, 23 ),
      41 : ( 106250, 1, 2, 544, 1, 41 ),
      42 : ( 106250, 1, 2, 544, 3, 41 ),
}
# Append the supportedProfiles information.
for profileID in numLanesFromSupportedProfile.keys():
   profileID = int( profileID )
   profilePortAttrs = portAttrsByProfile[ profileID ]
   platMapping[ "platformSupportedProfiles" ].append(
         OrderedDict( {
            "factor" : {
               "profileID" : profileID
            },
            "profile": OrderedDict( {
               "speed": profilePortAttrs[ 0 ],
               "iphy" : OrderedDict( {
                  "numLanes" : profilePortAttrs[ 1 ],
                  "modulation" : profilePortAttrs[ 2 ],
                  "fec" : profilePortAttrs[ 3 ],
                  "medium" : profilePortAttrs[ 4 ],
                  "interfaceMode" : profilePortAttrs[ 5 ],
                  "interfaceType" : profilePortAttrs[ 5 ]
               } )
            } )
         } ) )

json_out = json.dumps( platMapping, indent=2, sort_keys=False )
with open( "whistler_platform_mapping.json", "w") as fh:
   fh.write( json_out )

bcmConfigFh = open( "bcm_config", "w" )
with open( "whistler_static_mapping.csv", "w" ) as fh:
   # Description of attributes for front panel serdes in the order of their
   # occurence.
   # A_SLOT_ID : Linecard slot Id, 1 for fixed systems
   # A_CHIP_ID : ASIC id on the system slot, Whistler has two R3, can be 0,1
   # A_CHIP_TYPE : NPU
   # A_CORE_ID : ASIC serdes core ID
   # A_CORE_TYPE : ASIC serdes core type, FE/NIF
   # A_CORE_LANE : 0,numLanes - numLanes per core is 8 on J3/R3, so this value
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
   for portId in range( numFabricPorts ):
      frontPanelSlot  = ( portId // 8 ) + 1
      frontPanelLane = portId % 8
      frontPanelPortStrKey = f"{frontPanelSlot}/{frontPanelLane+1}"
      chipId = frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "chipId" ]
      rxPhysicalLane = frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "rx" ]
      txPhysicalLane = frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "tx" ]
      logicalLane = asicSerdesToLogicalLaneMap[ chipId ][ "rx" ][ rxPhysicalLane ]
      assert logicalLane == asicSerdesToLogicalLaneMap[ chipId ][ "tx" ][ txPhysicalLane ]
      serdesCore = logicalLane // 8

      _frontPanelSlot, _frontPanelLane, rxPolSwap = asicSerdesToFrontPanelMap[ chipId ][ "rx" ][
            rxPhysicalLane ]
      assert frontPanelSlot == _frontPanelSlot
      assert frontPanelLane == _frontPanelLane
      _frontPanelSlot, _frontPanelLane, txPolSwap = asicSerdesToFrontPanelMap[ chipId ][ "tx" ][
            txPhysicalLane ]
      assert frontPanelSlot == _frontPanelSlot
      assert frontPanelLane == _frontPanelLane
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
      asicCoreType = "R3_FE"
      laneMapType = "fabric"
      polaritySwapType = "fabric"
      fh.write(
            f"1,{chipId+1},NPU,{serdesCore},{asicCoreType},{logicalLane%8},{txPhysicalLane%8},{rxPhysicalLane%8},{txPolSwap},{rxPolSwap},1,{frontPanelSlot},TRANSCEIVER,0,OSFP,{frontPanelLane},{frontPanelLane},{frontPanelLane},N,N\n"
            )
      # BCM soc properties for lane maps and polarity swaps.
      # NOTE : Currently this only generates
      bcmConfigFh.write(
            f"\"lane_to_serdes_map_{laneMapType}_lane{logicalLane}.BCM8892X.{chipId}\": \"rx{rxPhysicalLane}:tx{txPhysicalLane}\",\n" )
      bcmConfigFh.write(
            f"\"phy_rx_polarity_flip_{polaritySwapType}{logicalLane}.BCM8892X.{chipId}\": \"{rxPolSwapProp}\",\n" )
      bcmConfigFh.write(
            f"\"phy_tx_polarity_flip_{polaritySwapType}{logicalLane}.BCM8892X.{chipId}\": \"{txPolSwapProp}\",\n" )

with open( "whistler_port_profile_mapping.csv", "w" ) as fh:
   fabricPortBase = 0
   # Description of fields in the order of their appearance:
   # Global PortID : Global port ID across all ASICs in the system.
   # Logical_PortID : Logical port ID used in the bcm soc properties.
   # Port_Name : Port name used in the platform mapping.
   # Attached_CoreId : CoreId on ASIC that the port is attached to.
   # Attached_Core_PortID : Core local portID assigned to this port.
   # NOTE : For Fabric ports, there is no core binding, the corresponding
   # Attached_CoreId and Attached_Core_PortID can be left empty.
   fabSupportedProfiles = '-'.join( numLanesFromSupportedProfile.keys() )
   # FBOSS assigns a range of 2k ports to each NPU, we will only use the first 512
   # IDs from this space.
   fabricPortsPerAsic = 2048
   for portId in range( numFabricPorts ):
      frontPanelSlot  = ( portId // 8 ) + 1
      frontPanelLane = portId % 8 + 1
      frontPanelPortStrKey = f"{frontPanelSlot}/{frontPanelLane}"
      chipId = frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "chipId" ]
      rxPhysicalLane = frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "rx" ]
      logicalLane = asicSerdesToLogicalLaneMap[ chipId ][ "rx" ][ rxPhysicalLane ]
      portStr = f"fab1/{frontPanelPortStrKey}"
      logicalPortId = logicalLane
      assert logicalLane < fabricPortsPerAsic
      globalPortId = ( fabricPortsPerAsic * chipId ) + logicalPortId
      fh.write( f"{globalPortId},{logicalPortId},{portStr},{fabSupportedProfiles},,\n" )

bcmConfigFh.close()
