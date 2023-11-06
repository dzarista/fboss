#!/usr/bin/env python3
# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from typing import List, Tuple

import argparse
import copy
import json
import os

# -----------------------------------------------
# General utilities

def viperConfigPath( clusterName, leaf ):
   return os.path.join( clusterName, leaf + ".conf" )

def whistlerConfigPath( clusterName, spine ):
   return os.path.join( clusterName, spine + ".conf" )

# -----------------------------------------------
# Config generation helpers

def tmplInterface( sysport=100, addressList=["3001::1/64"], mtu=9000 ):
   return {
       'intfID': sysport,
       'ipAddresses': addressList,
       'isStateSyncDisabled': True,
       'isVirtual': False,
       'mtu': mtu,
       'routerID': 0,
       'type': 2,
       'vlanID': 0 }

def sysport( leafIndex, offset ):
   return 100 + 200 * leafIndex + offset

def loopbackAddr( leafIndex ):
   return f"3000:{leafIndex}::1/128"

def ethAddrList( leafIndex, intfIdx ):
   return [ f"100:{leafIndex}:{intfIdx}::1/64" ]

def leafSwitchId( leafIndex ):
   return leafIndex * 4

def spineSwitchId( spineIndex ):
   return 512 + spineIndex * 4

def genDsfNodes( leafIdxs, spines ):
   result = {}
   for i, leaf in leafIdxs:
      switchId = leafSwitchId( i )
      result[ f"{switchId}" ] = {
            'asicType': 14,
            'loopbackIps': [ loopbackAddr( i ) ],
            'name': leaf,
            'nodeMac': '02:00:00:00:0F:0B',
            'platformType': 28,
            'switchId': switchId,
            'systemPortRange': {
               'maximum': sysport( i + 1, -1 ),
               'minimum': sysport( i, 0 ) },
            'type': 2 }

   for i, spine in enumerate( spines ):
      switchId = spineSwitchId( i )
      result[ f"{switchId}" ] = {
            "name": spine,
            "switchId": switchId,
            "type": 1,
            "asicType": 16,
            "platformType": 30
            }

   return result

def genSwitchIdToSwitchInfo(
      leafIdxList : List[ Tuple[ int, str ] ],
      spineIdxList : List[ Tuple[ int, str ] ] ):
   switchIdToSwitchInfo = {}

   for i, leaf in leafIdxList:
      switchId = leafSwitchId( i )
      switchIdToSwitchInfo[ f"{switchId}" ] = {
            "switchType": 2,
            "asicType": 14,
            "switchIndex": switchId,
            "portIdRange": {
              "minimum": 0,
              "maximum": 2047
            },
            "systemPortRange": {
              "minimum": sysport( i, 0 ),
              "maximum": sysport( i + 1, -1 )
            },
            "switchMac": "02:00:00:00:0F:0B"
         }

   for i, spine in spineIdxList:
      switchId = spineSwitchId( i )
      switchIdToSwitchInfo[ f"{switchId}" ] = {
            "switchType": 3,
            "asicType": 16,
            "switchIndex": switchId,
            "portIdRange": {
              "minimum": 0,
              "maximum": 2047
            },
            "connectionHandle": "15:00"
         }
      
   return switchIdToSwitchInfo

# -----------------------------------------------
# Config generator entry point

def generateViperConfig( baseViperConfig, leafName, leafIndex,
                         leafs, spines ):
   viperConfig = copy.deepcopy( baseViperConfig )

   viperConfig[ "sw" ][ "interfaces" ] = [
         # Recycle port
         tmplInterface(
            sysport=sysport( leafIndex, 1 ),
            addressList=[] ),# loopbackAddr( leafIndex ) ] ),

#         # Front panel port
#         tmplInterface(
#            sysport=sysport( leafIndex, 6 ),
#            addressList=ethAddrList( leafIndex, 6 ) ),
         ]

   viperConfig[ "sw" ][ "switchSettings" ][ "switchId" ] = leafSwitchId( leafIndex )

   viperConfig[ "sw" ][ "switchSettings" ][ "switchIdToSwitchInfo" ] = \
         genSwitchIdToSwitchInfo(
               [ ( leafIndex, leafName ) ], [] )

   viperConfig[ "sw" ][ "dsfNodes" ] = genDsfNodes(
         enumerate( leafs ), [] ) #spines )

   return viperConfig

def generateWhistlerConfig( baseWhistlerConfig, spineName, spineIndex,
                            leafs, spines ):
   whistlerConfig = copy.deepcopy( baseWhistlerConfig )

   whistlerConfig[ "sw" ][ "switchSettings" ][ "switchId" ] = spineSwitchId( spineIndex )

   whistlerConfig[ "sw" ][ "switchSettings" ][ "switchIdToSwitchInfo" ] = \
         genSwitchIdToSwitchInfo( [], [ ( spineIndex, spines ) ] )

   whistlerConfig[ "sw" ][ "dsfNodes" ] = genDsfNodes(
         enumerate( leafs ), spines )


   return whistlerConfig

# -----------------------------------------------
# Main program

def copyScripts( clusterName, leafs, spines ):
   for dev in leafs:
      configPath = viperConfigPath( clusterName, dev )
      os.system( f"scp -4 {configPath} root@{dev}:/tmp" )

   for dev in spines:
      configPath = whistlerConfigPath( clusterName, dev )
      os.system( f"scp -4 {configPath} root@{dev}:/tmp" )

def main( args ):
   # Generate viper config
   with open( "viper_cluster.conf" ) as f:
      baseViperConfig = json.loads( f.read() )

   os.system( f"mkdir {args.cluster_name}" )

   leafs = sorted( args.leaf )
   spines = sorted( args.spine )

   for idx, leaf in enumerate( leafs ):
      viperConfig = generateViperConfig( baseViperConfig, leaf, idx, leafs, spines )
      configPath = viperConfigPath( args.cluster_name, leaf )
      with open( configPath, "w" ) as f:
         json.dump( viperConfig, f, indent=2, separators=( ", ", ": " ) )

   # Generate whistler config
   with open( "whistler_cluster.conf" ) as f:
      baseWhistlerConfig = json.loads( f.read() )

   spines = sorted( args.spine )
   for idx, spine in enumerate( spines ):
      spineConfig = generateWhistlerConfig( baseWhistlerConfig, spine, idx, leafs, spines )
      configPath = whistlerConfigPath( args.cluster_name, spine )
      with open( configPath, "w" ) as f:
         json.dump( spineConfig, f, indent=2, separators=( ", ", ": " ) )

   if args.copy:
      copyScripts( args.cluster_name, leafs, spines )

def parsedArgs():
   parser = argparse.ArgumentParser()
   parser.add_argument( "cluster_name" )
   parser.add_argument( "-s", "--spine", metavar="SPINE_DUT_NAME",
         nargs="+", default=[] )
   parser.add_argument( "-l", "--leaf", metavar="LEAF_DUT_NAME",
         nargs="+", required=True )
   parser.add_argument( "--copy", action="store_true",
         help="Copy generated configs to dut" )

   args = parser.parse_args()
   if not args.leaf:
      parser.error( "Must name some leaf devices" )

   return args

if __name__ == "__main__":
   main( parsedArgs() )
