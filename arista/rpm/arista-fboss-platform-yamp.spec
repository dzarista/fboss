Name: arista-fboss-platform-yamp
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Yamp Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _fboss_yamp_dir %{_fboss_dir}/arista/platform/yamp

%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Yamp switches.

%install
mkdir -p %{_fboss_target_var}
install %{_fboss_yamp_dir}/config/fruid/fruid.json %{_fboss_target_var}

%files
/var/facebook/fboss/fruid.json
