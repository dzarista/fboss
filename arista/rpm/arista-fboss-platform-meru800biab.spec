Name: arista-fboss-platform-meru800biab
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Meru800biab Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _fboss_meru800biab_dir fboss.git/arista/platform/meru800biab
%define _fboss_build_repo_dir tmp_build_dir/repos/github.com-facebook-fboss.git
%define _fboss_oss_dir %{_fboss_build_repo_dir}/fboss/oss
%define _fboss_config_dir %{_fboss_build_repo_dir}/fboss/platform/configs
%define _sai_sdk_src_dir Aqua_SAI/sdk-src

%define _fboss_target_share %{root}/%{buildroot}/opt/fboss/share
%define _fboss_target_var %{root}/%{buildroot}/var/facebook/fboss/

%define _link_test_configs /opt/fboss/share/link_test_configs
%define _hw_test_configs /opt/fboss/share/hw_test_configs
%define _qsfp_test_configs /opt/fboss/share/qsfp_test_configs

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Meru800biab (ViperB0) switches.

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/%{_fboss_meru800biab_dir}/* .
find %{SOURCEURL0}/%{_sai_sdk_src_dir} -wholename "*/tools/sand/db" -exec cp -r {} . \;
mkdir -p platform_configs
cp -af %{SOURCEURL0}/%{_fboss_config_dir}/meru800biab/* platform_configs/
mkdir -p config_files
cp -af %{SOURCEURL0}/fboss.git/fboss/oss/link_test_configs/meru800bia.materialized_JSON config_files/
cp -af %{SOURCEURL0}/fboss.git/fboss/oss/hw_test_configs/meru800bia.agent.materialized_JSON config_files/
cp -af %{SOURCEURL0}/fboss.git/fboss/oss/qsfp_test_configs/meru800bia.materialized_JSON config_files/

%install
mkdir -p %{_fboss_target_share}
cp -rf db %{_fboss_target_share}/
mkdir -p %{_fboss_target_var}
install config/fruid/fruid.json %{_fboss_target_var}
mkdir -p %{_fboss_target_share}/platform_configs
cp -rf platform_configs/* %{_fboss_target_share}/platform_configs/
cp -f config_files/meru800bia.materialized_JSON %{_link_test_configs}/meru800biab.materialized_JSON
cp -f config_files/meru800bia.agent.materialized_JSON %{_hw_test_configs}/meru800biab.agent.materialized_JSON
cp -f config_files/meru800bia.materialized_JSON %{_qsfp_test_configs}/meru800biab.materialized_JSON
/opt/fboss/share/link_test_configs

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/db
/opt/fboss/share/platform_configs
