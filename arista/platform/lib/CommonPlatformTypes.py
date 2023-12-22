# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
from enum import Enum

PortMedium = Enum( 'PortMedium', 'Copper Optical' )
SpeedGbps = Enum( 'SpeedGbps',
      'TwentyFive Fifty FiftyThree Hundred HundredAndSix FourHundred' )

def validNifSerdesSpeeds():
   return ( SpeedGbps.Fifty, SpeedGbps.Hundred )

def validFabricSerdesSpeeds():
   return ( SpeedGbps.FiftyThree, SpeedGbps.HundredAndSix )


