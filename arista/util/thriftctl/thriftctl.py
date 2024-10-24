#!/usr/bin/env python3

import argparse
import ast
import importlib
import sys

sys.path.append( "/opt/fboss/lib/fb-py-libs" )
sys.path.append( "/opt/fboss/lib/fb-py-libs/gen-py" )

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol

tool_description = '''This tool can be used to fetch data on a device from thrift

Example:
python3 thriftctl.py request getTransceiverInfo --port 5910'''


# NOTE: Not comprehensive and may diverge depending on upstream changes
SERVICE_MAPPING = {
   # 5908: TODO: fsdb,
   5909: 'neteng.fboss.ctrl.FbossCtrl',
   5910: 'neteng.fboss.qsfp.QsfpService', # Meta plans to migrate this to 5960
   # 5930: TODO: ledService,
   5931: 'neteng.fboss.hw_ctrl.FbossHwCtrl',
   5932: 'neteng.fboss.hw_ctrl.FbossHwCtrl',
   # 5959: TODO: SwSwitch,
   5970: 'neteng.fboss.platform.sensor_service.SensorServiceThrift',
   # 5971: TODO: datacorral,
   5972: 'fan_service.FanService',
   5973: 'rackmonsvc.rackmonsvc.RackmonCtrl',
   # 5975: TODO: platform_manager,
   # 6909: TODO: bgpThriftPort, 
}

class FbossThriftctl:
   def __init__( self, port, host='localhost' ):
      self.host = host
      self.port = port

   def getClient( self, protocol, port ):
      service_path = SERVICE_MAPPING.get( port )
      if service_path:
         module_path, client_class = service_path.rsplit( '.', 1 )         
         service_module = importlib.import_module( service_path )
         return service_module.Client( protocol )
      else:
         print( f"No known path for port {port}" )
         return None, None

   def listMethods( self ):
      unfiltered_methods = dir( self.client )
      # ignore send_ recv_ methods, the full method wraps both
      methods = [ m for m in unfiltered_methods if "_" not in m ]
      print( f'Found {len( methods )} available methods under port:{self.port}' )
      for m in methods:
         print( f'\t{m}' )

   def connect( self ):
      try:
         self.transport = TSocket.TSocket( self.host, self.port )
         self.transport = TTransport.TBufferedTransport( self.transport )
         protocol = TBinaryProtocol.TBinaryProtocol( self.transport )

         self.client = self.getClient( protocol, self.port )

         self.transport.open()
      except Exception as e:
         print( f"Error connecting: {str(e)}" )

   def close(self):
      if self.transport:
         self.transport.close()

def list_ports():
   for port, path in SERVICE_MAPPING.items():
      print( f'{port}: {path}' )

def call_method( client, method_name, *args, **kwargs ):
   try:
      func = getattr( client, method_name )

      if callable( func ):
         return func( *args, **kwargs )
      else:
         print( f"{method_name} is not a callable method." )
         return None
   except AttributeError:
      print( f"Method '{method_name}' not found in the object." )
      return None

def process_arg( arg ):
   try:
      return ast.literal_eval( arg )
   except ( ValueError, SyntaxError ):
      return arg

def parseArgs( argv ):
   parser = argparse.ArgumentParser( prog='thriftctl', description=tool_description )

   subparsers = parser.add_subparsers( dest='operation', required=True,
                                        help='Available subcommands' )

   request = subparsers.add_parser( 'request', help='Install a package' )
   request.add_argument( 'method', help='The name of the method to call' )
   request.add_argument( 'args', nargs='*', default=None,
                          help='arguments to pass into the method' )
   request.add_argument( '-p', '--port', required=True, type=int,
                          help='Port on which the thrift endpoint is on' )
   request.add_argument( '--host', default='localhost', required=False )

   listports = subparsers.add_parser( 'listPorts', help='list ports' )

   listmethods = subparsers.add_parser( 'listMethods', help='list methods' )
   listmethods.add_argument( '-p', '--port', required=True, type=int,
                          help='Port on which the thrift endpoint is on' )
   listmethods.add_argument( '--host', default='localhost', required=False )

   return parser.parse_args( argv )

def main( argv ):
   args = parseArgs( argv )

   if args.operation == 'listPorts':
      list_ports()
   elif args.operation == 'request' or args.operation == 'listMethods':
      thirftctl = FbossThriftctl( host=args.host, port=args.port )

      thirftctl.connect()

      if args.operation == 'request':   
         processed_args = [ process_arg( arg ) for arg in args.args ]
         result = call_method( thirftctl.client, args.method, *processed_args )
         print(result)
      elif args.operation == 'listMethods':
         result = thirftctl.listMethods()

      thirftctl.close()

if __name__ == '__main__':
   sys.exit( main( sys.argv[ 1 : ] ) )
