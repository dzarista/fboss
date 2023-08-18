Name: arista-fboss-platform-meru800bia
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Meru800bia Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _fboss_meru800bia_dir fboss.git/arista/platform/meru800bia
%define _fboss_build_repo_dir tmp_build_dir/repos/github.com-facebook-fboss.git
%define _fboss_bcm_hw_config_dir %{_fboss_build_repo_dir}/fboss/oss/hw_test_configs
%define _fboss_config_dir %{_fboss_build_repo_dir}/fboss/platform/configs
%define _sai_sdk_src_dir Aqua_SAI/sdk-src

%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss/
%define _fboss_target_bin %{buildroot}/opt/fboss/bin/
%define _fboss_target_udev %{buildroot}/etc/udev/rules.d/

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Meru800bia (Viper) switches.

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/%{_fboss_meru800bia_dir}/* .
find %{SOURCEURL0}/%{_sai_sdk_src_dir} -wholename "*/tools/sand/db" -exec cp -r {} . \;
cp -af %{SOURCEURL0}/%{_fboss_config_dir}/meru800bia/sensor_service.json platform_sensors.conf

%install
mkdir -p %{_fboss_target_share}
cp -rf db %{_fboss_target_share}/
mkdir -p %{_fboss_target_var}
install config/fruid/fruid.json %{_fboss_target_var}
mkdir -p %{_fboss_target_bin}
install -m 755 scripts/platform_init.sh %{_fboss_target_bin}
mkdir -p %{_fboss_target_udev}
install config/udev/99-meru800bia.rules %{_fboss_target_udev}
mkdir -p %{_fboss_target_share}/sensor_service/
install platform_sensors.conf %{_fboss_target_share}/sensor_service/

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/db
/opt/fboss/bin/platform_init.sh
/etc/udev/rules.d/99-meru800bia.rules
/opt/fboss/share/sensor_service/platform_sensors.conf
