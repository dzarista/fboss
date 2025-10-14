This is a tool that can be used to compare the config contents of the upstream vs the internal in a mostly order agnostic way.

To use:

pip install deepdiff
python3 compareConfigs.py

Optional Args:
--platform
        Filter based on platforms. Use * to filter based on platforms starting with the arg.
        (--platform darwin to filter only on darwin, --platform darwin* to filter on both darwin and darwin48v)
              
--config
        Filter based on config files starting with the arg (--config platform will generate only diffs for platform_manager.json)
