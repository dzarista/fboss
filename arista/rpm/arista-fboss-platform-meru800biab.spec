Name: arista-fboss-platform-meru800biab
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Meru800biab Platform Utilities
Requires: arista-fboss-core

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _fboss_meru800biab_dir %{_fboss_dir}/arista/platform/meru800bia
%define _fboss_config_dir %{_fboss_dir}/fboss/platform/configs
%define _fboss_fw_dir %{_fboss_dir}/fboss.bsp.arista/meru800bia/firmware

%define _fboss_target_share %{buildroot}/opt/fboss/share
%define _fboss_target_var %{buildroot}/var/facebook/fboss

%define _link_test_configs /opt/fboss/share/link_test_configs
%define _hw_test_configs /opt/fboss/share/hw_test_configs
%define _qsfp_test_configs /opt/fboss/share/qsfp_test_configs

%description
This package provides platform-specific utilities to run Meta FBOSS OSS on Arista
Meru800biab (ViperB0) switches.

%install
mkdir -p %{_fboss_target_share}
cp -rf %{_sai_sdk_dir}/db %{_fboss_target_share}/

mkdir -p %{_fboss_target_var}
install %{_fboss_meru800biab_dir}/config/fruid/fruid.json %{_fboss_target_var}
# Overwrite the product name in the fruid
sed -i 's/"Product Name": "Meru800bia"/"Product Name": "Meru800biab"/' %{_fboss_target_var}/fruid.json

mkdir -p %{_fboss_target_share}/platform_configs
cp -rf %{_fboss_config_dir}/meru800bia/* %{_fboss_target_share}/platform_configs/

mkdir -p %{_fboss_target_share}/firmware
mkdir -p %{_fboss_target_share}/firmware/oldreleases
%define _latest_fw_package %(find %{_fboss_fw_dir} -maxdepth 1 -type d -name 'package_*' | sort -V | tail -n 1 | xargs realpath)
cp -rf %{_latest_fw_package}/* %{_fboss_target_share}/firmware/
cp -rf %{_fboss_fw_dir}/firmware_downgrade/* %{_fboss_target_share}/firmware/oldreleases/

# TODO: Move this to the spec for RPM that provides these files
%post
# Copy the platform configs from meru800bia and rename them to meru800biab
if [ -f %{_link_test_configs}/meru800bia.materialized_JSON ]; then
    cp -f %{_link_test_configs}/meru800bia.materialized_JSON %{_link_test_configs}/meru800biab.materialized_JSON
    cp -f %{_hw_test_configs}/meru800bia.agent.materialized_JSON %{_hw_test_configs}/meru800biab.agent.materialized_JSON
    cp -f %{_qsfp_test_configs}/meru800bia.materialized_JSON %{_qsfp_test_configs}/meru800biab.materialized_JSON
else
    echo "Meru800bia agent configs not found." >&2
fi

%files
/var/facebook/fboss/fruid.json
/opt/fboss/share/db
/opt/fboss/share/platform_configs
/opt/fboss/share/firmware
