Name: arista-fboss-platform-glath05a-64o
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Glath05a-64o Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _fboss_glath05a_64o_dir %{_fboss_dir}/arista/platform/glath05a-64o
%define _fboss_config_dir %{_fboss_dir}/fboss/platform/configs

%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Glath05a_64o (QuicksilverPFb) switches.

%install
mkdir -p %{_fboss_target_share}
cp -rf %{_sai_sdk_dir}/db %{_fboss_target_share}/

mkdir -p %{_fboss_target_var}
install %{_fboss_meru800ba_dir}/config/fruid/fruid.json %{_fboss_target_var}

mkdir -p %{_fboss_target_share}/platform_configs
cp -rf %{_fboss_config_dir}/meru800ba/* %{_fboss_target_share}/platform_configs/

# mkdir -p %{_fboss_target_share}/firmware
# cp -rf %{_fboss_meru800ba_dir}/firmware/* %{_fboss_target_share}/firmware/

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/db
/opt/fboss/share/platform_configs
# /opt/fboss/share/firmware
