# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
from enum import Enum
from dataclasses import dataclass

PortMedium = Enum( 'PortMedium', 'OPTICAL COPPER' )
SpeedGbps = Enum( 'SpeedGbps',
      'TwentyFive Fifty FiftyThree Hundred HundredAndSix FourHundred EightHundred' )

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
   elif speed == SpeedGbps.EightHundred:
      return 800000
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

@dataclass
class TxTapSettings:
   pre3: int = 0
   pre2: int = 0
   pre1: int = 0
   main: int = 0
   post1: int = 0
   post2: int = 0
   post3: int = 0

def __txTapSettingsByTraceLength( traceLength: float ) -> TxTapSettings:
   # Tx TAP Main setting by trace length (inches), this is interpreted as (x, y, mainTap)
   # tap = mainTap if x <= traceLength < y
   # NOTE : the assumption is that 0 < traceLength <= 100
   lengthBucketsToMainTap = ( ( 0, 4, 100 ),
                              ( 4, 8, 116 ),
                              ( 8, 11, 136 ),
                              ( 11, 16, 152 ),
                              ( 16, 100, 168 ) )
   for ( min, max, tap ) in lengthBucketsToMainTap:
      if min <= traceLength < max:
         return TxTapSettings(0, 0, 0, tap, 0, 0, 0 )
   assert False, f"No valid tx TAP settings bucket found for traceLength {traceLength}"

def txTapSettingsByLaneProps( serdesSpeed : SpeedGbps, medium : PortMedium,
                                traceLength : float = None ) -> TxTapSettings:
   if serdesSpeed == SpeedGbps.Hundred:
      if medium == PortMedium.OPTICAL:
         return TxTapSettings( None, 4, -16, 96, 0, 0, 0 )
      elif medium == PortMedium.COPPER:
         return TxTapSettings( -4, 14, -36, 112, 0, 0, 0 )
      else:
         assert False, f"Invalid medium {medium} for speed {serdesSpeed}"
   elif serdesSpeed == SpeedGbps.Fifty:
      if medium == PortMedium.COPPER:
         return TxTapSettings( 0, 4, -24, 130, -12, 0, 0 )
      else:
         assert False, f"Invalid medium {medium} for speed {serdesSpeed}"
   elif serdesSpeed == SpeedGbps.TwentyFive:
      if medium in ( PortMedium.OPTICAL, PortMedium.COPPER ):
         return TxTapSettings( None, None, 3, 31, 13, None, None )
      else:
         assert False, f"Invalid medium {medium} for speed {serdesSpeed}"
   elif serdesSpeed == SpeedGbps.HundredAndSix:
      if medium == PortMedium.COPPER:
         assert traceLength is not None, f"valid traceLength required for"\
         f" {medium}@{serdesSpeed}"
         return __txTapSettingsByTraceLength( traceLength )
      elif medium == PortMedium.OPTICAL:
         # Only valid for Viper, Whistler uses settings from a file.
         return TxTapSettings( None, 4, -16, 96, 0, 0, 0 )
      else:
         assert False, f"Invalid medium {medium} for speed {serdesSpeed}"
   else:
      assert False, f"Invalid speed {serdesSpeed}"
