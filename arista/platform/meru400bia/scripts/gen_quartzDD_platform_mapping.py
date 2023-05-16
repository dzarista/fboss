# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
from collections import OrderedDict
import json
import os
import Tac

"""
Author : seerpini@arista.com
Script for generating the QuartzDD platform mapping.
Assumptions:
    - Each front panel port is enumerated as 400G-8.
Output:
    - Generated platform is written to platform_mapping.json by default, can be
      override with --platform-mapping-out
Instructions:
    - Port speed and breakout are not currently configurable.
TODO
    - Accept platform settings from input/config file and generate mapping
      accordingly.
"""

# Variables to control the behavior for this script.
# Existing mappings at a port level are not replaced if preserveExistingMappings=True
preserveExistingMappings = True
# Logical port base in the SDK for NIF ports.
nifPortBase = 2
# Total number of NIF ports. Since we are operating in either 400G-4 or 800G-8 and we
# only plan to use the first port in the slot in 400G-4 mode, we have a total of 18
# front panel NIF ports.
numNifPorts = 18
# Logical port base in the SDK for fabric ports.
fabricPortBase = 1024
# Total number of fabric ports assuming that each fabric serdes is enumerated as a
# separate port.
numFabricPorts = 160
lanesPerSerdesCore = 4
numAsics = 1

def frontPanelSlotToPortType( slot ):
   return "eth"

nifSerdesOctetCoreToCoreAndFrontPanelSlot = {
      # serdes Octet: J3 core, front panel slot
      0 : ( 0, '18' ),
      1 : ( 0, '17' ),
      2 : ( 0, '16' ),
      3 : ( 0, '15' ),
      4 : ( 0, '14' ),
      5 : ( 0, '13' ),
      6 : ( 0, '12' ),
      7 : ( 0, '11' ),
      8 : ( 0, '10' ),
      9 : ( 1, '1' ),
      10 : ( 1, '2' ),
      11 : ( 1, '3' ),
      12 : ( 1, '4' ),
      13 : ( 1, '5' ),
      14 : ( 1, '6' ),
      15 : ( 1, '7' ),
      16 : ( 1, '8' ),
      17 : ( 1, '9' )
}

# Fixed fabric serdes octet to front panel slot mapping.
fabSerdesCoreToFrontPanelSlot = {}

# Assuming 100G lanes, number of lanes required by each supported port profile.
numLanesFromSupportedProfile = {
      "11" : 1,
      "22" : 4,
      "23" : 4,
      "26" : 8,
      "35" : 8,
}

