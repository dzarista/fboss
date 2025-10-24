# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import csv
from collections import namedtuple
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add the parent directory to the path to allow imports
sys.path.insert( 0, os.path.abspath( 
                        os.path.join( os.path.dirname( __file__ ), '..' ) ) )

from .L1Configs import L1Configs
from l1lib.L1Utils import SpeedGbps, TxTapSettings, PortMedium

class L1ConfigsTest( unittest.TestCase ):
    def setUp( self ):
        '''Create dummy test_platform files'''
        self.test_dir = tempfile.mkdtemp()
        self.platform_name = "test_platform"
        self.arch = "dnx"
        self.asic = "th5"
        self.num_asics = 1
        Xcvr = namedtuple( 'Xcvr', [ 'portNumber', 'lanesCount' ] )

        # Testing with an 8 port switch
        self.xcvrs = [ Xcvr( portNumber=i+1, lanesCount=8 ) for i in range( 8 ) ]

        # Create dummy directories and files in the temporary directory
        self.output_dir = os.path.join( self.test_dir,
            f"fboss/lib/platform_mapping_v2/platforms/{self.platform_name}" )
        self.l1lib_dir = os.path.join( self.test_dir,
            f"l1lib/platform-csvs/{self.platform_name}" )
        os.makedirs( self.output_dir, exist_ok=True )
        os.makedirs( self.l1lib_dir, exist_ok=True )

        # Dummy trace file
        self.trace_file_path = os.path.join( self.l1lib_dir, "Trace.csv" )
        with open( self.trace_file_path, "w" ) as f:
            f.write( "System,SystemSerdesId,FrontPanelSlot,LineSideLane,"
                     "SystemSideLane,ConnectionType,PolaritySwap\n" )
            for i in range( 64 ):
                f.write( f"0,{i},{i//8+1},{i%8},{i},rx,N\n" )
                f.write( f"0,{i},{i//8+1},{i%8},{i},tx,N\n" )

        # Dummy tuning file
        self.tuning_file_path = os.path.join( self.l1lib_dir,
                                              "Tuning_fiber_100G.csv" )
        with open( self.tuning_file_path, "w" ) as f:
            f.write( "ComponentId,SerdesId,Pre3Tap,Pre2Tap,Pre1Tap,MainTap,"
                     "Post1Tap,Post2Tap\n" )
            for i in range( 64 ):
                f.write( f"0,{i},0,6,-28,116,-20,0\n" )

    def tearDown( self ):
        shutil.rmtree( self.test_dir )

    def test_l1configs_initialization( self ):
        with patch( 'os.path.exists', return_value=True ), patch( 'os.mkdir' ):
            l1configs = L1Configs( self.platform_name, self.arch, self.asic,
                                   self.num_asics, self.xcvrs )

        l1configs.output_dir = self.output_dir
        self.assertEqual( l1configs.platform_name, self.platform_name )
        self.assertTrue( os.path.exists( self.output_dir ) )

    @patch( "builtins.open" )
    @patch( "os.listdir" )
    def test_get_tuning_settings( self, mock_listdir, mock_open ):
        mock_listdir.return_value = [ "Tuning_copper_50G.csv" ]
        
        mock_file_content = "ComponentId,SerdesId,Pre3Tap,Pre2Tap,Pre1Tap,MainTap," \
                            "Post1Tap,Post2Tap\n,0,0,4,-24,130,-12,0,0\n"
        mock_open.return_value.__enter__.return_value = \
                            mock_file_content.splitlines()

        with patch( 'os.path.exists', return_value=True ), patch( 'os.mkdir' ):
            l1configs = L1Configs( self.platform_name, self.arch, self.asic,
                                   self.num_asics, self.xcvrs )

        l1configs.tuning_dir = self.l1lib_dir
        tuning_settings = l1configs._get_tuning_settings()

        self.assertIn( SpeedGbps.Fifty, tuning_settings )
        self.assertIn( PortMedium.COPPER, tuning_settings[ SpeedGbps.Fifty ] )

        expected_taps = TxTapSettings( pre3=0, pre2=4, pre1=-24, main=130,
                                       post1=-12, post2=0, post3=0 )
        actual_taps = tuning_settings[ SpeedGbps.Fifty ][ PortMedium.COPPER ][ 0 ]
        self.assertEqual( actual_taps, expected_taps )

    def test_gen_si_settings_file_creation( self ):
        with patch( 'os.path.exists', return_value=True ), patch( 'os.mkdir' ):
            l1configs = L1Configs( self.platform_name, self.arch, self.asic,
                                   self.num_asics, self.xcvrs )

        l1configs.output_dir = self.output_dir
        l1configs.si_settings_file = os.path.join( self.output_dir,
                                        f"{self.platform_name}_si_settings.csv" )
        l1configs.tuning_dir = self.l1lib_dir
        l1configs.trace_file = self.trace_file_path

        # Test with no tuning settings
        l1configs.gen_si_settings()

        self.assertTrue( os.path.exists( l1configs.si_settings_file ) )
        with open( l1configs.si_settings_file, 'r' ) as f:
            lines = f.readlines()
            # 1 Header + 8 ports * 8 lanes * 1 media (100G Optic) = 65 Lines
            expected_lines = 65
            self.assertEqual( len( lines ), expected_lines)
            header = lines[0].strip().split(',')
            expected_header = [
                'SLOT_ID', 'CHIP_ID', 'CHIP_TYPE', 'CORE_ID', 'CORE_TYPE',
                'CORE_LANE', 'LANE_SPEED(mbps)', 'MEDIA_TYPE', 'TCVR_VENDOR',
                'NIC_VENDOR', 'CABLE_LENGTH(m)', 'TX_PRE3', 'TX_PRE2', 'TX_PRE1',
                'TX_MAIN', 'TX_POST1', 'TX_POST2', 'TX_POST3', 'RX_CTLE_CODE',
                'RX_DSP_MODE', 'RX_AFE_TRIM'
            ]
            self.assertEqual(header, expected_header)
        
        with open( l1configs.si_settings_file, 'r' ) as f:
            reader = csv.DictReader( f )
            for row in reader:
                if ( int( row[ 'CORE_LANE' ] ) == 0 
                     and int( row[ 'LANE_SPEED(mbps)' ] ) == 100000 ):
                    self.assertEqual( int( row[ 'TX_PRE2' ] ), 6 )
                    self.assertEqual( int( row[ 'TX_MAIN' ] ), 116 )
                    break
            else:
                self.fail("Tuning settings not applied")

    def test_gen_supported_profiles( self ):
        supported_th5_profiles = {
            1: [ '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32',
                 '35', '36', '37', '38', '39', '40', '43', '44', '45', '46', '47',
                 '48', '49', '50' ],
            2: [ '30', '36', '37', '43', '44', '47', '49' ],
            3: [ '29', '30', '31', '36', '37', '40', '43', '44', '46', '47', '48',
                 '49' ],
            4: [ '30', '36', '37', '43', '44', '47', '49' ],
            5: [ '22', '23', '24', '25', '27', '28', '29', '30', '31', '32', '36',
                 '37', '38', '40', '43', '44', '45', '46', '47', '48', '49' ],
            6: [ '30', '36', '37', '43', '44', '47', '49' ],
            7: [ '29', '30', '31', '36', '37', '40', '43', '44', '46', '47', '48',
                 '49' ],
            8: [ '30', '36', '37', '43', '44', '47', '49' ] }

        with patch( 'os.path.exists', return_value=True ), patch( 'os.mkdir' ):
            l1configs = L1Configs( self.platform_name, self.arch, self.asic,
                                   self.num_asics, self.xcvrs )

        supported_profiles = l1configs.gen_supported_profiles()
       
        self.assertEqual( supported_profiles[ 1 ], supported_th5_profiles[ 1 ] )
        self.assertEqual( supported_profiles[ 2 ], supported_th5_profiles[ 2 ] )
        self.assertEqual( supported_profiles[ 3 ], supported_th5_profiles[ 3 ] )
        self.assertEqual( supported_profiles[ 4 ], supported_th5_profiles[ 4 ] )
        self.assertEqual( supported_profiles[ 5 ], supported_th5_profiles[ 5 ] )
        self.assertEqual( supported_profiles[ 6 ], supported_th5_profiles[ 6 ] )
        self.assertEqual( supported_profiles[ 7 ], supported_th5_profiles[ 7 ] )
        self.assertEqual( supported_profiles[ 8 ], supported_th5_profiles[ 8 ] )

    def test_gen_static_mapping( self ):
        with patch( 'os.path.exists', return_value=True ), patch( 'os.mkdir' ):
            l1configs = L1Configs( self.platform_name, self.arch, self.asic,
                                   self.num_asics, self.xcvrs )

        l1configs.output_dir = self.output_dir
        l1configs.static_mapping_file = os.path.join( self.output_dir,
                                        f"{self.platform_name}_static_mapping.csv" )
        l1configs.trace_file = self.trace_file_path

        asic_serdes_mappings = l1configs._gen_asic_serdes_mappings()
        l1configs.gen_static_mapping( asic_serdes_mappings )

        self.assertTrue( os.path.exists( l1configs.static_mapping_file ) )
        with open( l1configs.static_mapping_file, 'r' ) as f:
            lines = f.readlines()
            expected_lines = 65 # ( 1 Header + 8 ports * 8 lanes )
            self.assertEqual( len( lines ), expected_lines ) 

    def test_gen_port_profile_mapping( self ):
        with patch( 'os.path.exists', return_value=True ), patch( 'os.mkdir' ):
            l1configs = L1Configs( self.platform_name, self.arch, self.asic,
                                   self.num_asics, self.xcvrs)

        l1configs.output_dir = self.output_dir
        l1configs.port_profile_mapping_file = os.path.join( self.output_dir,
                                f"{self.platform_name}_port_profile_mapping.csv" )

        supported_profiles = { 1: [ '22', '23' ] }
        nif_slot_to_serdes_core = { i+1: i for i in range(8) }

        l1configs.gen_port_profile_mapping( nif_slot_to_serdes_core,
                                            supported_profiles )

        self.assertTrue( os.path.exists( l1configs.port_profile_mapping_file ) )
        with open( l1configs.port_profile_mapping_file, 'r' ) as f:
            lines = f.readlines()
            expected_lines = 65 # ( 1 Header + 8 ports * 8 lanes )
            self.assertEqual( len( lines ), expected_lines )

    def test_gen_profile_settings( self ):
        with patch( 'os.path.exists', return_value=True ), patch( 'os.mkdir' ):
            l1configs = L1Configs( self.platform_name, self.arch, self.asic,
                                   self.num_asics, self.xcvrs )

        l1configs.output_dir = self.output_dir
        l1configs.profile_settings_file = os.path.join( self.output_dir,
                                f"{self.platform_name}_profile_settings.csv" )

        supported_profiles = { 1: [ '38', '39' ] }
        l1configs.gen_profile_settings( supported_profiles )

        self.assertTrue( os.path.exists( l1configs.profile_settings_file ) )
        with open( l1configs.profile_settings_file, 'r' ) as f:
            lines = f.readlines()
            self.assertEqual( len( lines ), 3 )
            header = lines[ 0 ].strip().split( ',' )
            expected_header = [
                'Port_Speed(mbps)', 'A_CHIP_TYPE', 'Z_CHIP_TYPE', 'NUM_LANES',
                'Modulation', 'FEC', 'MEDIA_TYPE', 'A_Interface_Type',
                'Z_Interface_Type'
            ]
            self.assertEqual( header, expected_header )
            self.assertEqual( lines[ 1 ], \
                    '400000,NPU,TRANSCEIVER,4,PAM4,RS544_2N,OPTICAL,SR4,\n' )
            self.assertEqual( lines[ 2 ], \
                    '800000,NPU,TRANSCEIVER,8,PAM4,RS544_2N,OPTICAL,SR8,\n' )

if __name__ == '__main__':
    unittest.main()
