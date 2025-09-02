#!/usr/bin/env python3

import argparse
import ast
import importlib
import json
import sys

sys.path.append( "/opt/fboss/lib/fb-py-libs" )
sys.path.append( "/opt/fboss/lib/fb-py-libs/gen-py" )

from thrift.protocol import TBinaryProtocol, TJSONProtocol
from thrift.transport import TSocket, TTransport

tool_description = '''This tool can be used to fetch data on a device from thrift

Example:
thriftctl request getTransceiverInfo -p 5910'''


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

def thrift_to_dict( obj ):
   if isinstance( obj, list ):
      return [ thrift_to_dict( item ) for item in obj ]
   elif isinstance( obj, dict ):
      return { key: thrift_to_dict( value ) for key, value in obj.items() }
   elif hasattr( obj, "__dict__" ):
      return { key: thrift_to_dict( value ) for key, value in obj.__dict__.items() }
   else:
      return obj

class FbossThriftctl:
   def __init__( self, port, host='localhost' ):
      self.host = host
      self.port = port
      self.transport = None

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

   def close( self ):
      if self.transport:
         self.transport.close()

   def parseResponseJson( self, response ):
      json_data = thrift_to_dict( response )
      return json.dumps( json_data, indent=2 )

def list_ports():
   for port, path in SERVICE_MAPPING.items():
      print( f'{port}: {path}' )

def resolve_args( client, arg ):
   '''Dynamically resolve and create Thrift struct objects.
   e.g. {"struct": "PwmHoldRequest", "pwm": 70}
   e.g. {'path': 'neteng.fboss.phy.ttypes',
         'struct':'PortPrbsState',
         'enabled' : True}'''
   try:
      # Intrepret arg using the struct key
      if isinstance( arg, dict ) and "struct" in arg:
         struct_name = arg.pop( "struct" )
         module_name = client.__class__.__module__
         path_name = arg.pop( "path", module_name )

         thrift_module = __import__( path_name, fromlist=[ struct_name ] )
         struct_class = getattr( thrift_module, struct_name, None )

         if struct_class:
            return struct_class( **arg )
         else:
            raise ValueError( f'Struct "{struct_name}" not in "{path_name}"' )

      return arg
   except Exception as e:
      print( f"Error resolving struct for argument '{arg}': {e}" )
      return arg 

def call_method( client, method_name, *args, **kwargs ):
   try:
      func = getattr( client, method_name )

      if callable( func ):
         # arguments may be complex structs and need to be parsed
         parsed_args = [ resolve_args( client, arg ) for arg in args ]
         parsed_kwargs = { k: resolve_args( client, v ) for k, v in kwargs.items() }

         return func( *parsed_args, **parsed_kwargs )
      else:
         print( f"{method_name} is not a callable method." )
         return None
   except AttributeError as e:
      print( f"Method '{method_name}' not found in the object. Error: {e}" )
      return None
   except Exception as e:
      print( f"An error occurred: {e}" )
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
                          help='Arguments to pass into the method. Pass each '
                          'arguments as a seperate string. '
                          'E.g. \'["CPU_CORE2_TEMP", "CPU_CORE3_TEMP"]\' '
                          'E.g. \'{"struct": "PwmHoldRequest", "pwm": 70}\'' )
   request.add_argument( '-p', '--port', required=True, type=int,
                          help='Port on which the thrift endpoint is on' )
   request.add_argument( '--host', default='localhost', required=False )
   request.add_argument( '--json', action='store_true', default=False,
                          required=False )

   subparsers.add_parser( 'listPorts', help='list ports' )

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
         if args.json:
            result = thirftctl.parseResponseJson( result )
         print(result)
      elif args.operation == 'listMethods':
         result = thirftctl.listMethods()

      thirftctl.close()

if __name__ == '__main__':
   sys.exit( main( sys.argv[ 1 : ] ) )
