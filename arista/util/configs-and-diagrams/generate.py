#!/usrb/bin/env python3

import argparse

from GenerateConfigsAndDiagrams.Platforms.QuicksilverPFb import QuicksilverPFb
from GenerateConfigsAndDiagrams.Platforms.Rackhawk import RackhawkORv3, Rackhawk
from GenerateConfigsAndDiagrams.Platforms.Viper import Viper
from GenerateConfigsAndDiagrams.Platforms.Whistler import Whistler

# Avoid generating certain configs on certain platforms.
# This is useful for platforms that share the configs.
EXCLUDE_LIST = {
   'pm-config': [],
   'sensor-config': [],
   'bsp-mapping': [ 'RackhawkORv3' ],
   'fan-config': [ 'Whistler', 'QuickSilverPFb', 'RackhawkORv3' ],
   'led-config': [ 'Rackhawk', 'RackhawkORv3' ],
   'weutil-config': [ 'Rackhawk', 'RackhawkORv3' ],
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
        
def genWeutilConfig( platform, aristaCodename, metaCodename, output ):
   if aristaCodename not in EXCLUDE_LIST.get( 'weutil-config', [] ):
      with open(
         f'../../../fboss/platform/configs/{ metaCodename }/weutil.json', 'w'
      ) as file:
         file.write( getattr( platform, output[ 'weutil-config' ] )() )
         file.write( '\n' )

def main():
   platforms = {
      'QuicksilverPFb': QuicksilverPFb,
      'Rackhawk': Rackhawk,
      'RackhawkORv3': RackhawkORv3,
      'Viper': Viper,
      'Whistler': Whistler
   }

   output = {
      'pm-config': 'pmConfigJson',
      'sensor-config': 'sensorServiceJson',
      'pm-diagram': 'genDiagram',
      'bsp-mapping': 'bspMappingCsv',
      'fan-config': 'fanJson',
      'led-config': 'ledJson',
      'weutil-config': 'weutilJson',
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
                                  'bsp-mapping', 'fan-config', 'led-config', 'weutil-config' ],

                        help='Config/diagram to generate' )
   args = parser.parse_args()

   if args.update_all_configs and not args.platform and not args.output:
      for p in platforms:
         aristaCodename = p
         platform = platforms[ p ]()
         metaCodename = platform.platformName.lower()

         genPmConfig( platform, aristaCodename, metaCodename, output )
         genSensorConfig( platform, aristaCodename, metaCodename, output )
         genBspMapping( platform, aristaCodename, metaCodename.capitalize(), output )
   elif args.platform and args.output and not args.update_all_configs:
      platform = platforms[ args.platform ]()
      result = getattr( platform, output[ args.output ] )()
      if args.output in [ 'pm-config', 'sensor-config', 'bsp-mapping', 'fan-config', 'led-config', 'weutil-config' ]:
         print( result )
   else:
      parser.error( parser.description )


if __name__ == '__main__':
   main()
