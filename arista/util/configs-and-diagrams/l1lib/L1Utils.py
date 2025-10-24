# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from dataclasses import dataclass
from enum import Enum

PortMedium = Enum( 'PortMedium', 'OPTICAL COPPER' )
SpeedGbps = Enum( 'SpeedGbps',
                  'TwentyFive '
                  'Fifty '
                  'FiftyThree '
                  'Hundred '
                  'TwoHundred '
                  'HundredAndSix '
                  'FourHundred '
                  'EightHundred '
                  'SixteenHundred')
Asic = Enum( 'Asic', 'th5 th6')
ProfileID = Enum( 'ProfileID', {
                  'PROFILE_100G_4_NRZ_RS528_COPPER': 22,
                  'PROFILE_100G_4_NRZ_RS528_OPTICAL': 23,
                  'PROFILE_200G_4_PAM4_RS544X2N_COPPER': 24,
                  'PROFILE_200G_4_PAM4_RS544X2N_OPTICAL': 25,
                  'PROFILE_400G_8_PAM4_RS544X2N_OPTICAL': 26,
                  'PROFILE_100G_4_NRZ_CL91_COPPER': 27,
                  'PROFILE_100G_4_NRZ_CL91_OPTICAL': 28,
                  'PROFILE_20G_2_NRZ_NOFEC_OPTICAL': 29,
                  'PROFILE_25G_1_NRZ_NOFEC_OPTICAL': 30,
                  'PROFILE_50G_2_NRZ_NOFEC_OPTICAL': 31,
                  'PROFILE_100G_4_NRZ_NOFEC_COPPER': 32,
                  'PROFILE_400G_8_PAM4_RS544X2N_COPPER': 35,
                  'PROFILE_53POINT125G_1_PAM4_RS545_COPPER': 36,
                  'PROFILE_53POINT125G_1_PAM4_RS545_OPTICAL': 37,
                  'PROFILE_400G_4_PAM4_RS544X2N_OPTICAL': 38,
                  'PROFILE_800G_8_PAM4_RS544X2N_OPTICAL': 39,
                  'PROFILE_100G_2_PAM4_RS544X2N_OPTICAL': 40,
                  'PROFILE_106POINT25G_1_PAM4_RS544_COPPER': 41,
                  'PROFILE_106POINT25G_1_PAM4_RS544_OPTICAL': 42,
                  'PROFILE_50G_1_PAM4_RS544_COPPER': 43,
                  'PROFILE_50G_1_PAM4_RS544_OPTICAL': 44,
                  'PROFILE_400G_4_PAM4_RS544X2N_COPPER': 45,
                  'PROFILE_100G_2_PAM4_RS544X2N_COPPER': 46,
                  'PROFILE_100G_1_PAM4_RS544_OPTICAL': 47,
                  'PROFILE_50G_2_NRZ_RS528_OPTICAL': 48,
                  'PROFILE_100G_1_PAM4_NOFEC_COPPER': 49,
                  'PROFILE_800G_8_PAM4_RS544X2N_COPPER': 50,
                  'PROFILE_400G_2_PAM4_RS544X2N_OPTICAL': 51,
                  'PROFILE_800G_4_PAM4_RS544X2N_OPTICAL': 52,
                  'PROFILE_200G_1_PAM4_RS544X2N_OPTICAL': 53 } )

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
   elif speed == SpeedGbps.TwoHundred:
      return 200000
   elif speed == SpeedGbps.FourHundred:
      return 400000
   elif speed == SpeedGbps.EightHundred:
      return 800000
   elif speed == SpeedGbps.SixteenHundred:
      return 1600000
   else:
      assert False, f"Invalid speed {speed}"

def parseSpeedToSpeedGbps( speedStr: str ) -> SpeedGbps:
   speedMap = {
      "25G": SpeedGbps.TwentyFive,
      "50G": SpeedGbps.Fifty,
      "53G": SpeedGbps.FiftyThree,
      "100G": SpeedGbps.Hundred,
      "106G": SpeedGbps.HundredAndSix,
      "200G": SpeedGbps.TwoHundred,
      "400G": SpeedGbps.FourHundred,
      "800G": SpeedGbps.EightHundred,
      "1600G": SpeedGbps.SixteenHundred,
   }

   assert speedStr in speedMap, f"Invalid speed {speedStr}"
   return speedMap.get( speedStr )

