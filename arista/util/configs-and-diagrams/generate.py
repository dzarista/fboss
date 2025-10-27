#!/usrb/bin/env python3
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
import os
import importlib
import inspect

from GenerateConfigsAndDiagrams.BaseConfigs import PlatformConfig

# Avoid generating certain configs on certain platforms.
# This is useful for platforms that share the configs.
EXCLUDE_LIST = {
   "pm-config": [
   ],
   "sensor-config": [
      "Banff"
   ],
   "bsp-mapping": [
      "RackhawkORv3",
      "Banff"
   ],
   "fan-config": [
      "Rackhawk",
      "RackhawkORv3",
      "Banff"
   ],
   "led-config": [
      "Rackhawk",
      "RackhawkORv3",
      "Banff"
   ]
}


def genPmConfig( platform, aristaCodename, metaCodename, output ):
   if aristaCodename not in EXCLUDE_LIST.get( 'pm-config', [] ):
      with open(
         f'../../../fboss/platform/configs/{ metaCodename }/platform_manager.json', 'w'
      ) as file:
         file.write( getattr( platform, output[ 'pm-config' ] )() )
         file.write( '\n' )


def genSensorConfig( platform, aristaCodename, metaCodename, output ):
   if aristaCodename not in EXCLUDE_LIST.get( 'sensor-config', [] ):
      with open(
         f'../../../fboss/platform/configs/{ metaCodename }/sensor_service.json', 'w'
      ) as file:
         file.write( getattr( platform, output[ 'sensor-config' ] )() )
         file.write( '\n' )


def genBspMapping( platform, aristaCodename, metaCodename, output ):
   if aristaCodename not in EXCLUDE_LIST.get( 'bsp-mapping', [] ):
      with open(
         f'../../../fboss/lib/bsp/bspmapping/input/{ metaCodename }_BspMapping.csv', 'w',
      ) as file:
         file.write( getattr( platform, output[ 'bsp-mapping' ] )() )

def genLedConfig( platform, aristaCodename, metaCodename, output ):
   if aristaCodename not in EXCLUDE_LIST.get( 'led-config', [] ):
      with open(
         f'../../../fboss/platform/configs/{ metaCodename }/led_manager.json', 'w'
      ) as file:
         file.write( getattr( platform, output[ 'led-config' ] )() )
         file.write( '\n' )

def genFanConfig( platform, aristaCodename, metaCodename, output ):
   if aristaCodename not in EXCLUDE_LIST.get( 'fan-config', [] ):
      with open(
         f'../../../fboss/platform/configs/{ metaCodename }/fan_service.json', 'w'
      ) as file:
         file.write( getattr( platform, output[ 'fan-config' ] )() )
         file.write( '\n' )

def get_platforms():
   '''Returns all platforms from GenerateConfigsAndDiagrams/Platforms'''
   platforms = {}
   this_dir = os.path.dirname( __file__ )
   platforms_dir = os.path.join( this_dir, 'GenerateConfigsAndDiagrams/Platforms' )
   for filename in os.listdir( platforms_dir ):
      if ( filename.endswith( '.py' ) and not filename.startswith( '__' ) 
           and filename != 'sample.py' and filename != 'BaseConfigs.py' ):
         module_name = f"GenerateConfigsAndDiagrams.Platforms.{filename[ :-3 ]}"
         module = importlib.import_module( module_name )
         for name, obj in inspect.getmembers( module ):
            if ( inspect.isclass( obj ) and issubclass( obj, PlatformConfig )
                 and obj is not PlatformConfig ):
               platforms[ name ] = obj
   return platforms

def main():
   platforms = get_platforms()

   output = {
      'pm-config': 'pmConfigJson',
      'sensor-config': 'sensorServiceJson',
      'pm-diagram': 'genDiagram',
      'bsp-mapping': 'bspMappingCsv',
      'fan-config': 'fanJson',
      'led-config': 'ledJson'
   }

   parser = argparse.ArgumentParser(
      description=( 'In order to use this script correctly, please either specify '
                    '--update_all_configs OR specify a choice of platform using '
                    '--platform AND a choice of output using --output.' )
   )
   parser.add_argument( '--update_all_configs', action='store_true',
                        help='Update configs for all defined platforms' )
   parser.add_argument( '--platform', choices=platforms.keys(),
                        help='Platform name' )
   parser.add_argument( '--output',
                        choices=[ 'pm-config', 'sensor-config', 'pm-diagram',
                                  'bsp-mapping', 'fan-config', 'led-config',
                                  'vendor-mappings' ],

                        help='Config/diagram to generate' )

   args = parser.parse_args()

   if args.update_all_configs and not args.platform and not args.output:
      for p in platforms:
         aristaCodename = p
         platform = platforms[ p ]()
         metaCodename = platform.platformName.lower()
         # Special case for Banff/Thrasher because there's no Aboot18 support for
         # overriding the dmidecode output.
         if metaCodename == 'redstart-rmb':
            metaCodename = 'glath06a-64o'

         genPmConfig( platform, aristaCodename, metaCodename, output )
         genSensorConfig( platform, aristaCodename, metaCodename, output )
         genBspMapping( platform, aristaCodename, metaCodename.capitalize(), output )
         genLedConfig( platform, aristaCodename, metaCodename, output )
         genFanConfig( platform, aristaCodename, metaCodename, output )
   elif args.platform and args.output and not args.update_all_configs:
      platform = platforms[ args.platform ]()
      if args.output == 'vendor-mappings':
          assert hasattr( platform, 'l1' ), f"L1Configs not defined on {args.platform}"
          l1_configs = platform.l1
          result = l1_configs.gen_vendor_mapping()
      elif args.output in [ 'pm-config', 'sensor-config', 'bsp-mapping',
                            'fan-config', 'led-config']:
         result = getattr( platform, output[ args.output ] )()
         print( result )
   else:
      parser.error( parser.description )


if __name__ == '__main__':
   main()
