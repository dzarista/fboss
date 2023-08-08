# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
from collections import OrderedDict

"""
Author : seerpini@arista.com
Script for generating the Viper fabric port platform mapping.
Assumptions:
    - Each fabric serdes is enumerated as a 100G port. Supported profiles 36, 37 correspond to 100G optical and copper.
    - Each front panel port is enumerated as either 400G-4 (only master port is
      used), or 800G-8.
Output:
    - Generated platform is written to viper_platform_mapping.json
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

nifSerdesCoreToCoreAndFrontPanelSlot = {
      # serdes Octet : J3 core, front panel slot
      0 : ( 0, '19' ),
      1 : ( 0, '16' ),
      2 : ( 0, '18' ),
      3 : ( 0, '15' ),
      4 : ( 0, '17' ),
      5 : ( 1, '13' ),
      6 : ( 1, '11' ),
      7 : ( 1, '14' ),
      8 : ( 1, '12' ),
      9 : ( 2, '20' ),
      10 : ( 2, '21' ),
      11 : ( 2, '22' ),
      12 : ( 2, '23' ),
      13 : ( 3, '27' ),
      14 : ( 3, '28' ),
      15 : ( 3, '25' ),
      16 : ( 3, '26' ),
      17 : ( 3, '24' )
}

# Fixed fabric serdes octet to front panel slot mapping for Viper.
fabSerdesCoreToFrontPanelSlot = {
      0 : '10',
      1 : '9',
      2 : '8',
      3 : '7',
      4 : '6',
      5 : '5',
      6 : '4',
      7 : '3',
      8 : '1',
      9 : '2',
      10 : '30',
      11 : '29',
      12 : '32',
      13 : '33',
      14 : '31',
      15 : '34',
      16 : '38',
      17 : '37',
      18 : '35',
      19 : '36'
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
                     #"transceiver" : [],
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
         #templateSuppProfiles[ suppProfile ][ "pins" ][ "transceiver" ].append(
         #      xcvrMapping )
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

platMapping = OrderedDict()
platMapping[ "ports" ] = OrderedDict( {
   "1" : getRecyclePortMapping( 1 )
   } )

supportedProfilesByPortType = {
      'eth' :  [ '24', '38', '39', ],
      'fab' :  [ '36', '37', '41', '42'],
}

# Append nif ports.
for port in range( nifPortBase, nifPortBase + numNifPorts ):
   portStr = str( port )
   # We are not describing non-master sub ports.
   portOctet = port - nifPortBase
   if portStr in platMapping[ 'ports' ] and preserveExistingMappings:
      continue
   supportedProfiles = supportedProfilesByPortType[ 'eth' ]
   serdesCore = f"BC{portOctet}"
   coreId, frontPanelSlot = nifSerdesCoreToCoreAndFrontPanelSlot[ portOctet ]
   frontPanelPort = f"eth1/{frontPanelSlot}"
   portMapping = getNifPortMapping( portId=port, serdesCore=serdesCore,
         frontPanelPort=frontPanelPort, coreId=coreId,
         supportedProfiles=supportedProfiles )
   platMapping[ 'ports' ][ portStr ] = portMapping
   if debug:
      print( portMapping )

# Append the fabric ports.
# Each serdes is described as a fabric port, so the enumeration here is somewhat
# different from the NIF ports.
for port in range( fabricPortBase, fabricPortBase + numFabricPorts ):
   portStr = str( port )
   portOctet = ( port - fabricPortBase ) // 8
   portLane = ( port % 8 )
   if portStr in platMapping[ 'ports' ] and preserveExistingMappings:
      continue
   supportedProfiles = supportedProfilesByPortType[ 'fab' ]
   serdesCore = f"BC{portOctet}"
   frontPanelSlot = fabSerdesCoreToFrontPanelSlot[ portOctet ]
   frontPanelPort = f"fab1/{frontPanelSlot}"
   portMapping = getFabricPortMapping( portId=port, serdesCore=serdesCore,
         frontPanelPort=frontPanelPort, firstLane=portLane,
         supportedProfiles=supportedProfiles )
   platMapping[ 'ports' ][ portStr ] = portMapping
   if debug:
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
serdesCores = max( numNifPorts, numFabricPorts//8 )
for core in range( serdesCores ):
   platMapping[ "chips" ].append( OrderedDict(
      {
         "name": f"BC{core}",
         "type" : 1,
         "physicalID": core
      } ) )
numFrontPanelPorts = 38
for port in range( numFrontPanelPorts ):
   frontPanelSlot = port+1
   frontPanelPortType = frontPanelSlotToPortType( frontPanelSlot )
   platMapping[ "chips" ].append( OrderedDict(
      {
         "name": f"{frontPanelPortType}1/{frontPanelSlot}",
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
      24 : ( 200000, 4, 2, 11, 1, 12 ),
      36 : ( 53125, 1, 2, 545, 1, 41 ),
      37 : ( 53125, 1, 2, 545, 3, 41 ),
      38 : ( 400000, 4, 2, 11, 2, 21 ),
      39 : ( 800000, 8, 2, 11, 2, 23 ),
      41 : ( 106250, 1, 2, 544, 1, 41 ),
      42 : ( 106250, 1, 2, 544, 3, 41 ),
}
# Append the supportedProfiles information.
for profileID in ( 11, 24, 36, 37, 38, 39 ):
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
with open( "viper_platform_mapping.json", "w") as fh:
   fh.write( json_out )

nifFrontPanelSlotToJ3CoreAndSerdesCore = {}
with open( "viper_static_mapping.csv", "w" ) as fh:
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
   for serdesCore in nifSerdesCoreToCoreAndFrontPanelSlot.keys():
      frontPanelSlot = nifSerdesCoreToCoreAndFrontPanelSlot[ serdesCore ][ 1 ]
      nifFrontPanelSlotToJ3CoreAndSerdesCore[ int( frontPanelSlot ) ] = \
            ( nifSerdesCoreToCoreAndFrontPanelSlot[ serdesCore ][ 0 ], serdesCore )
      for lane in range( 8 ):
         fh.write(
               f"1,1,NPU,{serdesCore},J3_NIF,{lane},{lane},{lane},N,N,1,{frontPanelSlot},TRANSCEIVER,0,OSFP,{lane},{lane},{lane},N,N\n"
               )
   for serdesCore,frontPanelSlot in fabSerdesCoreToFrontPanelSlot.items():
      for lane in range( 8 ):
         fh.write(
               f"1,1,NPU,{serdesCore},J3_FE,{lane},{lane},{lane},N,N,1,{frontPanelSlot},TRANSCEIVER,0,OSFP,{lane},{lane},{lane},N,N\n"
               )

with open( "viper_port_profile_mapping.csv", "w" ) as fh:
   # Description of fields in the order of their appearance:
   # Logical_PortID : Logical port ID used in the bcm soc properties.
   # Port_Name : Port name used in the platform mapping.
   # Attached_CoreId : CoreId on ASIC that the port is attached to.
   # Attached_Core_PortID : Core local portID assigned to this port.
   # NOTE : For Fabric ports, there is no core binding, the corresponding
   # Attached_CoreId and Attached_Core_PortID can be left empty.
   # Recycle port is a special port with port id 1, it is given internal serdes core
   # ID 55.
   fh.write("1,rcy1/1/55,11,0,1\n")
   # CPU port is 0, RCY port is 1, NIF ports start from logical port Id 2.
   # Fabric ports start from logical port Id 1024.
   nifLogicalPortIdBase = 2
   fabLogicalPortId = 1024
   fabSupportedProfiles = '-'.join( supportedProfilesByPortType[ 'fab' ] )
   nifSupportedProfiles = '-'.join( supportedProfilesByPortType[ 'eth' ] )
   for port in range( numFrontPanelPorts ):
      frontPanelSlot = port+1
      frontPanelPortType = frontPanelSlotToPortType( frontPanelSlot )
      portStrPrefix = f"{frontPanelPortType}1/{frontPanelSlot}"
      if frontPanelPortType == "fab":
         for subPort in range( 1,9 ):
            portStr = f"{portStrPrefix}/{subPort}"
            fh.write( f"{fabLogicalPortId},{portStr},{fabSupportedProfiles},,\n" )
            fabLogicalPortId += 1
      elif frontPanelPortType == "eth":
         portStr = f"{portStrPrefix}/1"
         # fapPortId
         attachedCoreId, serdesCoreId = nifFrontPanelSlotToJ3CoreAndSerdesCore[ frontPanelSlot ]
         nifLogicalPortId = nifLogicalPortIdBase + serdesCoreId
         attachedCorePortId = nifLogicalPortId
         assert nifLogicalPortId - nifLogicalPortIdBase < numNifPorts
         fh.write(
               f"{nifLogicalPortId},{portStr},{nifSupportedProfiles},{attachedCoreId},{attachedCorePortId}\n" )
         nifLogicalPortId += 1
      else:
         assert False, "Invalid frontPanelPortType"
