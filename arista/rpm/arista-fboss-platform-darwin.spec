Name: arista-fboss-platform-darwin
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Darwin Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _fboss_darwin_dir %{_fboss_dir}/arista/platform/darwin
%define _fboss_build_repo_dir %{_scratch_dir}/repos/github.com-facebook-fboss.git
%define _fboss_config_dir %{_fboss_build_repo_dir}/fboss/platform/configs
%define _fboss_platform_dir %{_fboss_build_repo_dir}/arista/platform

%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Darwin switches.

%install
mkdir -p %{_fboss_target_var}
install %{_fboss_darwin_dir}/config/fruid/fruid.json %{_fboss_target_var}

mkdir -p %{_fboss_target_share}/platform_configs
cp -rf %{_fboss_config_dir}/darwin/* %{_fboss_target_share}/platform_configs/

mkdir -p %{_fboss_target_share}/firmware
cp -rf %{_fboss_platform_dir}/darwin/firmware/* %{_fboss_target_share}/firmware/

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/platform_configs
/opt/fboss/share/firmware
