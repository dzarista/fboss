#!/usr/bin/env python3
# Copyright (c) 2025 Arista Networks, Inc. All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
from ast import literal_eval
import json
import os
import re


def create_platform_config( platform_name, codename ):
    platform_configs = (
        "../configs-and-diagrams/GenerateConfigsAndDiagrams/Platforms"
    )
    PlatformName = platform_name.capitalize()

    sample_path = os.path.join(
        os.path.dirname( __file__ ), f"{platform_configs}/sample.py"
    )
    new_platform_path = os.path.join(
        os.path.dirname( __file__ ), f"{platform_configs}/{PlatformName}.py"
    )

    with open( sample_path, "r" ) as f:
        content = f.read()

    content = content.replace( "_PLATFORM_NAME_", PlatformName )
    content = content.replace( "_codename_", codename )

    with open( new_platform_path, "w" ) as f:
        f.write( content )

    print( f"Created new platform config: {new_platform_path}" )


def create_spec_file( platform_name, codename ):
    sample_spec_path = os.path.join(
        os.path.dirname( __file__ ), "platform-sample.spec"
    )
    new_spec_path = os.path.join(
        os.path.dirname( __file__ ),
        f"../../rpm/platform/arista-fboss-platform-{codename}.spec",
    )

    with open( sample_spec_path, "r" ) as f:
        content = f.read()

    content = content.replace( '_PLATFORM_NAME_',
                               platform_name.lower().capitalize() )
    # variables can't contains dashes
    content = content.replace( '_codename2_', codename.replace( '-', '_' ) )
    content = content.replace( '_codename_', codename )

    with open( new_spec_path, 'w' ) as f:
        f.write( content )

    print( f"Created new spec file: {new_spec_path}" )


def create_fruid_json( codename ):
    new_fruid_path = os.path.join(
        os.path.dirname( __file__ ),
        f"../../platform/{codename}/config/fruid/fruid.json",
    )
    os.makedirs( os.path.dirname( new_fruid_path ), exist_ok=True )

    fruid_data = {
        "Actions": [],
        "Resources": [],
        "Information": {
            "Product Sub-Version": "1",
            "Facebook PCBA Part Number": "",
            "Product Version": "11",
            "Product Part Number": "000000",
            "Extended MAC Address Size": "0",
            "Facebook PCB Part Number": "",
            "Product Name": codename.lower().capitalize(),
            "Local MAC": "00:00:00:00:00:00",
            "PCB Manufacturer": "",
            "CRC8": "0x0",
            "System Assembly Part Number": "ASY0000",
            "ODM PCBA Serial Number": "",
            "Product Serial Number": "JPE00000000",
            "ODM PCBA Part Number": "",
            "System Manufacturing Date": "2024010100",
            "Version": "0",
            "Location on Fabric": "",
            "Assembled At": "",
            "Product Production State": "0",
            "Product Asset Tag": "",
            "Extended MAC Base": "00:00:00:00:00:00",
            "System Manufacturer": "",
        },
    }

    with open( new_fruid_path, "w" ) as f:
        json.dump( fruid_data, f )

    print( f"Created new fruid.json: {new_fruid_path}" )


def update_exclude_list( platform_name ):
    generate_py_path = os.path.join(
        os.path.dirname(__file__),
        "../configs-and-diagrams/generate.py",
    )

    PlatformName = platform_name.capitalize()

    with open( generate_py_path, "r" ) as f:
        content = f.read()

    match = re.search( r"EXCLUDE_LIST\s*=\s*({.*?})", content, re.DOTALL )
    assert match, f"Could not find EXCLUDE_LIST in {generate_py_path}"

    original_dict_str = match.group( 0 )
    dict_str_to_eval = match.group( 1 )

    exclude_list_data = literal_eval( dict_str_to_eval )

    for key in exclude_list_data:
        if isinstance( exclude_list_data[ key ], list ):
            if platform_name not in exclude_list_data[ key ]:
                exclude_list_data[ key ].append( PlatformName )

    formatted_dict = json.dumps( exclude_list_data, indent=3 )
    new_dict_str = f"EXCLUDE_LIST = {formatted_dict}"

    new_content = content.replace( original_dict_str, new_dict_str )

    with open( generate_py_path, "w" ) as f:
        f.write( new_content )

    print( f"Successfully updated EXCLUDE_LIST in {generate_py_path}" )

