from GenerateConfigsAndDiagrams.Platforms.Viper import Viper
from GenerateConfigsAndDiagrams.Platforms.Whistler import Whistler
import argparse

def main():
   parser = argparse.ArgumentParser()
   parser.add_argument( 'platform', choices=[ 'Viper', 'Whistler' ],
                        help='Platform name' )
   parser.add_argument( 'output',
                        choices=[ 'pm-config', 'sensor-config', 'pm-diagram' ],
                        help='Config/diagram to generate' )

   args = parser.parse_args()

   platforms = {
      'Viper': Viper,
      'Whistler': Whistler
   }

   output = {
      'pm-config': 'pmConfigJson',
      'sensor-config': 'sensorServiceJson',
      'pm-diagram': 'genDiagram'
   }

   platform = platforms[ args.platform ]()
   result = getattr( platform, output[ args.output ] )()

   if args.output in [ 'pm-config', 'sensor-config' ]:
      print( result )

if __name__ == '__main__':
   main()


