Name: arista-fboss-platform-meru800bfa
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Meru800bfa Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _fboss_meru800bfa_dir fboss.git/arista/platform/meru800bfa
%define _fboss_build_repo_dir tmp_build_dir/repos/github.com-facebook-fboss.git
#%define _fboss_bcm_hw_config_dir %{_fboss_build_repo_dir}/fboss/oss/hw_test_configs
%define _fboss_config_dir %{_fboss_build_repo_dir}/fboss/platform/configs
%define _sai_sdk_src_dir Aqua_SAI/sdk-src

%define _fboss_target_share %{root}/%{buildroot}/opt/fboss/share
%define _fboss_target_var %{root}/%{buildroot}/var/facebook/fboss/

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Meru800bfa (Whistler) switches.

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/%{_fboss_meru800bfa_dir}/* .
find %{SOURCEURL0}/%{_sai_sdk_src_dir} -wholename "*/tools/sand/db" -exec cp -r {} . \;
mkdir -p platform_configs
cp -af %{SOURCEURL0}/%{_fboss_config_dir}/meru800bfa/* platform_configs/

%install
mkdir -p %{_fboss_target_share}
cp -rf db %{_fboss_target_share}/
mkdir -p %{_fboss_target_var}
install config/fruid/fruid.json %{_fboss_target_var}
mkdir -p %{_fboss_target_share}/platform_configs
install config/npu*_platform_mapping.json %{_fboss_target_share}
mkdir -p %{_fboss_target_share}/platform_configs
cp -rf platform_configs/* %{_fboss_target_share}/platform_configs/

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/db
/opt/fboss/share/platform_configs
/opt/fboss/share/npu*_platform_mapping.json