def parseMediumToPortMedium( mediumStr: str ) -> PortMedium:
   mediumMap = {
      "copper": PortMedium.COPPER,
      "fiber": PortMedium.OPTICAL,
      "optical": PortMedium.OPTICAL,
   }
   return mediumMap.get( mediumStr.lower() )

def asicNifSerdesSpeed( asic: Asic ) -> SpeedGbps:
   assert asic in Asic.__members__, f"{asic} is not a supported asic"
   if asic == Asic.th6:
      return SpeedGbps.TwoHundred
   else:
      return SpeedGbps.Hundred

def parseSpeedString( speed: str ) -> str:
   return speed.replace( 'G', '' ).replace( 'POINT', '.' )

def getProfileDetails() -> list[ dict ]:
   profile_list = []
   for name, member in ProfileID.__members__.items():
      parts = name.split( '_' )
      speed_str = parseSpeedString( parts[ 1 ] )
      total_speed_gbps = float( speed_str )
      lanes = int( parts[ 2 ] )
      
      profile_list.append({
         'name': name,
         'value': member.value,
         'total_speed_gbps': total_speed_gbps,
         'lanes': lanes
      })
   return profile_list

def validNifSerdesSpeeds() -> tuple[ SpeedGbps ]:
   return ( SpeedGbps.TwoHundred, SpeedGbps.Hundred, SpeedGbps.Fifty, SpeedGbps.TwentyFive )

def validFabricSerdesSpeeds() -> tuple[ SpeedGbps ]:
   return ( SpeedGbps.FiftyThree, SpeedGbps.HundredAndSix )

def validMediaForSpeed( speed: SpeedGbps ) -> tuple[ PortMedium ]:
   if speed == SpeedGbps.TwoHundred:
      return ( PortMedium.OPTICAL, )
   if speed in ( SpeedGbps.Hundred, SpeedGbps.TwentyFive, SpeedGbps.HundredAndSix ):
      return PortMedium.__members__.values()
   elif speed == SpeedGbps.Fifty:
      return ( PortMedium.COPPER, )
   elif speed == SpeedGbps.FiftyThree:
      return tuple()
   else:
      assert False, f"Invalid speed {speed}"

def getUniqueProfileIds( profiles: list[ list ] ) -> set:
   ids = set()
   for profile_list in profiles.values():
      ids.update( profile_list )
   return ids

def getProfileToNameMap() -> dict:
   return { member.value: name for name, member in ProfileID.__members__.items() }

def sortUniqueProfileIds( uniqueIds: str ) -> list:
   """
   Sorts a set of profile IDs in the following order
   speed -> lane count -> profile ID
   """
   sortedList = list( uniqueIds )
   profileToNameMap = getProfileToNameMap()
   
   sortedList.sort( key=lambda profileId: (
      parseSpeedString( profileToNameMap[ int( profileId ) ].split( '_' )[ 1 ] ),
      int( profileToNameMap [int( profileId ) ].split( '_' )[ 2 ] ),
      profileId
   ) )
   return sortedList

def getInterfaceType( media: str, lanes: int ) -> str:
   prefix = "SR" if media == "OPTICAL" else "CR"
   return f"{prefix}{lanes}" if lanes > 1 else prefix

def getProfileSettings( profile: str ) -> dict:
   if not profile:
      raise Exception( "Profile name is empty" )

   parts = profile.split( '_' )
   speed_str = parseSpeedString( parts[ 1 ] )
   
   details = {
      'speed_mbps': int( float( speed_str ) * 1000 ),
      'num_lanes': int( parts[ 2 ] ),
      'modulation': parts[ 3 ],
      'fec': parts[ 4 ],
      'media': parts[ 5 ],
      'interface_type': getInterfaceType( parts[ 5 ], int( parts[ 2 ] ) )
   }
   return details

@dataclass
class TxTapSettings:
   pre3: int = 0
   pre2: int = 0
   pre1: int = 0
   main: int = 0
   post1: int = 0
   post2: int = 0
   post3: int = 0
