# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

"""
This file contains the logic to generate the vendor mappings of a platform.

Before running this script:
 - Create a new directory under arista/util/configs-and-diagrams/l1lib/platform-csvs
   with the name of the platform.
 - Under it place the generated Trace tuning csvs. See README.md for more details.
 - Ensure that the platform config under GenerateConfigsAndDiagrams/Platforms 
   defines the xcvrs.

E.g. python3 generate.py --platform QuicksilverPFb --output vendor-mappings

The generated vendor mappings can be found under:
fboss/lib/platform_mapping_v2/platforms/<platform_name>


NOTE: 1. This script has only been tested on th5 quicksilver.
      2. This script does not support generating mappings for fabric ports
"""

import csv
from dataclasses import astuple
from l1lib.L1Utils import (
   asicNifSerdesSpeed,
   getProfileDetails,
   getProfileSettings,
   getProfileToNameMap,
   getUniqueProfileIds,
   parseMediumToPortMedium,
   parseSpeedToSpeedGbps,
   TxTapSettings,
   sortUniqueProfileIds,
   speedInMbps,
   validMediaForSpeed,
   validNifSerdesSpeeds
)
from l1lib.VendorMappings import (
   PortProfileMapping,
   ProfileSettings,
   SISettings,
   StaticMapping,
)
import os

ARCHITECTURE = [ 'dnx', 'xgs' ]

