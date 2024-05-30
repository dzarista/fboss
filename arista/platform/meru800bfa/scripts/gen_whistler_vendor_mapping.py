#!/bin/env python3
# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import os
import sys
sys.path.append( "../../lib" )
import csv
from dataclasses import astuple
from PlatformUtils import validMediaForSpeed, validFabricSerdesSpeeds, \
   txTapSettingsByLaneProps, PortMedium, SpeedGbps, speedInMbps, TxTapSettings
from VendorMappings import StaticMapping, PortProfileMapping, SISettings
from WhistlerP1LanesMappingData import feToLaneMapSocProps, \
   fabricTraceLengthByLogicalLane, logicalLaneToPhysicalCoreLogicalLane

"""
Author : seerpini@arista.com
Script for generating the Whistler vendor mappings.
Assumptions:
    - Each fabric serdes is enumerated as a 100G port. Supported profiles 36, 37 correspond to 100G optical and copper.
Input:
    - Trace_whistler_1.0_Ramon3ToOSFP-800G.csv - system to line side serdes mappings
      and trace information.
    - SocPropertiesP1.csv - diags generated bcm soc properties for fabric port
      logical lane maps.
Output:
    - Vendor mappings (static and port profile mapping) and bcm configuration is
      generated.
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
# Number of fabric serdes cores per ASIC.
numFabricSerdesCoresPerAsic = 64
# Number of serdes per serdes core. Peregrine 8x100G serdes core on R3.
numSerdesPerCore = 8
numFabricSerdesPerAsic = numFabricSerdesCoresPerAsic * numSerdesPerCore
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

# Map ASIC physical rx and tx serdes/lanes to front panel slot, lane.
asicSerdesToFrontPanelMap = []
# Map front panel port to ASIC physical rx and tx serdes.
# X/Y => {chipId, rxPhysicalLane, txPhysicalLane}
frontPanelToAsicSerdesMap = {}
# Map ASIC logical lanes to physical core, per core rx logical lane, and average
# (tx+rx/2) trace length.
asicLogicalLaneTraceLength = []
# Map ASIC physical rx and tx serdes/lanes to logical lanes.
asicSerdesToLogicalLaneMap = []
for asic in range( numAsics ):
   asicSerdesToFrontPanelMap.append( { "rx" : {}, "tx" : {} } )
   asicSerdesToLogicalLaneMap.append( { "rx" : {}, "tx" : {} } )
   asicLogicalLaneTraceLength.append( {} )
# Returns fabric trace lengths by chipId, physical coreId and physical logical lane
asicFabricLaneTraceLengths = fabricTraceLengthByLogicalLane( numFabricSerdesCoresPerAsic,
                                                             numSerdesPerCore )

# On whistler each serdes is a port, we cannot derive the lane maps just by parsing
# the system side serdes to line side lane mapping information.
# For now we will just use the pre-generated lane map soc properties to map logical
# lanes to rx, tx physical lanes.
# We can then look up the system serdes id (which would be the rx, tx physical lane)
# to map it to a front panel slot and lane.
# The result of all this is that unlike NIF ports on Viper, on Whistler, the front
# panel lane will not always match the ASIC logical lane.
assert len( feToLaneMapSocProps ) == numAsics
for chipId in range( numAsics ):
   assert len( feToLaneMapSocProps[ chipId ] ) == numFabricSerdesPerAsic
   for propKey, propVal in feToLaneMapSocProps[ chipId ].items():
      logicalLane = int( propKey.removeprefix( "lane_to_serdes_map_fabric_lane" ) )
      rxPhysicalSerdes = 0
      txPhysicalSerdes = 0
      for physicalSerdes in propVal.split( ":" ):
         if physicalSerdes.startswith( "rx" ):
            rxPhysicalSerdes = int( physicalSerdes.removeprefix( "rx" ) )
         elif physicalSerdes.startswith( "tx" ):
            txPhysicalSerdes = int( physicalSerdes.removeprefix( "tx" ) )
         else:
            assert False, "physical serdes should be either rx or tx."
      asicSerdesToLogicalLaneMap[ chipId ][ "rx" ][ rxPhysicalSerdes ] = logicalLane
      asicSerdesToLogicalLaneMap[ chipId ][ "tx" ][ txPhysicalSerdes ] = logicalLane
      # Populate the trace length correctly by logical lane.
      # We should only see one line per logical lane per chip
      assert logicalLane not in asicLogicalLaneTraceLength[ chipId ]
      physicalSerdesCore = rxPhysicalSerdes // numSerdesPerCore
      serdesCoreLogicalLane = logicalLaneToPhysicalCoreLogicalLane( logicalLane,
                                                             rxPhysicalSerdes )
      laneInfo = asicFabricLaneTraceLengths[ chipId ].cores[ physicalSerdesCore
         ].lanes[ serdesCoreLogicalLane ]
      asicLogicalLaneTraceLength[ chipId ][ logicalLane ] = \
         laneInfo.traceLengthToNextEpInInches

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

# Print some debug information that helps us make sure that the trace length
# information has been extracted correctly.
# This output can be compared with the wire(...) calls in
# //src/DosSand/diags.dev-base-trunk-dmz/DosBoard/WhistlerP1LanesMappingData.py
# to make sure we have extracted the Diags' generated trace length information
# correctly.
if debug:
   for portId in range( numFabricPorts ):
      xcvrSlot = portId // 8 + 1
      xcvrLane = portId % 8
      frontPanelPortStrKey = f"{xcvrSlot}/{xcvrLane+1}"
      chipId = frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "chipId" ]
      rxPhysicalLane = frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "rx" ]
      physicalSerdesCore = rxPhysicalLane // 8
      logicalLane = asicSerdesToLogicalLaneMap[ chipId ][ "rx" ][ rxPhysicalLane ]
      serdesCoreLogicalLane = logicalLaneToPhysicalCoreLogicalLane( logicalLane,
                                                                    rxPhysicalLane )
      print( f"wire( xcvrSlots[{xcvrSlot}].sysLanes[{xcvrLane}],"
          f" fes[{chipId}].cores[{physicalSerdesCore}].lanes[{serdesCoreLogicalLane}] )" )

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

with open( "whistler_static_mapping.csv", "w" ) as fh, open( "bcm_config", "w" ) as bcmConfigFh:
   fields = [ field.name for field in StaticMapping.getFields()]
   mappingWriter = csv.writer(fh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   mappingWriter.writerow( fields )
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
      mappingWriter.writerow( astuple(
         StaticMapping(
            1,chipId+1,"NPU",serdesCore,asicCoreType,logicalLane%8,
            txPhysicalLane,rxPhysicalLane,txPolSwap,rxPolSwap,1,frontPanelSlot,
            "TRANSCEIVER",0,"OSFP",frontPanelLane,frontPanelLane,frontPanelLane,"N","N" )
      ) )
      # BCM soc properties for lane maps and polarity swaps.
      # NOTE : Currently this only generates
      bcmConfigFh.write(
            f"\"lane_to_serdes_map_{laneMapType}_lane{logicalLane}.BCM8892X.{chipId}\": \"rx{rxPhysicalLane}:tx{txPhysicalLane}\",\n" )
      bcmConfigFh.write(
            f"\"phy_rx_polarity_flip_{polaritySwapType}{logicalLane}.BCM8892X.{chipId}\": \"{rxPolSwapProp}\",\n" )
      bcmConfigFh.write(
            f"\"phy_tx_polarity_flip_{polaritySwapType}{logicalLane}.BCM8892X.{chipId}\": \"{txPolSwapProp}\",\n" )

with open( "whistler_port_profile_mapping.csv", "w" ) as fh, open( "bcm_config", "a" ) as bcmConfigFh:
   fields = [ field.name for field in PortProfileMapping.getFields()]
   mappingWriter = csv.writer(fh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   mappingWriter.writerow( fields )
   fabricPortBase = 0
   fabSupportedProfiles = '-'.join( numLanesFromSupportedProfile.keys() )
   # FBOSS assigns a range of 2k ports to each NPU, we will only use the first 512
   # IDs from this space.
   fabricPortsPerAsic = 2048
   virtualDevicesPerAsic = 2
   numFabricSerdesPerVD = numFabricSerdesPerAsic // virtualDevicesPerAsic
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
      virtualDeviceId = ( logicalPortId // numFabricSerdesPerVD ) + ( chipId * virtualDevicesPerAsic )
      mappingWriter.writerow( astuple(
         PortProfileMapping(globalPortId, logicalPortId, portStr,
                            fabSupportedProfiles, None, None, virtualDeviceId )
      ) )

with open( "whistler_si_settings.csv", "w" ) as fh:
   fields = [ field.name for field in SISettings.getFields()]
   mappingWriter = csv.writer(fh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   mappingWriter.writerow( fields )

   # Populate SI settings if they are available in a file.
   siSettingsFilePath = "./Whistler_Hw_SI_Settings_v16.csv"
   asicLogicalLaneToSISettings = {}
   if os.path.isfile( siSettingsFilePath ):
      for asicId in range( numAsics ):
         asicLogicalLaneToSISettings[ asicId ] = {}
      with open( siSettingsFilePath ) as siFh:
         siReader = csv.reader( siFh )
         for row in siReader:
            # Skip the field names
            if not row[0].isdigit():
               continue
            frontPanelPortStrKey = f"{row[0]}/{row[1]}"
            asicId = frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "chipId" ]
            rxPhysicalLane = frontPanelToAsicSerdesMap[ frontPanelPortStrKey ][ "rx" ]
            logicalLane = asicSerdesToLogicalLaneMap[ asicId ][ "rx" ][ rxPhysicalLane ]
            # HW port mapping does not have post3 values, so assuming 0.
            asicLogicalLaneToSISettings[ asicId ][ logicalLane ] = TxTapSettings(
               row[ 2 ], row[ 3 ], row[ 4 ], row[ 5 ], row[ 6 ], row[ 7 ], 0 )
      # Make sure that we were able to read SI settings for all ports on both asics.
      for asicId in range( numAsics ):
         assert len( asicLogicalLaneToSISettings[ asicId ] ) == numFabricSerdesPerAsic

   # We only care about 100G fabric serdes with Optical media on Whistler
   speed = SpeedGbps.HundredAndSix
   medium = PortMedium.OPTICAL
   for asicId in range( numAsics ):
      # chip ID in SI settings is 1-indexed.
      chipId = asicId + 1
      for logicalFabSerdes in range( numFabricSerdesPerAsic ):
         coreId = logicalFabSerdes // numSerdesPerCore
         coreLane = logicalFabSerdes % numSerdesPerCore
         if asicId in asicLogicalLaneToSISettings:
            txTapSettings = asicLogicalLaneToSISettings[ asicId ][ logicalFabSerdes ]
         else:
            txTapSettings = txTapSettingsByLaneProps( speed, medium,
                                                     asicLogicalLaneTraceLength[ asicId ][
                                                     logicalFabSerdes ] )
         mappingWriter.writerow( astuple(
                                SISettings(1, chipId, "NPU", coreId, "R3_FE",
                                coreLane, speedInMbps( speed ), medium.name,
                                None, None, None, txTapSettings.pre3,
                                txTapSettings.pre2, txTapSettings.pre1,
                                txTapSettings.main, txTapSettings.post1,
                                txTapSettings.post2, txTapSettings.post3,
                                None, None, None )
         ) )