def getBasePortMapping( portId=0, serdesCore="", frontPanelPort="", numLanes=1,
      firstLane=0, supportedProfiles=None, attachedCoreId=0, attachedCorePortIndex=0,
      portType=0 ):
   # Front panel port would be et1/X and based on the first lane, this can be et1/X/Y
   # where Y is firstLane+1.
   name=f"{frontPanelPort}/{firstLane+1}"
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
   for lane in range( firstLane, firstLane+numLanes ):
      serdesCoreLane = lane
      if type( serdesCore ) == int:
         serdesCoreId = serdesCore + ( lane // lanesPerSerdesCore )
         serdesCoreLane = ( lane % lanesPerSerdesCore )
         serdesCoreName = f"BC{serdesCoreId}"
      else:
         serdesCoreLane = lane
         serdesCoreName = serdesCore
      pinMapping = OrderedDict( {
         "a" : OrderedDict( {
            "chip" : serdesCoreName,
            "lane" : serdesCoreLane
         } ),
         "z" : OrderedDict( {
            "end" : OrderedDict( {
               "chip" : frontPanelPort,
               "lane" : lane
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
      for lane in range( firstLane, firstLane+reqLanes ):
         if type( serdesCore ) == int:
            serdesCoreId = serdesCore + ( lane // lanesPerSerdesCore )
            serdesCoreLane = ( lane % lanesPerSerdesCore )
            serdesCoreName = f"BC{serdesCoreId}"
         else:
            serdesCoreLane = lane
            serdesCoreName = serdesCore
         pinIPhyMapping = OrderedDict( {
            "id" : OrderedDict( {
               "chip" : serdesCoreName,
               "lane" : serdesCoreLane
            } )
         } )
         xcvrMapping = OrderedDict( {
            "id" : OrderedDict( {
               "chip" : frontPanelPort,
               "lane" : lane
            } )
         } )
         templateSuppProfiles[ suppProfile ][ "pins" ][ "iphy" ].append(
               pinIPhyMapping )
         templateSuppProfiles[ suppProfile ][ "pins" ][ "transceiver" ].append(
               xcvrMapping )
   return portMapping

def getRecyclePortMapping( portId, attachedCoreId=0 ):
   serdesCore = f"rcy{portId}"
   # There is no frontPanelPort for the recycle, hack it to match what
   # getBasePortMapping() expects.
   frontPanelPort = f"{serdesCore}/1"
   portMapping = getBasePortMapping( portId=portId, serdesCore=serdesCore,
         frontPanelPort=frontPanelPort, numLanes=1, firstLane=0,
         supportedProfiles=[ "11", ], attachedCoreId=attachedCoreId,
         attachedCorePortIndex=portId, portType=3 )
   # Recycle port does not have a "z" side of the port.
   del portMapping[ "mapping" ][ "pins" ][0][ "z" ]
   return portMapping

def getNifPortMapping( portId, serdesCore, frontPanelPort, coreId,
                       supportedProfiles=None ):
   return getBasePortMapping( portId=portId, serdesCore=serdesCore,
         frontPanelPort=frontPanelPort, numLanes=8, firstLane=0,
         supportedProfiles=supportedProfiles, attachedCoreId=coreId,
         attachedCorePortIndex=portId, portType=0 )

def getFabricPortMapping( portId, serdesCore, frontPanelPort, firstLane,
                          supportedProfiles=None ):
   portMapping = getBasePortMapping( portId=portId, serdesCore=serdesCore,
         frontPanelPort=frontPanelPort, numLanes=1, firstLane=firstLane,
         supportedProfiles=supportedProfiles, portType=1 )
   del portMapping[ "mapping" ][ "attachedCoreId" ]
   del portMapping[ "mapping" ][ "attachedCorePortIndex" ]
   return portMapping

def main():
   ap = argparse.ArgumentParser()
   ap.add_argument( '--platform-mapping-out', type=str,
         default="platform_mapping.json",
         help='Output file to write platform mapping to' )
   ap.add_argument( '--product-info', type=str,
         default="AsicToXcvrTraceInfo.csv",
         help='Mapping from ASIC Cores to Xcvr slots, trace information etc.' )
   ap.add_argument( '--bcm-config-out', type=str,
         default="bcm_config",
         help='Bcm soc properties for port lane maps and swaps.' )
   ap.add_argument( '--fabric-enabled', action="store_true",
                    help='Include fabric ports in the platform mapping' )
   ap.add_argument( '--debug', action="store_false",
                    help='Print debug information' )
   args = ap.parse_args()
   assert os.path.isfile( args.product_info )
   if not args.fabric_enabled:
      numFabricPorts = 0

   bcmSocProps = OrderedDict( {
      'laneMapping': OrderedDict(),
      'ports' : [] } )

   platMapping = OrderedDict()
   platMapping[ "ports" ] = OrderedDict( {
      "1" : getRecyclePortMapping( 1 )
      } )

   # Append nif ports.
   for port in range( nifPortBase, nifPortBase + numNifPorts ):
      portStr = str( port )
      # We are not describing non-master sub ports.
      portOctet = port - nifPortBase
      if portStr in platMapping[ 'ports' ] and preserveExistingMappings:
         continue
      supportedProfiles = [ '22', '23', '26', '35', ]
      maxLanesPerPort = max( [ numLanesFromSupportedProfile[ prof ] for prof in
         supportedProfiles ] )
      portSerdesCore = portOctet * ( maxLanesPerPort // lanesPerSerdesCore )
      serdesCore = f"BC{portSerdesCore}"
      coreId, frontPanelSlot = nifSerdesOctetCoreToCoreAndFrontPanelSlot[ portOctet ]
      frontPanelPort = f"eth1/{frontPanelSlot}"
      portMapping = getNifPortMapping( portId=port, serdesCore=portSerdesCore,
            frontPanelPort=frontPanelPort, coreId=coreId,
            supportedProfiles=supportedProfiles )
      platMapping[ 'ports' ][ portStr ] = portMapping
      bcmSocProps[ 'ports' ].append( f"\"ucode_port_{port}.BCM8885X\": \"CDGE{portSerdesCore}:core_{coreId}.{port}\"" )
      if args.debug:
         print( portMapping )

   if args.fabric_enabled :
      # Append the fabric ports.
      # Each serdes is described as a fabric port, so the enumeration here is somewhat
      # different from the NIF ports.
      for port in range( fabricPortBase, fabricPortBase + numFabricPorts ):
         portStr = str( port )
         portOctet = ( port - fabricPortBase ) // 8
         portLane = ( port % 8 )
         if portStr in platMapping[ 'ports' ] and preserveExistingMappings:
            continue
         supportedProfiles = [ '36', '37', ]
         serdesCore = f"BC{portOctet}"
         frontPanelSlot = fabSerdesCoreToFrontPanelSlot[ portOctet ]
         frontPanelPort = f"fab1/{frontPanelSlot}"
         portMapping = getFabricPortMapping( portId=port, serdesCore=serdesCore,
               frontPanelPort=frontPanelPort, firstLane=portLane,
               supportedProfiles=supportedProfiles )
         platMapping[ 'ports' ][ portStr ] = portMapping
         if args.debug:
            print( portMapping )

   # Append the chips enumeration.
   # Serdes cores is a superset of octet cores required for fabric and front panel
   # ports.
   platMapping[ "chips" ] = []
   platMapping[ "chips" ].append( OrderedDict( {
         "name" : "rcy1",
         "type" : 1,
         "physicalID" : 55
   } ) )
   serdesCores = max( numNifPorts * ( 8//lanesPerSerdesCore ), numFabricPorts//8 )
   for core in range( serdesCores ):
      platMapping[ "chips" ].append( OrderedDict(
         {
            "name": f"BC{core}",
            "type" : 1,
            "physicalID": core
         } ) )
   numFrontPanelPorts = 18
   for port in range( 1, numFrontPanelPorts+1 ):
      platMapping[ "chips" ].append( OrderedDict(
         {
            "name": f"{frontPanelSlotToPortType(port)}1/{port}",
            "type" : 3,
            "physicalID": port 
         } ) )

   platMapping[ "platformSettings" ] = OrderedDict()
   platMapping[ "portConfigOverrides" ] = []
   platMapping[ "platformSupportedProfiles" ] = []
   # Port Attributes by profile
   portAttrsByProfile = {
         #profileId : ( speed, numLanes, modulation, fec, medium, interfaceMode )
         '11' : ( 10000, 1, 1, 1, 1, 10 ),
         '22' : ( 10000, 4, 1, 528, 1, 12 ),
         '23' : ( 10000, 4, 1, 528, 3, 12 ),
         # TODO : we might need to adjust some of the attributes here.
         '26' : ( 40000, 8, 2, 545, 3, 41 ),
         '35' : ( 40000, 8, 2, 545, 1, 41 ),
   }
   # Append the supportedProfiles information.
   for profileID in numLanesFromSupportedProfile.keys():
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
   with open( args.platform_mapping_out, "w") as fh:
      fh.write( json_out )

   laneMapping = bcmSocProps[ 'laneMapping' ]
   for line in open( args.product_info, "r"):
      if line.startswith( 'SystemComponent' ):
         continue
      chip, serdes, xcvrSlot, xcvrLane, _, direction, swap = line.rstrip().split(",")
      if int( chip ) >= numAsics:
         continue
      nifOctet = -1
      for serdesCoreOctet, xcvrSlotMap in nifSerdesOctetCoreToCoreAndFrontPanelSlot.items():
         if xcvrSlotMap[ 1 ] == xcvrSlot:
            nifOctet = serdesCoreOctet
            break;
      assert nifOctet >= 0
      nifLane = nifOctet * 8 + int( xcvrLane )
      if nifLane not in laneMapping:
         laneMapping[ nifLane ] = {}
      laneMapping[ nifLane ][ direction ] = ( serdes, "1" if swap == "Yes" else "0" )
   with open( args.bcm_config_out, "w" ) as fh:
      fh.write( ",\n".join( bcmSocProps[ "ports" ] ) + ",\n" )
      for lane in laneMapping:
         laneInfo = laneMapping[ lane ]
         laneMapOutput = f'"lane_to_serdes_map_nif_lane{lane}": '
         for direction in ( 'rx', 'tx' ):
            laneInfoEntry = laneInfo[ direction ]
            if direction == 'rx':
               laneMapOutput += f'"{direction}{laneInfoEntry[0]}:'
            else:
               laneMapOutput += f'{direction}{laneInfoEntry[0]}",\n'
            fh.write( f'"phy_{direction}_polarity_flip_phy{lane}.0": "{laneInfoEntry[1]}",\n' )
         fh.write( laneMapOutput )

if __name__ == '__main__':
   main()
