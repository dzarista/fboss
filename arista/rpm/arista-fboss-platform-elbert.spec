Name: arista-fboss-platform-elbert
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS Elbert Platform Utilities

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

Prefix: /opt
%define _fboss_fw_dir %{_fboss_dir}/fboss.bsp.arista/elbert/firmware
%define _fboss_target_share %{buildroot}/opt/fboss/share

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Elbert (Monterey) switches.

%install
mkdir -p %{_fboss_target_share}
mkdir -p %{_fboss_target_share}/firmware
mkdir -p %{_fboss_target_share}/firmware/oldreleases

%define _latest_fw_package %(find %{_fboss_fw_dir} -maxdepth 1 -type d -name 'package_*' | sort -V | tail -n 1)

cp -rf %{_latest_fw_package}/* %{_fboss_target_share}/firmware/
cp -rf %{_fboss_fw_dir}/firmware_downgrade/* %{_fboss_target_share}/firmware/oldreleases/

%files
/opt/fboss/share/firmware