Name: arista-fboss-platform-meru400bia
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Meru400bia Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _fboss_meru400bia_dir fboss.git/arista/platform/meru400bia
%define _fboss_build_repo_dir tmp_build_dir/repos/github.com-facebook-fboss.git
%define _fboss_bcm_hw_config_dir %{_fboss_build_repo_dir}/fboss/oss/hw_test_configs
%define _sai_sdk_src_dir Aqua_SAI/sdk-src

%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss/
%define _fboss_target_bin %{buildroot}/opt/fboss/bin/
%define _fboss_target_udev %{buildroot}/etc/udev/rules.d/

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Meru400bia (QuartzDD) switches.

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/%{_fboss_meru400bia_dir}/* .
cp -af %{SOURCEURL0}/%{_fboss_bcm_hw_config_dir}/meru400bia.agent.materialized_JSON .
find %{SOURCEURL0}/%{_sai_sdk_src_dir} -wholename "*/tools/sand/db" -exec cp -r {} . \;

%install
mkdir -p %{_fboss_target_share}/wedge_agent/
install meru400bia.agent.materialized_JSON %{_fboss_target_share}/wedge_agent/platform_wedge_agent.conf
cp -rf db %{_fboss_target_share}/
mkdir -p %{_fboss_target_share}/qsfp_service/
install config/qsfp_service/meru400bia_qsfp.conf %{_fboss_target_share}/qsfp_service/platform_qsfp.conf
mkdir -p %{_fboss_target_var}
install config/fruid/fruid.json %{_fboss_target_var}
mkdir -p %{_fboss_target_bin}
install -m 755 scripts/platform_init.sh %{_fboss_target_bin}
mkdir -p %{_fboss_target_udev}
install config/udev/99-meru400bia.rules %{_fboss_target_udev}

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/db
/opt/fboss/share/wedge_agent/platform_wedge_agent.conf
/opt/fboss/share/qsfp_service/platform_qsfp.conf
/opt/fboss/bin/platform_init.sh
/etc/udev/rules.d/99-meru400bia.rules