def update_fboss_thrift( codename ):
    fboss_thrift_path = os.path.join(
        os.path.dirname( __file__ ),
        "../../../fboss/lib/if/fboss_common.thrift",
    )

    with open( fboss_thrift_path, "r" ) as f:
        lines = f.readlines()

    new_platform_name = f"PLATFORM_{codename.upper().replace( '-', '_' )}"
    platform_regex = re.compile( r"^\s*(PLATFORM_[A-Z0-9_]+)\s*=\s*(\d+)" )
    
    parsed_enums = []
    for i, line in enumerate( lines ):
        if new_platform_name in line:
            print( f"Platform '{new_platform_name}' "
                   f"already exists in {fboss_thrift_path}. No changes needed." )
            return
        
        match = platform_regex.match( line )
        if match:
            parsed_enums.append( {
                "name": match.group( 1 ),
                "value": int( match.group( 2 ) ),
                "index": i
            } )


    assert parsed_enums, "Could not find any valid platform enums in the file."

    max_enum_val = max(
        ( enum[ "value" ] for enum in parsed_enums 
          if enum[ "name" ] != "PLATFORM_UNKNOWN" ),
        default=0
    )

    insertion_index = -1
    for i in range( len( parsed_enums ) - 1 ):
        current_val = parsed_enums[ i ][ "value" ]
        next_val = parsed_enums[ i + 1 ][ "value" ]

        if next_val != current_val + 1:
            insertion_index = parsed_enums[ i ][ "index" ] + 1
            break

    if insertion_index == -1:
        insertion_index = parsed_enums[ -1 ][ "index" ] + 1

    new_value = max_enum_val + 1
    new_platform_line = f"  {new_platform_name} = {new_value},\n"

    lines.insert( insertion_index, new_platform_line )

    with open( fboss_thrift_path, "w" ) as f:
        f.writelines( lines )

    print( f"Updated PlatformType in {fboss_thrift_path}"
           f" with '{new_platform_name}={new_value}'" )

def update_platform_mode( codename ):
    platform_mode_path = os.path.join(
        os.path.dirname( __file__ ),
        "../../../fboss/lib/platforms/PlatformMode.h",
    )

    with open( platform_mode_path, "r" ) as f:
        lines = f.readlines()

    new_platform_name = f"PLATFORM_{codename.upper().replace('-', '_')}"
    new_platform_codename = codename.upper()
    
    for line in lines:
        if new_platform_name in line:
            print(
                f"Platform '{new_platform_name}' already exists in "
                "{platform_mode_path}. No changes needed."
            )
            return

    insertion_index = -1
    for i, line in enumerate( lines ):
        if "PLATFORM_UNKNOWN" in line:
            insertion_index = i
            break

    assert insertion_index != -1, "Could not find PLATFORM_UNKNOWN in PlatformMode.h"

    new_case_line = (
        f'    case PlatformType::{new_platform_name}:\n'
        f'      return "{new_platform_codename}";\n'
    )

    lines.insert(insertion_index, new_case_line)

    with open( platform_mode_path, "w" ) as f:
        f.writelines( lines )

    print(f"Updated PlatformMode.h with '{new_platform_name}'")

