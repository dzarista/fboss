Name: arista-fboss-platform-meru400bia
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Meru400bia Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _fboss_meru400bia_dir %{_fboss_dir}/arista/platform/meru400bia

%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss
%define _fboss_target_bin %{buildroot}/opt/fboss/bin
%define _fboss_target_udev %{buildroot}/etc/udev/rules.d

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Meru400bia (QuartzDD) switches.

%install
mkdir -p %{_fboss_target_var}
install %{_fboss_meru400bia_dir}/config/fruid/fruid.json %{_fboss_target_var}

mkdir -p %{_fboss_target_share}
mkdir -p %{_fboss_target_share}/platform_configs
cp -rf %{_fboss_config_dir}/meru400bia/* %{_fboss_target_share}/platform_configs/

mkdir -p %{_fboss_target_bin}
install -m 755 %{_fboss_meru400bia_dir}/scripts/platform_init.sh %{_fboss_target_bin}

mkdir -p %{_fboss_target_udev}
install %{_fboss_meru400bia_dir}/config/udev/99-meru400bia.rules %{_fboss_target_udev}

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/platform_configs
/opt/fboss/bin/platform_init.sh
/etc/udev/rules.d/99-meru400bia.rules
