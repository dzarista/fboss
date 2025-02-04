# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json

multiNpuPlatMapping = None
with open( "multi_npu_platform_mapping.json" ) as fh:
   multiNpuPlatMapping = json.load( fh )

numNpus = 2
portsPerNpu = 512
offsetPerNpu = 2048
# Per NPU platform mapping for NPU0 and NPU1
perNpuPlatMapping = {}
for npu in range( numNpus ):
   perNpuPlatMapping[ npu ] = { "ports": {} }

def npuFromPortId( portId ):
   for npu in range( numNpus ):
      npuPortOffset = npu * offsetPerNpu
      if portId >= npuPortOffset and portId < npuPortOffset + portsPerNpu:
         return npu
   # No NPU matched, this should not happen
   assert False

for port, portMapping in multiNpuPlatMapping[ "ports" ].items():
   portId = portMapping[ "mapping" ][ "id" ]
   portNpu = npuFromPortId( portId )
   portId = portId - ( portNpu * offsetPerNpu )
   portMapping[ "mapping" ][ "id" ] = portId
   portMapping[ "mapping" ][ "controllingPort" ] = portId
   perNpuPlatMapping[ portNpu ][ "ports" ][ f"{portId}" ] = portMapping

# Copy over the remaining entries in platform mapping.
# We will retain the chips mapping, that will contain the mapping for all the NPUs.
for key in multiNpuPlatMapping:
   if key != "ports":
      for npu in range( numNpus ):
         perNpuPlatMapping[ npu ][ key ] = multiNpuPlatMapping[ key ]

for npu in range( numNpus ):
   json_out = json.dumps( perNpuPlatMapping[ npu ], indent=2, sort_keys=False )
   with open( f"npu{npu}_platform_mapping.json", "w" ) as fh:
      fh.write( json_out) 
