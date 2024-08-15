#!/usrb/bin/env python3

import argparse

from GenerateConfigsAndDiagrams.Platforms.Viper import Viper
from GenerateConfigsAndDiagrams.Platforms.Whistler import Whistler


def main():
   platforms = {
      'Viper': Viper,
      'Whistler': Whistler
   }

   output = {
      'pm-config': 'pmConfigJson',
      'sensor-config': 'sensorServiceJson',
      'pm-diagram': 'genDiagram'
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
                        choices=[ 'pm-config', 'sensor-config', 'pm-diagram' ],
                        help='Config/diagram to generate' )
   args = parser.parse_args()

   if args.update_all_configs and not args.platform and not args.output:
      for p in platforms:
         platform = platforms[ p ]()
         name = platform.platformName.lower()
         with open(
            f'../../../fboss/platform/configs/{ name }/platform_manager.json', 'w'
         ) as file:
            file.write( getattr( platform, output[ 'pm-config' ] )() )
            file.write( '\n' )
         with open(
            f'../../../fboss/platform/configs/{ name }/sensor_service.json', 'w'
         ) as file:
            file.write( getattr( platform, output[ 'sensor-config' ] )() )
            file.write( '\n' )
   elif args.platform and args.output and not args.update_all_configs:
      platform = platforms[ args.platform ]()
      result = getattr( platform, output[ args.output ] )()
      if args.output in [ 'pm-config', 'sensor-config' ]:
         print( result )
   else:
      parser.error( parser.description )


if __name__ == '__main__':
   main()


