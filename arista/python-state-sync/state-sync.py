#!/usr/bin/env python3

import argparse
import datetime
import itertools
import json
import sys

sys.path.append( "gen-py" )

from thrift.transport import (
      TSocket,
      TTransport,
      )
from thrift.protocol import THeaderProtocol
from neteng.fboss.ctrl import FbossCtrl

# -----------------------------------------------
# General helpers

class Trace:
   disabled = 0
   error = 1
   info = 2
   debug = 3

   choices = ( "disabled", "error", "info", "debug" )
   desired = "info"

   @staticmethod
   def strep( lvl ):
      return {
         Trace.info: "INF",
         Trace.error: "ERR",
         Trace.debug: "DBG",
      }[ lvl ]

def trace( level, *msg ):
   if level > Trace.desired:
      return
   now = datetime.datetime.now()
   sys.stderr.write( " ".join(
      map( str,
           itertools.chain(
              ( datetime.datetime.now(), Trace.strep( level ) ),
              msg ) ) ) + "\n" )

# -----------------------------------------------
# Thrift helpers

def getClient( addr, port=5909 ):
   transport = TSocket.TSocket( addr, 5909 )
   transport = TTransport.TBufferedTransport( transport )
   protocol = THeaderProtocol.THeaderProtocol( transport )

   client = FbossCtrl.Client( protocol )
   transport.open()
   trace( Trace.info, f"connected to {addr}:{port}" )
   return client

def getPortAndHostData( client ):
   pathToState = client.getCurrentStateJSONForPaths( { "systemPortMaps", "interfaceMaps" } )
   trace( Trace.info, "fetched state successfully" )
   trace( Trace.debug, pathToState )
   return pathToState

def remapMergePortAndHostData( pathToState, resultPathToState ):
   # Temporarily left in. We have to merge data from multiple neighbors
   # but the data return from get is not a dictionary but a string reprepresantion
   # of dictionaries. When we the ability to test against multiple remote leaf
   # devices, we'll have to revisit this.
   #resultPathToState[ "remoteSystemPortMaps" ].update(
   #      json.loads( pathToState.pop( "systemPortMaps" ) ) )
   #resultPathToState[ "remoteInterfaceMaps" ].update(
   #      json.loads( pathToState.pop( "interfaceMaps" ) ) )
   resultPathToState[ "remoteSystemPortMaps" ] = pathToState.pop( "systemPortMaps" )
   resultPathToState[ "remoteInterfaceMaps" ] = pathToState.pop( "interfaceMaps" )

def setState( client, pathToState ):
   client.patchCurrentStateJSONForPaths( pathToState )
   trace( Trace.info, "Set state completed" )

# -----------------------------------------------
# main

def main( args ):

   pathToState = {
      "remoteSystemPortMaps": {},
      "remoteInterfaceMaps": {},
   }

   if args.load:
      with open( args.load ) as f:
         content = f.read()

      pathToState = eval( content )

   else:
      for remote in args.get:
         client = getClient( remote )
         remapMergePortAndHostData( getPortAndHostData( client ), pathToState )

   trace( Trace.debug, "remapped data", pathToState )

   if args.set:
      client = getClient( "127.0.0.1" )
      setState( client, pathToState )
   else:
      trace( Trace.info, "No action taken" )

def parseArgs():
   parser = argparse.ArgumentParser()
   parser.add_argument( "--get", action="append",
         metavar="REMOTE_LEAF",
         help="Hostname/IP address of remote leaf to retrieve "
            "state from",
         default=[] )
   parser.add_argument( "--load",
         metavar="LOAD_FILE",
         help="Instead of getting data from remote hosts, "
            "load it from local file" )
   parser.add_argument( "--set", action="store_true",
         help="Set state locally instead of just displaying it" )
   choices=( "disabled", "error", "info", "debug" ),
   parser.add_argument( "--trace", choices=Trace.choices,
         help=f"Choose tracing level. default={Trace.desired}",
         default=Trace.desired )

   args = parser.parse_args()
   if args.get and args.load:
      parser.error( "Can't use --get and --load at the same time" )

   if not args.get and not args.load:
      parser.error( "Must specify --get or --load" )

   Trace.desired = getattr( Trace, args.trace )
   return args

if __name__ == "__main__":
   main( parseArgs() )
