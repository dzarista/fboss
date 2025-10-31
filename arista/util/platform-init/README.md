# Description
Generate minimal platform setup.

Whats supported so far:
- Minimal platform service config file under `arista/util/configs-and-diagrams/platforms/{platform_name}`
- fruid.json file under `arista/platform/{codename}/config/fruid/fruid.json`
- RPM spec file under `arista/rpm/arista-fboss-platform-{codename}.spec`
- FBOSS PlatformType enum entry under `fboss/lib/if/fboss_common.thrift`
- FBOSS PlatformType to string mapping under `fboss/lib/platforms/PlatformMode.h`
- Add platform to platform_mapping switch statement `fboss/agent/platforms/common/PlatformMappingUtils.cpp`
- Add platform to PlatformProductInfo.cpp initMode if statements `fboss/lib/platforms/PlatformProductInfo.cpp`

e.g python3 platform-init.py --platform_name steamerlane --codename glath06l-64or --arch xgs