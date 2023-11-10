#!/usr/bin/env python3
# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from typing import List, Tuple

import argparse
import copy
import json
import os
import re
import subprocess

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
            "switchIndex": 0,
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
            "switchIndex": 0,
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
                         leafs, spines, artInfo ):
   viperConfig = copy.deepcopy( baseViperConfig )

   viperConfig[ "sw" ][ "interfaces" ] = [
         # Recycle port
         tmplInterface(
            sysport=sysport( leafIndex, 1 ),
            addressList=[ loopbackAddr( leafIndex ) ] ),

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

   if artInfo:
      nonSnakeFabricIntfs = [ intf for intf in artInfo[ "interfaces" ] if not intf[ "snake" ] and intf[ "localIntf" ].startswith( "Fabric" ) ]
      nonSnakeFabricIntfFbossNames = {
            "fab1/" + intf[ "localIntf" ].lstrip( "Fabric" )
            for intf in nonSnakeFabricIntfs }

      newPorts = []
      for port in viperConfig[ "sw" ][ "ports" ]:
         portName = port[ "name" ]

         if portName.startswith( "rcy" ) or portName.startswith( "eth" ):
            print( f"{leafName} kept {portName}" )
            newPorts.append( port )
            continue

         elif portName.startswith( "fab" ):
            if portName in nonSnakeFabricIntfFbossNames:
               print( f"{leafName} kept {portName}" )
               newPorts.append( port )
            else:
               print( f"{leafName} skipped {portName}" )
            continue

         import pdb; pdb.set_trace()
         assert False, "Unhandled port type"

      viperConfig[ "sw" ][ "ports" ] = newPorts

   return viperConfig

def generateWhistlerConfig( baseWhistlerConfig, spineName, spineIndex,
                            leafs, spines, artInfo ):
   whistlerConfig = copy.deepcopy( baseWhistlerConfig )

   whistlerConfig[ "sw" ][ "switchSettings" ][ "switchId" ] = spineSwitchId( spineIndex )

   whistlerConfig[ "sw" ][ "switchSettings" ][ "switchIdToSwitchInfo" ] = \
         genSwitchIdToSwitchInfo( [], [ ( spineIndex, spines ) ] )

   whistlerConfig[ "sw" ][ "dsfNodes" ] = genDsfNodes(
         enumerate( leafs ), spines )

   if artInfo:
      nonSnakeFabricIntfs = [ intf for intf in artInfo[ "interfaces" ] if not intf[ "snake" ] and intf[ "localIntf" ].startswith( "Fabric" ) ]
      nonSnakeFabricIntfFbossNames = {
            "fab1/" + intf[ "localIntf" ].lstrip( "Fabric" )
            for intf in nonSnakeFabricIntfs }

      newPorts = []
      for port in whistlerConfig[ "sw" ][ "ports" ]:
         portName = port[ "name" ]

         if portName.startswith( "rcy" ) or portName.startswith( "eth" ):
            print( f"{spineName} kept {portName}" )
            newPorts.append( port )
            continue

         elif portName.startswith( "fab" ):
            if portName in nonSnakeFabricIntfFbossNames:
               print( f"{spineName} kept {portName}" )
               newPorts.append( port )
            else:
               print( f"{spineName} skipped {portName}" )
            continue

         import pdb; pdb.set_trace()
         assert False, "Unhandled port type"

      whistlerConfig[ "sw" ][ "ports" ] = newPorts

   return whistlerConfig

# -----------------------------------------------
# Art info handling

class ArtInfoParser:
   """
   Parses the output of "Art info --detail <devicename>" and extracts
   a few pieces of relevant information. Specifically:
   - device name
   - interface (with its properties)
   """
   dutspecRe = re.compile( "dutspec\s+(?P<devName>\S+)" )
   interfacesBlockRe = re.compile(
         "interfaces:\s+(?P<count>\d+)"
         "(?P<data>.*?)"
         "child testbeds:", re.DOTALL )

   # Sample output
   #  interfaces:             448
   #     Fabric1/1            <snake> Fabric2/1 (fabric)
   #     Fabric41/1           vpr107 Fabric1/1 (fabric) (disabled)
   #     Ethernet13/1         svp614 eth7/1 (400G-8)
   #  child testbeds:
   interfaceLineRe = re.compile(
         "(?P<localIntf>\S+)\s+"
         "(?P<snake>.snake.)?\s*"
         "(?P<remoteDev>[a-z]{2,6}[0-9]{1,4})?\s*"
         "(?P<remoteIntf>([A-Z][a-z\/0-9]+)|(eth[0-9\/]+))\s*"
         "(?P<comment>\([^\)]*\))?"
         "(?P<disabled>.disabled.)?" )

   @staticmethod
   def parse( text : str ):
      devName = None
      details = { "interfaces": [] }

      match = ArtInfoParser.dutspecRe.search( text )
      devName = match.group( "devName" )

      match = ArtInfoParser.interfacesBlockRe.search( text )
      interfacesText = match.group( "data" )

      for line in interfacesText.split( "\n" ):
         if not line.strip():
            continue
         match = ArtInfoParser.interfaceLineRe.search( line )
         try:
            details[ "interfaces" ].append( match.groupdict() ) 
         except:
            print( f"Failed to match: {line}" )
            import pdb; pdb.set_trace()
            pass

      return ( devName, details )

def getArtInfo( devices ):
   """
   Get a in iterable of devices to get art-info for

   The method invokes a single "Art info" in the latest eos-trunk
   abuild workspace and extracts dut information from the output.
   """
   cmd = [ "ap", "abuild", "-p", "eos-trunk", "-S",
         "--command", "Art info --detail " + " ".join( devices ),
         "pass" ]
   output = subprocess.check_output( cmd )
   output = output.decode( "ascii", "replace" )

   devBlockRe = "RdamDut details:(.*?)\r\n\r\n"

   result = {}
   for match in re.finditer( devBlockRe, output, flags=re.DOTALL ):
      # Find each devices information
      devName, details = ArtInfoParser.parse( match.group( 0 ) )
      result[ devName ] = details 

   return result

# -----------------------------------------------
# Main program

def copyScripts( clusterName, leafs, spines ):
   for dev in leafs:
      configPath = viperConfigPath( clusterName, dev )
      os.system( f"scp -4 {configPath} root@{dev}:/tmp/sbirmiwal" )

   for dev in spines:
      configPath = whistlerConfigPath( clusterName, dev )
      os.system( f"scp -4 {configPath} root@{dev}:/tmp/sbirmiwal" )

def main( args ):
   # Generate viper config
   with open( "viper_cluster.conf" ) as f:
      baseViperConfig = json.loads( f.read() )

   os.system( f"mkdir {args.cluster_name}" )

   leafs = sorted( args.leaf )
   spines = sorted( args.spine )

   artInfo = {}
   if not args.no_filter_ports:
      artInfo = getArtInfo( spines + leafs )

   for idx, leaf in enumerate( leafs ):
      viperConfig = generateViperConfig( baseViperConfig, leaf, idx, leafs, spines, artInfo.get( leaf ) )
      configPath = viperConfigPath( args.cluster_name, leaf)
      with open( configPath, "w" ) as f:
         json.dump( viperConfig, f, indent=2, separators=( ", ", ": " ) )

   # Generate whistler config
   with open( "whistler_cluster.conf" ) as f:
      baseWhistlerConfig = json.loads( f.read() )

   spines = sorted( args.spine )
   for idx, spine in enumerate( spines ):
      spineConfig = generateWhistlerConfig( baseWhistlerConfig, spine, idx, leafs, spines, artInfo.get( spine ) )
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
   parser.add_argument( "--no-filter-ports", action="store_true",
         default=False,
         help="Filter fabric ports based on Art info --detail information" )
   parser.add_argument( "--copy", action="store_true",
         help="Copy generated configs to dut" )

   args = parser.parse_args()
   if not args.leaf:
      parser.error( "Must name some leaf devices" )

   return args

if __name__ == "__main__":
   main( parsedArgs() )
