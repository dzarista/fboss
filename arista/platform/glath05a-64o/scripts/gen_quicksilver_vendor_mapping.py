#!/bin/env python3
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import sys
sys.path.append( "../../lib" )
import csv
from dataclasses import astuple
from PlatformUtils import PortMedium, SpeedGbps, validMediaForSpeed, \
   validNifSerdesSpeeds, speedInMbps, txTapSettingsByLaneProps, TxTapSettings
from VendorMappings import StaticMapping, PortProfileMapping, SISettings

"""
Author : alamsi@arista.com
Script for generating the quicksilver vendor mappings.
Assumptions:
    - Each front panel port is enumerated as 800G-8.
Output:
    - Vendor mappings (static and port profile mapping) and bcm configuration is
      generated.
"""


# Number of ASICs in the system
numAsics = 1

# Number of serdes per serdes octet. Peregrine 8x100G serdes core on TH5.
numSerdesPerOctet = 8

# Total number of NIF ports.
numNifSerdesOctets = 64
numNifSerdes = numNifSerdesOctets * numSerdesPerOctet


# All ports are nifs
def frontPanelSlotToPortType( slot ):
   assert 1 <= slot <= numNifSerdesOctets
   return "nif"

# NOTE: aquired from chip model
# Number of serdes/lanes per front panel slot
def numLanesInFrontPanelSlot( slot ):
   assert 1 <= slot <= numNifSerdesOctets
   return 8

asicId = 0
asicSerdesMappings = []
for asic in range( numAsics ):
   asicSerdesMappings.append( { 'nif': {} } )
