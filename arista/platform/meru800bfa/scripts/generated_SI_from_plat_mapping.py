# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import sys

multiNpuPlatMapping = None
platformMappingFile = sys.argv[ 1 ]
with open( platformMappingFile ) as fh:
   multiNpuPlatMapping = json.load( fh )


portNameToIdMap = {}
for port, mapping in multiNpuPlatMapping[ "ports" ].items():
   portName = mapping[ "mapping" ][ "name" ]
   portNameToIdMap[ portName ] = port

for port in range(1, 129):
   for lane in range(1,9):
      portId = portNameToIdMap[ f"fab1/{port}/{lane}" ]
      txSettings = multiNpuPlatMapping[ "ports" ][ portId ][ "supportedProfiles" ][
            "42" ][ "pins" ][ "iphy" ][0][ "tx" ]
      pre3 = txSettings[ "pre3" ]
      pre2 = txSettings[ "pre2" ]
      pre = txSettings[ "pre" ]
      main = txSettings[ "main" ]
      post = txSettings[ "post" ]
      post2 = txSettings[ "post2" ]
      print( f"{port},{lane},{pre3},{pre2},{pre},{main},{post},{post2}" )
