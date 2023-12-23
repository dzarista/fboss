# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
from enum import Enum

PortMedium = Enum( 'PortMedium', 'OPTICAL COPPER' )
SpeedGbps = Enum( 'SpeedGbps',
      'TwentyFive Fifty FiftyThree Hundred HundredAndSix FourHundred' )

def speedInMbps( speed: SpeedGbps ) -> int:
   if speed == SpeedGbps.TwentyFive:
      return 25000
   elif speed == SpeedGbps.Fifty:
      return 50000
   elif speed == SpeedGbps.FiftyThree:
      return 53125
   elif speed == SpeedGbps.Hundred:
      return 100000
   elif speed == SpeedGbps.HundredAndSix:
      return 106250
   elif speed == SpeedGbps.FourHundred:
      return 400000
   else:
      assert False, f"Invalid speed {speed}"


def validNifSerdesSpeeds() -> tuple[SpeedGbps]:
   return ( SpeedGbps.Hundred, SpeedGbps.Fifty, SpeedGbps.TwentyFive )

def validFabricSerdesSpeeds() -> tuple[SpeedGbps]:
   return ( SpeedGbps.FiftyThree, SpeedGbps.HundredAndSix )

def validMediaForSpeed( speed: SpeedGbps ) -> tuple[PortMedium]:
   if speed in ( SpeedGbps.Hundred, SpeedGbps.TwentyFive, SpeedGbps.HundredAndSix ):
      return PortMedium.__members__.values()
   elif speed == SpeedGbps.Fifty:
      return ( PortMedium.COPPER, )
   elif speed == SpeedGbps.FiftyThree:
      return tuple()
   else:
      assert False, f"Invalid speed {speed}"
