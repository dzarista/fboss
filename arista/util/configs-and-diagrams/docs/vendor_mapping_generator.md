# Vendor Mapping Generator

## Overview

The Vendor Mapping Generator is a tool integrated within the platform generator tool "generate.py" and makes use of existing xcvr configs in the platform definition along with provided trace and tuning csv files to generate the vendor mappings.

## Purpose

This tool generates four critical configuration files for each platform:

1. **Static Mapping** (`*_static_mapping.csv`) - Physical lane connections between ASIC and transceivers
2. **SI Settings** (`*_si_settings.csv`) - Signal integrity parameters (TX tap settings)
3. **Port Profile Mapping** (`*_port_profile_mapping.csv`) - Supported port profiles per logical port
4. **Profile Settings** (`*_profile_settings.csv`) - Detailed settings for each supported profile

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Platform      │    │   L1Configs      │    │   Generated Files   │
│   Definition    │───▶│   Generator      │───▶│   (CSV Mappings)    │
│   (Python)      │    │                  │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
                                 ▲                        │
                                 │                        ▼
                       ┌──────────────────┐    ┌─────────────────────┐
                       │   Trace & Tuning │    │   FBOSS Platform    │
                       │   CSVs (l1lib)   │    │   Mapping Files     │
                       └──────────────────┘    └─────────────────────┘
```

## Prerequisites

### 1. Platform Definition

- A platform config to be defined under GenerateConfigsAndDiagrams/Platforms/<platform_name>
- The same platform config to define all the xcvrs with the accurate lanes count
- The same platform config to define the `l1` attribute as an `L1Configs` instance under the main switchcard class.

### 2. Input Files

#### Trace File (`Trace.csv`)
This file can be fetched from EOS or generated from this repo https://gitlab.aristanetworks.com/csv-generator/csvgenerator.

See the README.md under the above repo for instructions on how to generate the trace file.

**Location**: `l1lib/platform-csvs/<platform_name>/Trace.csv`

#### Tuning Files (`Tuning_<medium>_<speed>.csv`)
The tuning files need to be in the name format above where medium is either copper or fiber and speed is the speed of the port in Gbps. Reach out to EDVT for status on the tuning files.

**Location**: `l1lib/platform-csvs/<platform_name>/`

**Naming Convention**: `Tuning_<medium>_<speed>.csv`
- `<medium>`: `copper` or `fiber`
- `<speed>`: Speed in Gbps (e.g., `100G`, `50G`, `400G`)

**Format**:
```csv
ComponentId,SerdesId,Pre3Tap,Pre2Tap,Pre1Tap,MainTap,Post1Tap,Post2Tap
0,0,-4,14,-36,112,0,0
```

## Usage

```bash
cd arista/util/configs-and-diagrams
python3 generate.py --platform <PlatformName> --output vendor-mappings
```

### Example

```bash
python3 generate.py --platform QuicksilverPFb --output vendor-mappings
```

## Generated Output Files

All files are generated in: `fboss/lib/platform_mapping_v2/platforms/<platform_name>/`

### 1. Static Mapping (`<platform>_static_mapping.csv`)

Maps physical connections between ASIC serdes and transceiver lanes.

### 2. SI Settings (`<platform>_si_settings.csv`)

Contains signal integrity parameters for each serdes lane.

### 3. Port Profile Mapping (`<platform>_port_profile_mapping.csv`)

Maps logical ports to their supported profiles.

### 4. Profile Settings (`<platform>_profile_settings.csv`)

Detailed configuration for each supported profile.

## Adding a New Platform

### Step 1: Create Platform Directory Structure

```bash
mkdir -p l1lib/platform-csvs/<platform_name>
```

### Step 2: Complete The Platform Config

By this step, it is expected that the plaform cofig is defined and generates the xcvrs list.

Before moving on, define a `l1` attribute as an `L1Configs` instance under the main switchcard class.

```bash
# Define l1 configs
self.l1 = L1Configs( self.codename, arch="xgs", asic="th5", num_asics=1,
                    xcvrs=quicksilverSMB.pciDeviceConfigs[0].xcvrCtrlConfigs,
                    profile_exclude = [
                        'PROFILE_100G_4_NRZ_RS528_COPPER',
                        'PROFILE_200G_4_PAM4_RS544X2N_COPPER',
                        'PROFILE_400G_8_PAM4_RS544X2N_OPTICAL',
                        'PROFILE_100G_4_NRZ_CL91_COPPER',
                        'PROFILE_100G_4_NRZ_CL91_OPTICAL',
                        'PROFILE_20G_2_NRZ_NOFEC_OPTICAL',
                        'PROFILE_25G_1_NRZ_NOFEC_OPTICAL',
                        'PROFILE_50G_2_NRZ_NOFEC_OPTICAL',
                        'PROFILE_100G_4_NRZ_NOFEC_COPPER',
                        'PROFILE_400G_8_PAM4_RS544X2N_COPPER',
                        'PROFILE_53POINT125G_1_PAM4_RS545_COPPER',
                        'PROFILE_53POINT125G_1_PAM4_RS545_OPTICAL',
                        'PROFILE_100G_2_PAM4_RS544X2N_OPTICAL',
                        'PROFILE_50G_1_PAM4_RS544_COPPER',
                        'PROFILE_50G_1_PAM4_RS544_OPTICAL',
                        'PROFILE_100G_2_PAM4_RS544X2N_COPPER',
                        'PROFILE_50G_2_NRZ_RS528_OPTICAL'
                    ] )
```

### Step 3: Prepare Input Files

1. **Generate Trace.csv**: Reference Trace File section above for more details
2. **Add Tuning Files**: Reference Tuning File section above for more details

### Step 4: Generate Mappings

```bash
python3 generate.py --platform MyPlatform --output vendor-mappings
```

## Current Limitations

1. **Fabric Ports**: Currently only supports NIF (Network Interface) ports
2. **Single ASIC**: Tested primarily on single-ASIC platforms
3. **XGS Focused**: Most testing done on Tomahawk 5 platforms
4. **Fixed Slot Systems**: Designed for fixed-form-factor switches
5. **Broadcom configs not generated**: Broadcom asic configs are required to run the agent, but we don't have a way to generate them yet (there is a standalone script for quicksilver arista/util/configs-and-diagrams/l1lib/xgsBcmConfGen_quicksilver.py)