Name: arista-fboss-platform-meru800bia
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Meru800bia Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _fboss_meru800bia_dir %{_fboss_dir}/arista/platform/meru800bia
%define _fboss_config_dir %{_fboss_dir}/fboss/platform/configs
%define _fboss_fw_dir %{_fboss_dir}/fboss.bsp.arista/meru800bia/firmware

%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Meru800bia (Viper) switches.

%install
mkdir -p %{_fboss_target_share}
cp -rf %{_sai_sdk_dir}/db %{_fboss_target_share}/

mkdir -p %{_fboss_target_var}
install %{_fboss_meru800bia_dir}/config/fruid/fruid.json %{_fboss_target_var}

mkdir -p %{_fboss_target_share}/platform_configs
cp -rf %{_fboss_config_dir}/meru800bia/* %{_fboss_target_share}/platform_configs/

mkdir -p %{_fboss_target_share}/firmware
mkdir -p %{_fboss_target_share}/firmware/oldreleases
%define _latest_fw_package %(find %{_fboss_fw_dir} -maxdepth 1 -type d -name 'package_*' | sort -V | tail -n 1 | xargs realpath)
cp -rf %{_latest_fw_package}/* %{_fboss_target_share}/firmware/
cp -rf %{_fboss_fw_dir}/firmware_downgrade/* %{_fboss_target_share}/firmware/oldreleases/

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/db
/opt/fboss/share/platform_configs
/opt/fboss/share/firmware
