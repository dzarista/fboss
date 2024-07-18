# FBOSS OSS Platform Manager Config Generation Tool

Copyright (C) 2024 Arista Networks, Inc.

## Purpose

This directory contains code for defining a Python-based hardware description of 
a specific platform and automatically generating the contents of 
`platform_manager.json` config files living in 
`arista-fboss/fboss/platform/configs/<platform_name>`.

## How to build

All Python objects necessary to build an internal representation of a platform are
defined in `BaseConfigs.py`. In order to define hardware description for a platform
not yet supported, create a new file Python file in `Platforms` directory with the
platform name. Bear in mind that all platform-specific classes (e.g. `Viper` and
`Whistler`) should inherit from `PlatformConfig`, which also pre-defines some common
platform features. If a new platform does not share these features, they have to be
overwritten in the child class.

Every platform-specific file should define a `main` function that simply instantiates
an object of the given class and generates the JSON config by calling the overloaded
`.asJson()` method.

Hence, to generate a PM config for a specific platform (e.g. `Viper`), run
```
python3 -m Platforms.Viper > platform_manager.json
```
from the `GeneratePmConfigs` directory.