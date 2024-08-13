#!/usrb/bin/env python3

import argparse

from GenerateConfigsAndDiagrams.Platforms.Rackhawk import Rackhawk, RackhawkORv3
from GenerateConfigsAndDiagrams.Platforms.Viper import Viper
from GenerateConfigsAndDiagrams.Platforms.Whistler import Whistler

def main():
   platforms = {
      'Rackhawk': Rackhawk,
      'RackhawkORv3': RackhawkORv3,
      'Viper': Viper,
      'Whistler': Whistler
   }

   output = {
      'pm-config': 'pmConfigJson',
      'sensor-config': 'sensorServiceJson',
      'pm-diagram': 'genDiagram'
   }

   parser = argparse.ArgumentParser()
   parser.add_argument( 'platform', choices=platforms.keys(),
                        help='Platform name' )
   parser.add_argument( 'output',
                        choices=[ 'pm-config', 'sensor-config', 'pm-diagram' ],
                        help='Config/diagram to generate' )
   args = parser.parse_args()

   platform = platforms[ args.platform ]()
   result = getattr( platform, output[ args.output ] )()

   if args.output in [ 'pm-config', 'sensor-config' ]:
      print( result )

if __name__ == '__main__':
   main()


