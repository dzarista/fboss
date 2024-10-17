#!/bin/env python3
# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import sys
sys.path.append( "../../lib" )
import csv
from dataclasses import astuple
from PlatformUtils import PortMedium, SpeedGbps, validMediaForSpeed, \
   validNifSerdesSpeeds, validFabricSerdesSpeeds, speedInMbps, \
   txTapSettingsByLaneProps
from VendorMappings import StaticMapping, PortProfileMapping, SISettings
from ViperLinkData import fabricTraceLengthByLogicalLane

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
# Number of ASICs in the system
numAsics = 1
numAsicCores = 4
# Number of serdes per serdes quartet. QSFP Mgmt port is on a 4x25G serdes core.
numSerdesPerQuartet = 4
# Number of serdes per serdes octet. Peregrine 8x100G serdes core on J3.
numSerdesPerOctet = 8
# Logical port base in the SDK for NIF ports.
nifPortBase = 2
# Total number of NIF ports. Since we are operating in either 400G-4 or 800G-8 and we
# only plan to use the first port in the slot in 400G-4 mode, we have a total of 18
# front panel NIF ports.
numNifSerdesOctets = 18
numNifSerdesQuartets = 1
numNifSerdes = numNifSerdesOctets * numSerdesPerOctet \
   + numNifSerdesQuartets * numSerdesPerQuartet
# Logical port base in the SDK for fabric ports.
fabricPortBase = 1024
# Total number of fabric ports assuming that each fabric serdes is enumerated as a
# separate port.
numFabricSerdesOctets = 20
numFabricSerdes = numFabricSerdesOctets * numSerdesPerOctet
# Slot number for the 4x25G QSFP port.
qsfpPortFrontPanelSlot = 39
# Print debug information
debug = False

# Viper has a non-linear front panel slot to port type mapping.
# First 10 ports and last 10 ports on the front panel are Fabric ports.
# The 18 ports in between are NIF ports including the special QSFP port at
# slot 39.
def frontPanelSlotToPortType( slot ):
   assert 1 <= slot <= qsfpPortFrontPanelSlot
   if 11 <= slot <= 28 or slot == qsfpPortFrontPanelSlot:
      return "nif"
   else:
      return "fabric"

def frontPanelSlots():
   numFrontPanelPorts = numFabricSerdesOctets + numNifSerdesOctets + numNifSerdesQuartets
   return list( range( 1, numFrontPanelPorts + 1 ) )

# Number of serdes/lanes per front panel slot. All slots except slot 39 (QSFP port)
# have 8 lanes.
def numLanesInFrontPanelSlot( slot ):
   assert 1 <= slot <= qsfpPortFrontPanelSlot
   if slot == qsfpPortFrontPanelSlot:
      return 4
   else:
      return 8

# Returns the first portId on a given asic core (assuming 0 indexed).
# This helper can also be used to return the total number of ports all the cores
# before coreId have.
def firstPortIdOffsetByAsicCore( coreId ):
   # in 400g-4x2 breakout, we will have two ports per serdes octet.
   # Note, this only accounts for ports that are statically assigned to ASIC cores.
   # The QSFP port is treated differently in the frontPanelSlot iteration below.
   portsPerCore = { 0 : 10, 1 : 8, 2 : 8, 3 : 10 }
   firstPortId = 0
   for core in range( coreId ):
      firstPortId += portsPerCore[ core ]
   return firstPortId

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
      # we treat the 4x25G QSFP port as core 18, and we bind this to core 1 for now.
      18 : 1,
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

supportedProfilesBySpeed = {
      # SpeedGbps : { subport : [], subport : [] ... }
      SpeedGbps.Hundred : { 1 : [ '22', '23' ] },
      SpeedGbps.FourHundred : { 1 : [ '24', '35', '38', '39', '45' ], 5 : [ '24', '38', '45' ] },
      SpeedGbps.HundredAndSix : { 1 : [ '36', '37', '41', '42'] }
}

asicId = 0
fabricLogicalLaneTraceLengths = fabricTraceLengthByLogicalLane( asicId,
                                                                numFabricSerdes )