class L1Configs:
   def __init__( self, platform_name, arch, asic, num_asics,
                 xcvrs, profile_exclude=[] ):
      self.platform_name = platform_name
      self.arch = arch
      self.asic = asic
      self.num_asics = num_asics
      self.xcvrs = xcvrs
      self.profile_exclude = profile_exclude
      self.output_dir = (
         f"../../../fboss/lib/platform_mapping_v2/platforms/{platform_name}" )
      self.static_mapping_file = os.path.join(
         self.output_dir, f"{platform_name}_static_mapping.csv" )
      self.port_profile_mapping_file = os.path.join(
         self.output_dir, f"{platform_name}_port_profile_mapping.csv" )
      self.si_settings_file = os.path.join(
         self.output_dir, f"{platform_name}_si_settings.csv" )
      self.profile_settings_file = os.path.join(
         self.output_dir, f"{platform_name}_profile_settings.csv" )
      self.tuning_dir = f"l1lib/platform-csvs/{platform_name}"
      self.trace_file = f"{self.tuning_dir}/Trace.csv"
      self.all_profiles = getProfileDetails()

      os.makedirs( self.output_dir, exist_ok=True )

      assert os.path.exists( self.trace_file ), f"{self.trace_file} not found"
      assert arch in ARCHITECTURE, f"invalid arch: {arch}"

   def _gen_asic_serdes_mappings( self ):
      numNifSerdesOctets = len( self.xcvrs )

      def frontPanelSlotToPortType( slot ):
         assert 1 <= slot <= numNifSerdesOctets
         return "nif"

      def numLanesInFrontPanelSlot( slot ):
         assert 1 <= slot <= numNifSerdesOctets
         return self.xcvrs[ slot - 1 ].lanesCount

      asicSerdesMappings = [ { 'nif': {} } for _ in range( self.num_asics ) ]

      with open( self.trace_file ) as fh:
         for line in fh:
            if line.startswith( "System" ):
               continue
            ( asic,
              systemSerdesId,
              frontPanelSlot,
              lineSideLane,
              _,
              connectionType,
              polaritySwap ) = line.rstrip().split( "," )
            asic = int( asic )
            frontPanelSlot = int( frontPanelSlot )
            portType = frontPanelSlotToPortType( frontPanelSlot )
            systemSerdesId = int( systemSerdesId )
            lanesInSlot = numLanesInFrontPanelSlot( frontPanelSlot )
            lineSideLane = int( lineSideLane )
            lineSideSerdes = ( ( systemSerdesId // lanesInSlot ) * lanesInSlot
               ) + lineSideLane
            assert asic < self.num_asics
            asicPortMapping = asicSerdesMappings[ asic ][ portType ]
            asicPortMapping.setdefault( lineSideSerdes, {} )
            if connectionType not in asicPortMapping[ lineSideSerdes ]:
               asicPortMapping[ lineSideSerdes ][ connectionType ] = (
                  frontPanelSlot,
                  systemSerdesId,
                  polaritySwap )
      return asicSerdesMappings

   def gen_supported_profiles( self ):
      """
      Dictionary of lane index to a list of supported profiles
      """
      # Get the maximum serdes speed in Mbps for the ASIC
      max_serdes_speed_mbps = speedInMbps( asicNifSerdesSpeed( self.asic ) )
      self.physical_lanes = self.xcvrs[ 0 ].lanesCount
      supported_profiles = {}

      # Iterate over every possible profile
      for profile in self.all_profiles:
         profile_name = profile[ 'name' ]
         profile_lanes = profile[ 'lanes' ]

         if profile_lanes == 0 or profile_name in self.profile_exclude:
            continue

         profile_serdes_speed = ( 
            profile[ 'total_speed_gbps' ] * 1000 ) / profile_lanes
         if profile_serdes_speed > max_serdes_speed_mbps:
            continue

         # A profile can start on any lane that is a multiple of its own lane count
         for start_lane in range( 1, self.physical_lanes + 1, profile_lanes ):
            if ( start_lane + profile_lanes - 1 ) <= self.physical_lanes:
               supported_profiles.setdefault( start_lane, [] )
               supported_profiles[ start_lane ].append( str( profile[ 'value' ] ) )

      final_profiles = {}
      for start_lane, profile_list in supported_profiles.items():
         if profile_list:
            profile_list.sort( key=int )
            final_profiles[ start_lane ] = profile_list
               
      return dict( sorted( final_profiles.items() ) )

   def gen_static_mapping( self, asicSerdesMappings ):
      asicId = 0
      nifFrontPanelSlotToSerdesCore = {}
      with open( self.static_mapping_file, "w", newline="" ) as fh:
         fields = [ field for field in StaticMapping.getLabels() ]
         mappingWriter = csv.writer(
            fh, lineterminator="\n", quoting=csv.QUOTE_NONE )
         mappingWriter.writerow( fields )

         def genSerdesCoreMappings( serdesCore, firstSerdes, numSerdes, portType ):
            tempProps = {}
            asicPortSerdesMappings = asicSerdesMappings[ asicId ][ portType ]
            for lane in range( numSerdes ):
               serdesId = firstSerdes + lane
               frontPanelSlot, rxLane, rxPolSwap = asicPortSerdesMappings[
                     serdesId ][ "rx" ]
               _frontPanelSlot, txLane, txPolSwap = asicPortSerdesMappings[
                     serdesId ][ "tx" ]
               assert firstSerdes <= rxLane < firstSerdes + numSerdes
               assert firstSerdes <= txLane < firstSerdes + numSerdes
               assert frontPanelSlot == _frontPanelSlot
               frontPanelLane = lane
               if portType == "nif":
                  logicalLane = lane
                  nifFrontPanelSlotToSerdesCore[ frontPanelSlot ] = serdesCore
                  asicCoreType = f"{self.asic.upper()}_NIF"
               rxPolSwap = rxPolSwap[ 0 ]
               txPolSwap = txPolSwap[ 0 ]
               tempProps[ logicalLane ] = StaticMapping(
                  A_SLOT_ID=1,
                  A_CHIP_ID=1,
                  A_CHIP_TYPE="NPU",
                  A_CORE_ID=serdesCore,
                  A_CORE_TYPE=asicCoreType,
                  A_CORE_LANE=logicalLane,
                  A_PHYSICAL_TX_LANE=txLane,
                  A_PHYSICAL_RX_LANE=rxLane,
                  A_TX_POLARITY_SWAP=txPolSwap,
                  A_RX_POLARITY_SWAP=rxPolSwap,
                  Z_SLOT_ID=1,
                  Z_CHIP_ID=frontPanelSlot,
                  Z_CHIP_TYPE="TRANSCEIVER",
                  Z_CORE_ID=0,
                  Z_CORE_TYPE="OSFP",
                  Z_CORE_LANE=frontPanelLane,
                  Z_PHYSICAL_TX_LANE=frontPanelLane,
                  Z_PHYSICAL_RX_LANE=frontPanelLane,
                  Z_TX_POLARITY_SWAP="N",
                  Z_RX_POLARITY_SWAP="N" )
            for lane in range( numSerdes ):
                  mappingWriter.writerow( astuple( tempProps[ lane ] ) )

         for serdesCore, xcvr in enumerate( self.xcvrs ):
            genSerdesCoreMappings(
               serdesCore,
               serdesCore * xcvr.lanesCount,
               xcvr.lanesCount,
               "nif" )
      return nifFrontPanelSlotToSerdesCore

   def gen_port_profile_mapping( self, nifFrontPanelSlotToSerdesCore,
                                 supportedProfiles ):
       with open( self.port_profile_mapping_file, "w" ) as fh:
         fields = [ field for field in PortProfileMapping.getLabels() ]
         mappingWriter = csv.writer(
            fh, lineterminator="\n", quoting=csv.QUOTE_NONE )
         mappingWriter.writerow( fields )
         nifLogicalPortIdBase = 1

         for xcvr in self.xcvrs:
            frontPanelSlot = xcvr.portNumber
            subPorts = list( range( 1, xcvr.lanesCount + 1 ) )
            for subPort in subPorts:
               portStr = f"eth1/{frontPanelSlot}/{subPort}"
               serdesCoreId = nifFrontPanelSlotToSerdesCore[ frontPanelSlot ]
               nifSupportedProfiles = "-".join(
               supportedProfiles.get( subPort, [] ) )
               # Calculate logical port id from serdes core id and lane number 
               nifLogicalPortId = (
                  nifLogicalPortIdBase
                  + ( serdesCoreId * len( subPorts ) )
                  + subPort
                  - 1 )
               mappingWriter.writerow(
                  astuple(
                     PortProfileMapping(
                        Global_PortID=nifLogicalPortId,
                        Logical_PortID=nifLogicalPortId,
                        Port_Name=portStr,
                        Supported_Port_Profiles=nifSupportedProfiles,
                        Attached_CoreID="",
                        Attached_Core_PortID="",
                        Virtual_Device_ID="",
                        Port_Type=0,
                        Scope=0 ) ) )
               nifLogicalPortId += 1

   def _get_tuning_settings( self ):
      txTapSettingsByLane = {}

      assert os.path.exists( self.tuning_dir ), f"{self.tuning_dir} doesn't exist"

      for filename in os.listdir( self.tuning_dir ):
         if not ( filename.startswith( "Tuning_" ) and filename.endswith( ".csv" ) ):
            continue
         filepath = os.path.join( self.tuning_dir, filename )
         parts = filename.replace( ".csv", "" ).split( "_" )
         medium = parseMediumToPortMedium( parts[ 1 ] )
         speed = parseSpeedToSpeedGbps( parts[ 2 ] )

         if speed not in txTapSettingsByLane:
            txTapSettingsByLane[ speed ] = { medium: {} }
         elif medium not in txTapSettingsByLane[ speed ]:
            txTapSettingsByLane[ speed ][ medium ] = {}
         else:
            raise Exception( f'Duplicate tuning file detected {filename}' )

         with open( filepath, "r" ) as fh:
            for line in fh:
               if line.startswith( "ComponentId" ) or not line.strip():
                  continue
               
               # Get tuning csv content (8 columns)
               line_parts = line.rstrip().split(",")
               ( SerdesId, Pre3Tap, Pre2Tap, Pre1Tap, MainTap, Post1Tap,
                Post2Tap ) = [ int( part ) for part in line_parts[ 1:8 ] ]

               taps = TxTapSettings( Pre3Tap, Pre2Tap, Pre1Tap, MainTap,
                                       Post1Tap, Post2Tap, 0 )
               txTapSettingsByLane[ speed ][ medium ][ SerdesId ] = taps
      return txTapSettingsByLane

   def _create_si_setting_row( self, chipId, coreId, coreLane,
                               speed, medium, txTapSettings ):
      return astuple(
         SISettings( 1, chipId, "NPU", coreId,
                     f"{self.asic.upper()}_NIF",
                     coreLane, speedInMbps( speed ),
                     medium.name, None, None, None,
                     txTapSettings.pre3,
                     txTapSettings.pre2,
                     txTapSettings.pre1,
                     txTapSettings.main,
                     txTapSettings.post1,
                     txTapSettings.post2,
                     txTapSettings.post3,
                     None, None, None ) )

   def _process_xcvr_lane( self, mappingWriter, chipId, xcvr, coreLane,
                           speed, medium, tuning_settings ):
      coreId = xcvr.portNumber - 1
      logicalNifSerdes = ( coreId * xcvr.lanesCount) + coreLane

      # Skip if tuning settings not available for this speed/medium combination
      if not( speed in tuning_settings and medium in tuning_settings[ speed ] ):
         return

      txTapSettings = tuning_settings[ speed ][ medium ][ logicalNifSerdes ]
      row = self._create_si_setting_row( chipId, coreId, coreLane, speed,
                                         medium, txTapSettings )
      mappingWriter.writerow( row )

   def _process_xcvr( self, mappingWriter, chipId, xcvr,
                      speed, medium, tuning_settings ):
      for coreLane in range( xcvr.lanesCount ):
         self._process_xcvr_lane( mappingWriter, chipId, xcvr, coreLane,
                                  speed, medium, tuning_settings )

   def _process_speed_medium_combination( self, mappingWriter, chipId,
                                          speed, medium, tuning_settings ):
      for xcvr in self.xcvrs:
         self._process_xcvr( mappingWriter, chipId, xcvr,
                             speed, medium, tuning_settings )

   def gen_si_settings( self ):
      """Generate SI settings file with reduced nesting."""
      asicId = 0
      chipId = asicId + 1
      tuning_settings = self._get_tuning_settings()

      with open( self.si_settings_file, "w" ) as fh:
         fields = [ field for field in SISettings.getLabels() ]
         mappingWriter = csv.writer( fh, lineterminator="\n", quoting=csv.QUOTE_NONE )
         mappingWriter.writerow( fields )

         # Process all speed/medium combinations
         for speed in validNifSerdesSpeeds():
            for medium in validMediaForSpeed( speed ):
               self._process_speed_medium_combination( mappingWriter, chipId, speed, 
                                                       medium, tuning_settings )

   def gen_profile_settings( self, supportedProfiles ):
      with open( self.profile_settings_file, "w" ) as fh:
         fields = [ field for field in ProfileSettings.getLabels() ]
         mappingWriter = csv.writer(
            fh, lineterminator="\n", quoting=csv.QUOTE_NONE )
         mappingWriter.writerow( fields )

         profileToNameMap = getProfileToNameMap()
         uniqueProfileIds = getUniqueProfileIds( supportedProfiles )
         sortedProfielIds = sortUniqueProfileIds( uniqueProfileIds )

         for profileId in sortedProfielIds:
            profileName = profileToNameMap.get( int( profileId ) )
            details = getProfileSettings( profileName )

            # Profile_settings fec values differ slightly
            fec = details[ "fec" ]
            if fec == "NOFEC":
               fec = "NONE"
            elif fec == "RS544X2N":
               fec = "RS544_2N"

            mappingWriter.writerow(
               astuple(
                  ProfileSettings(
                     Port_Speed_mbps=details[ "speed_mbps" ],
                     A_CHIP_TYPE="NPU",
                     Z_CHIP_TYPE="TRANSCEIVER",
                     NUM_LANES=details[ "num_lanes" ],
                     Modulation=details[ "modulation" ],
                     FEC=fec,
                     MEDIA_TYPE=details[ "media" ],
                     A_Interface_Type=details[ "interface_type" ],
                     Z_Interface_Type="" ) ) )

   def gen_vendor_mapping( self ):
      supportedProfiles = self.gen_supported_profiles()
      asicSerdesMappings = self._gen_asic_serdes_mappings()
      nifSlotToSerdesCore = self.gen_static_mapping( asicSerdesMappings )
      self.gen_port_profile_mapping( nifSlotToSerdesCore, supportedProfiles )
      self.gen_si_settings()
      self.gen_profile_settings( supportedProfiles )