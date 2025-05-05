## Instructions

This tool is a wrapper around the platform mapping genration tool located under `fboss/lib/platform_mapping_v2/`.

To use this command, you need to provide a folder path via `--input-dir` that includes the following files, with `PLATFORM` being a common string that identifies your platform:
- `PLATFORM_port_profile_mapping.csv`
- `PLATFORM_profile_settings.csv`
- `PLATFORM_si_settings.csv`
- `PLATFORM_static_mapping.csv`
- `PLATFORM_vendor_config.json`

Please put the vendor mapping files under arista/platform/<platform_name>/config

This command will generate the platform mapping config from these source files and save it to tmp/generated_platform_mappings/PLATFORM_NAME/

To enable proper `qsfp_service` and `agent` initialization, you must manually copy the generated JSON file into the C++ file `fboss/agent/platforms/common/PLATFORM_NAME/PLATFORM_NAME.cpp`.