# For Quicksilver, since each serdes core maps to a single OSFP port, we can figure out the
# lanes from reverse mapping the line side lane to the system side serdes lane.
# This also means that the logical lanes on the ASIC side always match the OSFP front
# panel lanes. The lane maps tell us how a logical lane maps to rx, tx physical
# lanes.
with open( "Trace_quicksilverP_1.0_Tomahawk5ToOSFP.csv" ) as fh:
   for line in fh:
      if line.startswith( "System" ):
         continue
      asic, systemSerdesId, frontPanelSlot, lineSideLane, _, connectionType, polaritySwap = line.rstrip().split(",")
      asic = int( asic )
      frontPanelSlot = int( frontPanelSlot )
      portType = frontPanelSlotToPortType( frontPanelSlot )
      systemSerdesId = int( systemSerdesId )

      systemSideLane = systemSerdesId
      lanesInSlot = numLanesInFrontPanelSlot( frontPanelSlot )
      lineSideLane = int( lineSideLane )
      lineSideSerdes = ( ( systemSerdesId // lanesInSlot ) * lanesInSlot ) + lineSideLane
      assert asic < numAsics
      asicPortMapping = asicSerdesMappings[ asic ][ portType ]
      if lineSideSerdes not in asicPortMapping:
         asicPortMapping[ lineSideSerdes ] = {}
      if connectionType not in asicPortMapping[ lineSideSerdes ]:
         asicPortMapping[ lineSideSerdes ][ connectionType ] = ( frontPanelSlot,
                  systemSideLane, polaritySwap )


nifFrontPanelSlotToAsicCoreAndSerdesCore = {}
with open( "quicksilver_static_mapping.csv", "w", newline="" ) as fh:
   fields = [ field for field in StaticMapping.getLabels()]
   mappingWriter = csv.writer(fh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   mappingWriter.writerow( fields )

   def genMappingsForSerdesCore( serdesCore, firstSerdes, numSerdes, portType ): 
      tempProps = {}
      tempBcmPolSwapProps = {}
      asicPortSerdesMappings = asicSerdesMappings[ asicId ][ portType ]
      for lane in range( numSerdes ):
         serdesId = firstSerdes + lane
         frontPanelSlot, rxLane, rxPolSwap = asicPortSerdesMappings[ serdesId
               ][ "rx" ]
         _frontPanelSlot, txLane, txPolSwap = asicPortSerdesMappings[ serdesId
               ][ "tx" ]
         assert firstSerdes <= rxLane < firstSerdes + numSerdes
         assert firstSerdes <= txLane < firstSerdes + numSerdes
         assert frontPanelSlot == _frontPanelSlot
         frontPanelLane = lane
         if portType == "nif":
            logicalLane = lane
            nifFrontPanelSlotToAsicCoreAndSerdesCore[ frontPanelSlot ] = serdesCore
            asicCoreType = "TH5_NIF"
            polaritySwapType = "phy"

         rxPolSwap = rxPolSwap[ 0 ]
         txPolSwap = txPolSwap[ 0 ]

         tempProps[ logicalLane ] = StaticMapping(
            A_SLOT_ID=1, # Linecard slot Id, 1 for fixed systems
            A_CHIP_ID=1, # Only one asic, so always 1
            A_CHIP_TYPE="NPU",
            A_CORE_ID=serdesCore, # ASIC serdes core ID
            A_CORE_TYPE=asicCoreType, # ASIC serdes core type
            A_CORE_LANE=logicalLane,
            A_PHYSICAL_TX_LANE=txLane, # Physical tx trace corresponding to serdes core lane.
            A_PHYSICAL_RX_LANE=rxLane, # Physical rx trace corresponding to serdes core lane.
            A_TX_POLARITY_SWAP=txPolSwap, # bool, is polarity swapped for tx trace.
            A_RX_POLARITY_SWAP=rxPolSwap, # bool, is polarity swapped for rx trace.
            Z_SLOT_ID=1, # Transceiver system slot Id, 1 for fixed systems.
            Z_CHIP_ID=frontPanelSlot, # Transceiver front panel slot Id.
            Z_CHIP_TYPE="TRANSCEIVER",
            Z_CORE_ID=0, # Always 0, since we don't have external PHYs or cores within a single XCVR slot
            Z_CORE_TYPE="OSFP",
            Z_CORE_LANE=frontPanelLane,
            Z_PHYSICAL_TX_LANE=frontPanelLane,
            Z_PHYSICAL_RX_LANE=frontPanelLane,
            Z_TX_POLARITY_SWAP="N",
            Z_RX_POLARITY_SWAP="N"
         )

      for lane in range( numSerdes ):
         mappingWriter.writerow( astuple( tempProps[ lane ] ) )

   for serdesCore in range( numNifSerdesOctets ):
      genMappingsForSerdesCore( serdesCore, serdesCore * 8, 8, "nif" )



def frontPanelSlots():
   numFrontPanelPorts = numNifSerdesOctets
   return list( range( 1, numFrontPanelPorts + 1 ) )
   

supportedProfiles = {
      1 : [ '23', '25', '38', '39', '45', '47', '49', '50' ],
      2 : [ '47', '49' ],
      3 : [ '47', '49' ],
      4 : [ '47', '49' ],
      5 : [ '23', '25', '38', '45', '47', '49' ],
      6 : [ '47', '49' ],
      7 : [ '47', '49' ],
      8 : [ '47', '49' ]
}

with open( "quicksilver_port_profile_mapping.csv", "w" ) as fh:
   fields = [ field for field in PortProfileMapping.getLabels()]
   mappingWriter = csv.writer(fh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   mappingWriter.writerow( fields )

   # CPU port is 0, NIF ports start from logical port Id 1.
   nifLogicalPortIdBase = 1
   # attachedCorePortIdsByAsicCore = { core : [] for core in range( numAsicCores ) }
   for frontPanelSlot in frontPanelSlots():
      subPorts = list( range( 1, numSerdesPerOctet + 1 ) )

      for subPort in subPorts:
         portStr = f"eth1/{frontPanelSlot}/{subPort}"

         serdesCoreId = nifFrontPanelSlotToAsicCoreAndSerdesCore[ frontPanelSlot ]

         nifSupportedProfiles = '-'.join( supportedProfiles[ subPort ] )

         nifLogicalPortId = nifLogicalPortIdBase + ( serdesCoreId * len( subPorts ) ) + subPort - 1

         mappingWriter.writerow( astuple(
            PortProfileMapping( 
               Global_PortID=nifLogicalPortId, # Global port ID across all ASICs in the system.
               Logical_PortID=nifLogicalPortId, #  Logical port ID used in the bcm soc properties.
               Port_Name=portStr, # Port name used in the platform mapping.
               Supported_Port_Profiles=nifSupportedProfiles, # FBOSS Port profile supported by the port.
               Attached_CoreID="", # CoreId on ASIC that the port is attached to. Not used on XGS
               Attached_Core_PortID="", #Core local portID assigned to this port. Not used on XGS
               Virtual_Device_ID="", # Not applicable
               Port_Type=0,
               Scope=0
            )
         ) )
         nifLogicalPortId += 1

txTapSettingsByLane = {
   SpeedGbps.Fifty:{
      PortMedium.COPPER:{},
      PortMedium.OPTICAL:{}
   },
   SpeedGbps.Hundred:{
      PortMedium.COPPER:{},
      PortMedium.OPTICAL:{}
   }
}

with open( "quicksilverLineTuningFiber100G.csv" ) as fh:
   for line in fh:
      if line.startswith( "ComponentId" ):
         continue
      ComponentId,SerdesId,Pre3Tap,Pre2Tap,Pre1Tap,MainTap,Post1Tap,Post2Tap = line.rstrip().split(",")

      SerdesId = int( SerdesId )
      Pre3Tap = int( Pre3Tap )
      Pre2Tap = int( Pre2Tap )
      Pre1Tap = int( Pre1Tap )
      MainTap = int( MainTap )
      Post1Tap = int( Post1Tap )
      Post2Tap = int( Post2Tap )

      taps = TxTapSettings(Pre3Tap, Pre2Tap, Pre1Tap, MainTap, Post1Tap, Post2Tap, 0)
      txTapSettingsByLane[SpeedGbps.Hundred][PortMedium.OPTICAL][SerdesId] = taps

with open( "quicksilverLineTuningFiber50G.csv" ) as fh:
   for line in fh:
      if line.startswith( "ComponentId" ):
         continue
      ComponentId,SerdesId,Pre3Tap,Pre2Tap,Pre1Tap,MainTap,Post1Tap,Post2Tap = line.rstrip().split(",")

      SerdesId = int( SerdesId )
      Pre3Tap = int( Pre3Tap )
      Pre2Tap = int( Pre2Tap )
      Pre1Tap = int( Pre1Tap )
      MainTap = int( MainTap )
      Post1Tap = int( Post1Tap )
      Post2Tap = int( Post2Tap )

      taps = TxTapSettings(Pre3Tap, Pre2Tap, Pre1Tap, MainTap, Post1Tap, Post2Tap, 0)
      txTapSettingsByLane[SpeedGbps.Fifty][PortMedium.OPTICAL][SerdesId] = taps

with open( "quicksilverLineTuningCopper50G.csv" ) as fh:
   for line in fh:
      if line.startswith( "ComponentId" ):
         continue
      ComponentId,SerdesId,Pre3Tap,Pre2Tap,Pre1Tap,MainTap,Post1Tap,Post2Tap = line.rstrip().split(",")

      SerdesId = int( SerdesId )
      Pre3Tap = int( Pre3Tap )
      Pre2Tap = int( Pre2Tap )
      Pre1Tap = int( Pre1Tap )
      MainTap = int( MainTap )
      Post1Tap = int( Post1Tap )
      Post2Tap = int( Post2Tap )

      taps = TxTapSettings(Pre3Tap, Pre2Tap, Pre1Tap, MainTap, Post1Tap, Post2Tap, 0)
      txTapSettingsByLane[SpeedGbps.Fifty][PortMedium.COPPER][SerdesId] = taps

with open( "quicksilver_si_settings.csv", "w" ) as fh:
   fields = [ field for field in SISettings.getLabels()]
   mappingWriter = csv.writer(fh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   mappingWriter.writerow( fields )
   # chipId in the SI settings is 1-indexed.
   chipId = asicId + 1

   for speed in validNifSerdesSpeeds():
      for medium in validMediaForSpeed(speed):
         if speed != SpeedGbps.TwentyFive:
            for logicalNifSerdes in range( numNifSerdesOctets * numSerdesPerOctet ):
               coreId = logicalNifSerdes // numSerdesPerOctet
               coreLane = logicalNifSerdes % numSerdesPerOctet

               if txTapSettingsByLane[speed][medium]:
                  txTapSettings = txTapSettingsByLane[speed][medium][logicalNifSerdes]
               else:
                  txTapSettings = txTapSettingsByLaneProps( speed, medium )

               mappingWriter.writerow( astuple(
                                      SISettings(1, chipId, "NPU", coreId, "TH5_NIF",
                                      coreLane, speedInMbps( speed ), medium.name,
                                      None, None, None, txTapSettings.pre3,
                                      txTapSettings.pre2, txTapSettings.pre1,
                                      txTapSettings.main, txTapSettings.post1,
                                      txTapSettings.post2, txTapSettings.post3,
                                      None, None, None )
               ) )
