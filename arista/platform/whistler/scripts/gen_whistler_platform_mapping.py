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
preserveExistingMappings = True
# Logical port base in the SDK for fabric ports.
fabricPortBase = 0
# Whistler has two Ramon3 ASICs with 512x100G serdes on each ASIC.
numAsics = 2
# Total number of fabric ports assuming that each fabric serdes is enumerated as a
# separate port.
numFabricPorts = 128 * 8
# Print debug information
debug = False
numNifPorts = 0

# Assuming 100G lanes, number of lanes required by each supported port profile.
numLanesFromSupportedProfile = {
      "36" : 1,
      "37" : 1,
}

def getBasePortMapping( portId=0, serdesCore="", frontPanelPort="", numLanes=1,
      firstLane=0, supportedProfiles=None, attachedCoreId=0, attachedCorePortIndex=0,
      portType=0 ):
   # Front panel port would be et1/X or fab1/X and based on the first lane, this can
   # be et1/X/Y (or fab1/X/Y) where Y is firstLane+1.
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
      pinMapping = OrderedDict( {
         "a" : OrderedDict( {
            "chip" : serdesCore,
            "lane" : lane
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
         pinIPhyMapping = OrderedDict( {
            "id" : OrderedDict( {
               "chip" : serdesCore,
               "lane" : lane
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

def getFabricPortMapping( portId, serdesCore, frontPanelPort, firstLane,
                          supportedProfiles=None ):
   portMapping = getBasePortMapping( portId=portId, serdesCore=serdesCore,
         frontPanelPort=frontPanelPort, numLanes=1, firstLane=firstLane,
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

# Append the fabric ports.
# Each serdes is described as a fabric port, so the enumeration here is somewhat
# different from the NIF ports.
assert len( fabricFrontPanelMap ) == numFabricPorts
for portId in range( numFabricPorts ):
   frontPanelPort = str( portId + 1 )
   frontPanelInfo = fabricFrontPanelMap[ frontPanelPort ]
   portId += fabricPortBase
   portStr = str( portId )
   frontPanelSlot = ( ( portId ) // 8 ) + 1
   assert str( frontPanelSlot ) == frontPanelInfo[ 3 ]
   frontPanelLane = ( portId % 8 )
   assert str( frontPanelLane + 1 ) == frontPanelInfo[ 4 ]
   if portStr in platMapping[ 'ports' ] and preserveExistingMappings:
      continue
   supportedProfiles = [ '36', '37', ]
   serdesCore = frontPanelInfo[ 8 ]
   serdesCore = f"BC{serdesCore}"
   frontPanelPort = f"fab1/{frontPanelSlot}"
   portMapping = getFabricPortMapping( portId=portId, serdesCore=serdesCore,
         frontPanelPort=frontPanelPort, firstLane=frontPanelLane,
         supportedProfiles=supportedProfiles )
   platMapping[ 'ports' ][ portStr ] = portMapping
   if debug:
      print( portMapping )

# Append the chips enumeration.
# Serdes cores is a superset of octet cores required for fabric and front panel
# ports.
platMapping[ "chips" ] = []
serdesCores = max( numNifPorts, numFabricPorts//8 ) // numAsics
for core in range( serdesCores ):
   platMapping[ "chips" ].append( OrderedDict(
      {
         "name": f"BC{core}",
         "type" : 1,
         "physicalID": core
      } ) )
numFrontPanelPorts = 128
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
}
# Append the supportedProfiles information.
for profileID in ( 36, 37 ):
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
