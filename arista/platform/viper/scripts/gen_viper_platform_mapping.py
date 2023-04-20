# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import copy
from collections import OrderedDict

"""
Author : seerpini@arista.com
Script for generating the Viper fabric port platform mapping.
Assumptions:
    - viper_platform_mapping.json exists in CWD and is a valid json file.
    - "chips" dict is already populated correctly for "fab1/X" ports and the corresponding BC(Y) cores.
      this script does not populate the "chips" dictionary.
    - Each fabric serdes is enumerated as a 100G port. Supported profiles 36, 37 correspond to 100G optical and copper.
Output:
    - Updated platform mapping is written to new_viper_mapping.json
Instructions:
    - Please update the following variables to control how fabric port mappings are generated.
    - Port speed and breakout are not currently parameterized by the script.
"""

# Variables to control the behavior for the script
# Existing mappings at a port level are not replaced if preserveExistingMappings=True
preserveExistingMappings = True
# Logical port base in the SDK for fabric ports.
fabricPortBase = 1024
# Total number of fabric ports.
numFabricPorts = 160
# Print debug information
debug = False

platMapping = None
with open( "viper_platform_mapping.json" ) as fh:
   platMapping = json.load( fh, object_pairs_hook=OrderedDict )

# Fixed fabric serdes octet to front panel slot mapping for Viper.
fabSerdesOctetToFrontPanelSlot = {
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

def getFabricPortMappingTemplate( supportedProfiles=[] ):
   templatePortMapping = OrderedDict()
   templatePortMapping[ "id" ] = 0
   templatePortMapping[ "name" ] = ""
   templatePortMapping[ "controllingPort" ] = 0
   pinMapping = OrderedDict()
   pinMapping[ "a" ] = OrderedDict()
   pinMapping[ "a" ][ "chip" ] = ""
   pinMapping[ "a" ][ "lane" ] = 0
   pinMapping[ "z" ] = OrderedDict()
   pinMapping[ "z" ][ "end" ] = OrderedDict()
   pinMapping[ "z" ][ "end" ][ "chip" ] = ""
   pinMapping[ "z" ][ "end" ][ "lane" ] = 0
   templatePortMapping[ "pins" ] = [ pinMapping, ]
   templatePortMapping[ "portType" ] = 1
   pinIPhyMapping = OrderedDict()
   pinIPhyMapping[ "id" ] = OrderedDict()
   pinIPhyMapping[ "id" ][ "chip" ] = ""
   pinIPhyMapping[ "id" ][ "lane" ] = 0
   templateSuppProfiles = OrderedDict()
   for suppProfile in supportedProfiles:
       templateSuppProfiles[ suppProfile ] = OrderedDict()
       templateSuppProfiles[ suppProfile ][ "pins" ] = OrderedDict( { "iphy" : [
          copy.deepcopy(pinIPhyMapping), ] } )
   portMapping = OrderedDict()
   portMapping[ "mapping" ] = templatePortMapping
   portMapping[ "supportedProfiles" ] = templateSuppProfiles
   return portMapping

for port in range( fabricPortBase, fabricPortBase + numFabricPorts ):
   portStr = str( port )
   portOctet = ( port - fabricPortBase ) // 8
   portLane = ( port % 8 )
   if portStr in platMapping[ 'ports' ] and preserveExistingMappings:
      continue
   else:
      supportedProfiles = [ '36', '37', ]
      portMapping = getFabricPortMappingTemplate( supportedProfiles=supportedProfiles )
      assert 'mapping' in portMapping
      portMapping[ 'mapping' ][ 'id' ] = port
      portMapping[ 'mapping' ][ 'controllingPort' ] = port
      fabFrontPanelMasterPortStr = "fab1/" + fabSerdesOctetToFrontPanelSlot[ portOctet ]
      portMapping[ 'mapping' ][ 'name' ] = fabFrontPanelMasterPortStr + "/" + str(
            portLane+1 )
      portMapping[ 'mapping' ][ 'pins'][ 0 ][ 'a' ][ 'chip' ] = "BC" + str( portOctet )
      portMapping[ 'mapping' ][ 'pins'][ 0 ][ 'a' ][ 'lane' ] = portLane
      portMapping[ 'mapping' ][ 'pins'][ 0 ][ 'z' ][ 'end' ][ 'chip' ] = fabFrontPanelMasterPortStr
      portMapping[ 'mapping' ][ 'pins'][ 0 ][ 'z' ][ 'end' ][ 'lane' ] = portLane
      assert 'supportedProfiles' in portMapping
      for suppProfile in supportedProfiles:
         assert suppProfile in portMapping[ 'supportedProfiles' ]
         portMapping[ 'supportedProfiles' ][ suppProfile ][ 'pins' ][ 'iphy' ][
               0 ][ 'id' ][ 'chip' ] = "BC" + str( portOctet )
         portMapping[ 'supportedProfiles' ][ suppProfile ][ 'pins' ][ 'iphy' ][
               0 ][ 'id' ][ 'lane' ] = portLane
      platMapping[ 'ports' ][ portStr ] = portMapping
      if debug:
          print( portMapping )

json_out = json.dumps( platMapping, indent=2, sort_keys=False )

with open( "new_viper_mapping.json", "w") as fh:
   fh.write( json_out )