def update_platform_mapping_utils( codename ):
    platform_mapping_utils_path = os.path.join(
        os.path.dirname( __file__ ),
        "../../../fboss/agent/platforms/common/PlatformMappingUtils.cpp",
    )

    with open( platform_mapping_utils_path, "r" ) as f:
        lines = f.readlines()

    new_platform_name = f"PLATFORM_{codename.upper().replace( '-', '_' )}"

    # check if platform already exists
    for line in lines:
        if new_platform_name in line:
            print(
                f"Platform '{new_platform_name}' already exists in {platform_mapping_utils_path}. "
                "No changes needed."
            )
            return

    # find the insertion point
    insertion_index = -1
    for i, line in enumerate( lines ):
        if "PLATFORM_UNKNOWN" in line:
            insertion_index = i
            break

    assert insertion_index != -1, ( f"Could not find PLATFORM_UNKNOWN in "
                                    "PlatformMappingUtils.cpp. This scripts "
                                    "works by injecting a new switch case with "
                                    f"{new_platform_name} above PLATFORM_UNKNOWN" )

    new_case_line = f"    case PlatformType::{new_platform_name}:\n"

    lines.insert( insertion_index, new_case_line )

    with open( platform_mapping_utils_path, "w" ) as f:
        f.writelines( lines )

    print( f"Updated PlatformMappingUtils.cpp with '{new_platform_name}'" )

def update_platform_product_info( codename ):
    platform_product_info_path = os.path.join(
        os.path.dirname( __file__ ),
        "../../../fboss/lib/platforms/PlatformProductInfo.cpp",
    )

    with open( platform_product_info_path, "r" ) as f:
        lines = f.readlines()

    platform_name = f"PLATFORM_{codename.upper().replace( '-', '_' )}"

    for line in lines:
        if platform_name in line:
            print(
                f"Platform '{platform_name}' already exists in "
                "{platform_product_info_path}. No changes needed."
            )
            return

    insertion_index = -1

    # Search for insertion point on FLAGS_mode.empty case 
    for i, line in enumerate( lines ):
        if 'throw FbossError("invalid model name " + modelName)' in line:
            insertion_index = i
            break
    
    assert insertion_index != -1, ( f"Could not detect end of switch cases in "
                                    "PlatformProductInfo.cpp." )

    new_case_line = (
        f'    }} else if (\n'
        f'        modelName.find("{codename.capitalize()}") == 0 ||\n'
        f'        modelName.find("{codename.upper()}") == 0) {{\n'
        f'      type_ = PlatformType::{platform_name};\n'
    )

    lines.insert( insertion_index-1, new_case_line )

    # Search for insertion point on not FLAGS_mode.empty case
    for i, line in enumerate( lines ):
        if 'throw std::runtime_error("invalid mode " + FLAGS_mode)' in line:
            insertion_index = i
            break

    new_case_line = (
        f'    }} else if (FLAGS_mode == "{codename.lower()}") {{\n'
        f'      type_ = PlatformType::{platform_name};\n'
    )

    lines.insert( insertion_index-1, new_case_line )

    with open( platform_product_info_path, "w" ) as f:
        f.writelines( lines )

    print( f"Updated PlatformProductInfo.cpp initMode with '{platform_name}'" )

def main():
    parser = argparse.ArgumentParser(
        description="Create a new platform configuration."
    )
    parser.add_argument(
        "--platform_name",
        required=True,
        help="The name of the new platform (e.g., MyPlatform).",
    )
    parser.add_argument(
        "--codename",
        required=True,
        help="The codename for the new platform (e.g., myplatform).",
    )
    parser.add_argument(
        "--arch",
        required=True,
        choices=[ "xgs", "dnx" ],
        help="The architecture of the new platform.",
    )
    args = parser.parse_args()

    create_platform_config( args.platform_name, args.codename )
    create_spec_file( args.platform_name, args.codename )
    create_fruid_json( args.codename )
    update_exclude_list( args.platform_name )
    update_fboss_thrift( args.codename )
    update_platform_mode( args.codename )
    update_platform_mapping_utils( args.codename )
    update_platform_product_info( args.codename )

    print( f"\nNOTE: You will need to remove {args.platform_name} "
           "from arista/util/configs-and-diagrams/generate.py prior to generating "
           "any service configs." )


if __name__ == "__main__":
    main()
