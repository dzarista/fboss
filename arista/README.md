# Arista FBOSS OSS

Copyright (C) 2023 Arista Networks, Inc.

## Purpose

This directory contains Arista-specific code for building, packaging, and installing
FBOSS OSS on Arista platforms.

## Directory Structure

The table below outlines the structure of this directory.

| Directory   | Description                                      |
|-------------|--------------------------------------------------|
| build-utils | Helper scripts for build tasks.                  |
| core        | Core FBOSS scripts and config.                   |
| platform    | Platform-specific scripts and config.            |
| rpm         | Spec files for code Arista code packages.        |

## How to Build

### In a Docker Container

The simplest way to build the FBOSS OSS + SAI + SDK is in an FBOSS CentOS 8 build
container. For ease of use, the `fbossctl` script is provided to automate building
and packaging. Run `fbossctl help` to show the usage.

To build, first clone this git repository locally on your user server. Next,
designate a build directory: this is where all build artifacts will live. You can
set the build directory by setting the `FBOSS_BUILD_DIR` env var. If this var is
not set, fbossctl will use `//garage/$USER/fboss-build` as the default build directory.

With the build directory set, run `fbossctl build` to build FBOSS OSS + SAI + SDK
from source. The `--arch` flag must be set to specify the SDK architecture. For your
first build, you will need to build FBOSS OSS, SAI, and the SDK. This build will take
around 40 minutes. All build artifacts can be found in `$FBOSS_BUILD_DIR/FBOSS_DIR`.

### Manually

To build FBOSS OSS + SAI + SDK manually outside of a container, you can use the
build-utils/build.sh script. The arguments are the same as `fbossctl build`, but an
extra `--build-dir` argument must be provided to specify the build directory.

### Rebuilding

To rebuild the SDK from scratch, you must specify `--rebuild-sdk` to `fbossctl build`.
To rebuild FBOSS OSS from scratch, you must specify `--rebuild-fboss`. To rebuild
only the FBOSS OSS binaries, use `fbossctl build --skip-sdk --fboss-bins-only`; this
is by far the fastest option.

## How to Package

Multiple spec files are included in `rpm/` to package the built source into
RPMs that can be installed on an Arista switch. The `arista-fboss-core.spec` file
contains the core FBOSS libraries and services, and `arista-platform-*.spec` files
contain platform-specific scripts and config files.

To build all RPMs, simply run `fbossctl package`. If you only want to build a
specific RPM, then provide the name of the RPM as an optional argument, e.g.
`fbossctl package arista-fboss-core`.

Built RPMs can be found in `$FBOSS_BUILD_DIR/FBOSS_DIR/rpmbuild/RPMS/`.

## How to install on a Switch

To install FBOSS OSS on an Arista switch in the lab, first build and package the
source as RPMs. With your RPMs built, sanitize your DUT using
`a dut sanitize --os=fbossOss --osArgs="ossRpmDir=<dir>"`.

### How to Quickly Reinstall Changes

When quickly testing changes with an already sanitized DUT, you can simply
copy your newly built RPMs to the switch. `fbossctl update-dut <dut>`
provides a convenient way to copy the latest RPMs to <dut>:/tmp. After copying
the RPMs, SSH to the DUT and install the RPMs using `rpm -ivh <rpm>`.

To re-initialize FBOSS OSS, run `/opt/fboss/bin/fboss_init.sh`.

## Other fbossctl Options

If you want to play around in the FBOSS CentOS 8 build container, run
`fbossctl shell`. This will drop you into a bash session in a build container,
which can be convenient for debug.

To delete the $FBOSS_BUILD_DIR/FBOSS_DIR directory, run `fbossctl clean`.

## How to add a New Platform

To add support for a new platform, create a new directory in `platform` with
any platform-specific code, then add a new spec file in `rpms/` with
instructions on how to build the platform code. Any special initialization
needs to be put in a `platform_init.sh` script that gets installed in
`/opt/fboss/bin/`; this will automatically get called during the generic
`fboss_init.sh`. Any service-specific configuration files should go in the
`platform/<platform>/config` directory. Make sure to also include a `fruid.json`
which FBOSS will use to identify the platform.
