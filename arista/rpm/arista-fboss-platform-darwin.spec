Name: arista-fboss-platform-darwin
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Darwin Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _fboss_darwin_dir fboss.git/arista/platform/darwin
%define _fboss_build_repo_dir tmp_build_dir/repos/github.com-facebook-fboss.git
%define _fboss_config_dir %{_fboss_build_repo_dir}/fboss/platform/config_lib/configs

%define _fboss_target_udev %{buildroot}/etc/udev/rules.d/
%define _fboss_target_bin %{buildroot}/opt/fboss/bin/
%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss/

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Darwin switches.

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/%{_fboss_darwin_dir}/* .
cp -af %{SOURCEURL0}/%{_fboss_config_dir}/sensor_service/darwin.json platform_sensors.conf

%install
mkdir -p %{_fboss_target_bin}
install -m 755 scripts/platform_init.sh %{_fboss_target_bin}
mkdir -p %{_fboss_target_udev}
install config/udev/99-darwin.rules %{_fboss_target_udev}
mkdir -p %{_fboss_target_share}/sensor_service/
install platform_sensors.conf %{_fboss_target_share}/sensor_service/
mkdir -p %{_fboss_target_var}
install config/fruid/fruid.json %{_fboss_target_var}

%files
/opt/fboss/bin/platform_init.sh
/etc/udev/rules.d/99-darwin.rules
/var/facebook/fboss/fruid.json
/opt/fboss/share/sensor_service/platform_sensors.conf
