Name: arista-fboss-platform-darwin48v
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Darwin48V Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _fboss_darwin_dir fboss.git/arista/platform/darwin48v
%define _fboss_build_repo_dir tmp_build_dir/repos/github.com-facebook-fboss.git
%define _fboss_config_dir %{_fboss_build_repo_dir}/fboss/platform/configs

%define _fboss_target_udev %{root}/%{buildroot}/etc/udev/rules.d/
%define _fboss_target_bin %{root}/%{buildroot}/opt/fboss/bin/
%define _fboss_target_share %{root}/%{buildroot}/opt/fboss/share
%define _fboss_target_var %{root}/%{buildroot}/var/facebook/fboss/

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Darwin48V switches.

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/%{_fboss_darwin_dir}/* .
mkdir -p platform_configs
cp -af %{SOURCEURL0}/%{_fboss_config_dir}/darwin48v/* platform_configs/

%install
mkdir -p %{_fboss_target_var}
install config/fruid/fruid.json %{_fboss_target_var}
mkdir -p %{_fboss_target_bin}
install -m 755 scripts/platform_init.sh %{_fboss_target_bin}
mkdir -p %{_fboss_target_udev}
install config/udev/99-darwin48v.rules %{_fboss_target_udev}
mkdir -p %{_fboss_target_share}/platform_configs
cp -rf platform_configs/* %{_fboss_target_share}/platform_configs/

%files
/var/facebook/fboss/fruid.json
/opt/fboss/bin/platform_init.sh
/etc/udev/rules.d/99-darwin48v.rules
/opt/fboss/share/platform_configs
