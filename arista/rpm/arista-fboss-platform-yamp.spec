Name: arista-fboss-platform-yamp
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Yamp Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _fboss_yamp_dir fboss.git/arista/platform/yamp
%define _fboss_build_repo_dir tmp_build_dir/repos/github.com-facebook-fboss.git
%define _fboss_bcm_sai_config_dir %{_fboss_build_repo_dir}/fboss/bcm_sai_configs

%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss/

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Yamp switches.

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/%{_fboss_yamp_dir}/* .
cp -af %{SOURCEURL0}/%{_fboss_bcm_sai_config_dir}/yamp.agent.materialized_JSON .

%install
mkdir -p %{_fboss_target_share}/wedge_agent/
install yamp.agent.materialized_JSON %{_fboss_target_share}/wedge_agent/platform_wedge_agent.conf
mkdir -p %{_fboss_target_share}/qsfp_service/
install config/qsfp_service/yamp_qsfp.conf %{_fboss_target_share}/qsfp_service/platform_qsfp.conf
mkdir -p %{_fboss_target_var}
install config/fruid/fruid.json %{_fboss_target_var}

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/wedge_agent/platform_wedge_agent.conf
/opt/fboss/share/qsfp_service/platform_qsfp.conf