asicSerdesMappings = []
for asic in range( numAsics ):
   asicSerdesMappings.append( { 'fabric' : {}, 'nif': {} } )
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
      frontPanelSlot = int( frontPanelSlot )
      portType = frontPanelSlotToPortType( frontPanelSlot )
      systemSerdesId = int( systemSerdesId )
      # Adjust fabric serdes Id to start from 0, they are currently monotonously
      # increasing after the NIF serdes.
      if portType == 'fabric':
         systemSerdesId -= numNifSerdes
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

nifFrontPanelSlotToAsicCoreAndSerdesCore = {}
fabFrontPanelLaneToLogicalLane = {}
with open( "viper_static_mapping.csv", "w", newline="" ) as fh, open( "bcm_config", "w" ) as bcmConfigFh:
   fields = [ field.name for field in StaticMapping.getFields()]
   mappingWriter = csv.writer(fh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   mappingWriter.writerow( fields )
   # Special entry for recycle port, which is attached to J3 with a special serdes
   # core Id 55 (this serdes core Id is derived from a reverse calculation of the bcm
   # soc property for recycle port base).
   mappingWriter.writerow( astuple(
      StaticMapping( 1, 1, "NPU", 55, "J3_RCY", 0, None, None, None, None, None,
                    None, None, None, None, None, None, None, None, None )
   ) )
   def genMappingsForSerdesCore( serdesCore, firstSerdes, numSerdes, portType ): 
      tempProps = {}
      tempBcmLaneMapProps = {}
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
            nifFrontPanelSlotToAsicCoreAndSerdesCore[ frontPanelSlot ] = (
                  nifSerdesCoreToAsicCore[ serdesCore ], serdesCore )
            asicCoreType = "J3_NIF"
            polaritySwapType = "phy"
         else:
            # For fabric ports, logical lane is the same as the serdes pysical Rx
            # Lane.
            logicalLane = rxLane % numSerdes
            asicCoreType = "J3_FE"
            polaritySwapType = "fabric"

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
         # For fabric ports, the logicalLane need not match lane, so if we write it
         # here we will be out of order. We will stash them here so that we can write
         # them to the relevant files in the order of logical lanes.
         tempProps[ logicalLane ] = StaticMapping(
               1,1,"NPU",serdesCore,asicCoreType,logicalLane,txLane,rxLane,txPolSwap,rxPolSwap,1,frontPanelSlot,"TRANSCEIVER",0,"OSFP",frontPanelLane,frontPanelLane,frontPanelLane,"N","N"
         )
         # bcm logicalLane is a global lane number that is in range (0,144) for NIF
         # and (0,160) for Fabric.
         bcmLogicalLane = logicalLane + firstSerdes
         if portType == "fabric":
            fabFrontPanelLaneToLogicalLane[ frontPanelSlot * 8 + frontPanelLane ] = bcmLogicalLane

         # BCM soc properties for lane maps and polarity swaps.
         tempBcmLaneMapProps[ logicalLane ] = f"\"lane_to_serdes_map_{portType}_lane{bcmLogicalLane}.BCM8889X\": \"rx{rxLane}:tx{txLane}\",\n"
         tempBcmPolSwapProps[ logicalLane ] = (
               f"\"phy_rx_polarity_flip_{polaritySwapType}{bcmLogicalLane}.BCM8889X\": \"{rxPolSwapProp}\",\n",
               f"\"phy_tx_polarity_flip_{polaritySwapType}{bcmLogicalLane}.BCM8889X\": \"{txPolSwapProp}\",\n" )

      for lane in range( numSerdes ):
         mappingWriter.writerow( astuple( tempProps[ lane ] ) )
         for prop in tempBcmLaneMapProps[ lane ]:
            bcmConfigFh.write( prop )
         for prop in tempBcmPolSwapProps[ lane ]:
            bcmConfigFh.write( prop )

   for serdesCore in range( numNifSerdesOctets ):
      genMappingsForSerdesCore( serdesCore, serdesCore * 8, 8, "nif" )
   # Generate the static mapping and bcm lane map config for QSFP port. We treat this
   # as NIF core 18 for now.
   genMappingsForSerdesCore( numNifSerdesOctets, numNifSerdesOctets * 8, 4, "nif" )
   for serdesCore in range( numFabricSerdesOctets ):
      genMappingsForSerdesCore( serdesCore, serdesCore * 8, 8, "fabric" )

with open( "viper_port_profile_mapping.csv", "w" ) as fh, open( "bcm_config", "a" ) as bcmConfigFh:
   fields = [ field.name for field in PortProfileMapping.getFields()]
   mappingWriter = csv.writer(fh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   mappingWriter.writerow( fields )
   # Description of fields in the order of their appearance:
   # Global PortID : Global port ID across all ASICs in the system.
   # Logical_PortID : Logical port ID used in the bcm soc properties.
   # Port_Name : Port name used in the platform mapping.
   # Supported_Port_Profiles : FBOSS Port profile (speed and other L1 attributes)
   #    supported by the port.
   # Attached_CoreId : CoreId on ASIC that the port is attached to.
   # Attached_Core_PortID : Core local portID assigned to this port.
   # NOTE : For Fabric ports, there is no core binding, the corresponding
   #    Attached_CoreId and Attached_Core_PortID can be left empty.
   # Virtual_Device_ID : Virtual device ID for FE ASICs.

   # Since fabric serdes on J3 don't have a core mapping and the notion of Virtual
   # Devices does not exist on J3, always set this to 0.
   virtualDeviceId = 0
   # Recycle port is a special port with port id 1, it is given internal serdes core
   # ID 55.
   mappingWriter.writerow( astuple(
      PortProfileMapping(1,1,"rcy1/1/55",11,0,1,virtualDeviceId )
   ) )
   # CPU port is 0, RCY port is 1, NIF ports start from logical port Id 2.
   # Fabric ports start from logical port Id 1024.
   nifLogicalPortIdBase = 2
   fabLogicalPortIdBase = 1024
   fabSupportedProfiles = '-'.join( supportedProfilesBySpeed[
      SpeedGbps.HundredAndSix ][ 1 ] )
   attachedCorePortIdsByAsicCore = { core : [] for core in range( numAsicCores ) }
   for frontPanelSlot in frontPanelSlots():
      frontPanelPortType = frontPanelSlotToPortType( frontPanelSlot )
      if frontPanelPortType == "fabric":
         for subPort in range( 1,9 ):
            portStr = f"fab1/{frontPanelSlot}/{subPort}"
            fabLogicalPortId = fabLogicalPortIdBase + fabFrontPanelLaneToLogicalLane[
                  frontPanelSlot * 8 + ( subPort - 1 ) ]
            mappingWriter.writerow( astuple(
               PortProfileMapping( fabLogicalPortId, fabLogicalPortId, portStr,
                                  fabSupportedProfiles, None, None, virtualDeviceId )
            ) )
      elif frontPanelPortType == "nif":
         subPorts = [ 1 ]
         if frontPanelSlot == qsfpPortFrontPanelSlot:
            #100G-4, QSFP
            bcmConfigPortPrefix="CGE"
            speedInGbps = SpeedGbps.Hundred
         else:
            #400G-4
            bcmConfigPortPrefix="CDGE4_"
            speedInGbps = SpeedGbps.FourHundred
            # Breakout only supported on OSFP front panel NIF ports.
            subPorts.append( 5 )
         for subPort in subPorts:
            portStr = f"eth1/{frontPanelSlot}/{subPort}"
            # fapPortId
            attachedCoreId, serdesCoreId = nifFrontPanelSlotToAsicCoreAndSerdesCore[ frontPanelSlot ]
            # 400G-4 CDGE core Id
            if subPort == 1:
               # Though we call it cdgeCore_4 here, this calculation also works for
               # QSFP port since that is treated as NIF core 18 with serdes 144-147.
               cdgeCore_4 = serdesCoreId * 2
            elif subPort == 5:
               cdgeCore_4 = serdesCoreId * 2 + 1
            nifSupportedProfiles = '-'.join( supportedProfilesBySpeed[ speedInGbps ][
               subPort ] )
            nifLogicalPortId = nifLogicalPortIdBase + cdgeCore_4
            # Reuse attachedCorePortId since it a core local construct.
            attachedCorePortId = nifLogicalPortId - firstPortIdOffsetByAsicCore(
                  attachedCoreId )
            # There is no easy way to derive the attachedCorePortId for QSFP port on
            # slot 39 as the serdes core is 18, but it is assigned to core 1.
            # Override the attachedCorePortId for QSFP port to be the max
            # attachedCorePortId on its core + 1.
            # We can only do this because the QSFP front panel slot is the last slot
            # in the frontPanelSlot iteration loop.
            if frontPanelSlot == qsfpPortFrontPanelSlot:
               attachedCorePortId = max( attachedCorePortIdsByAsicCore[
                  attachedCoreId ] ) + 1
            else:
               # For all other slots keep track of the assigned attachedCorePortIds
               # by Asic core.
               attachedCorePortIdsByAsicCore[ attachedCoreId ].append( attachedCorePortId )
            assert nifLogicalPortId - nifLogicalPortIdBase < ( numNifSerdesOctets +
                  numNifSerdesQuartets ) * 2
            bcmConfigFh.write( f"\"ucode_port_{nifLogicalPortId}.BCM8889X\": \"{bcmConfigPortPrefix}{cdgeCore_4}:core_{attachedCoreId}.{attachedCorePortId}\",\n" )
            mappingWriter.writerow( astuple(
               PortProfileMapping( nifLogicalPortId, nifLogicalPortId, portStr,
                                  nifSupportedProfiles, attachedCoreId,
                                  attachedCorePortId, virtualDeviceId )
            ) )
            nifLogicalPortId += 1
      else:
         assert False, "Invalid frontPanelPortType"

with open( "viper_si_settings.csv", "w" ) as fh:
   fields = [ field.name for field in SISettings.getFields()]
   mappingWriter = csv.writer(fh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   mappingWriter.writerow( fields )
   # chipId in the SI settings is 1-indexed.
   chipId = asicId + 1

   for speed in validNifSerdesSpeeds():
      for medium in validMediaForSpeed(speed):
         if speed != SpeedGbps.TwentyFive:
            # NIF serdes cores 0-17 all have 8 serdes per core.
            for logicalNifSerdes in range( numNifSerdesOctets * numSerdesPerOctet ):
               coreId = logicalNifSerdes // numSerdesPerOctet
               coreLane = logicalNifSerdes % numSerdesPerOctet
               txTapSettings = txTapSettingsByLaneProps( speed, medium )
               mappingWriter.writerow( astuple(
                                      SISettings(1, chipId, "NPU", coreId, "J3_NIF",
                                      coreLane, speedInMbps( speed ), medium.name,
                                      None, None, None, txTapSettings.pre3,
                                      txTapSettings.pre2, txTapSettings.pre1,
                                      txTapSettings.main, txTapSettings.post1,
                                      txTapSettings.post2, txTapSettings.post3,
                                      None, None, None )
               ) )
         else:
            # NIF serdes core 18 has 4 serdes (only NIF serdes quartet on the ASIC).
            coreId = numNifSerdesOctets
            firstSerdes = numNifSerdesOctets * numSerdesPerOctet
            for logicalNifSerdes in range( firstSerdes, firstSerdes + 4 ):
               coreLane = ( logicalNifSerdes  - firstSerdes ) % 4
               txTapSettings = txTapSettingsByLaneProps( speed, medium )
               mappingWriter.writerow( astuple(
                                      SISettings(1, chipId, "NPU", coreId, "J3_NIF",
                                      coreLane, speedInMbps( speed ), medium.name,
                                      None, None, None, txTapSettings.pre3,
                                      txTapSettings.pre2, txTapSettings.pre1,
                                      txTapSettings.main, txTapSettings.post1,
                                      txTapSettings.post2, txTapSettings.post3,
                                      None, None, None )
               ) )

   for speed in validFabricSerdesSpeeds():
      for medium in validMediaForSpeed(speed):
         for logicalFabSerdes in range( numFabricSerdes ):
            coreId = logicalFabSerdes // numSerdesPerOctet
            coreLane = logicalFabSerdes % numSerdesPerOctet
            txTapSettings = txTapSettingsByLaneProps( speed, medium,
                              fabricLogicalLaneTraceLengths[ logicalFabSerdes
                                                ].traceLengthToNextEpInInches )
            mappingWriter.writerow( astuple(
                                   SISettings(1, chipId, "NPU", coreId, "J3_FE",
                                   coreLane, speedInMbps( speed ), medium.name,
                                   None, None, None, txTapSettings.pre3,
                                   txTapSettings.pre2, txTapSettings.pre1,
                                   txTapSettings.main, txTapSettings.post1,
                                   txTapSettings.post2, txTapSettings.post3,
                                   None, None, None )
            ) )
