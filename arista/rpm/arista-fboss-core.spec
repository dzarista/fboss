Name: arista-fboss-core
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Core Utilities

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _fboss_repo_core %{_fboss_dir}/arista/core

%define _fboss_target_opt %{buildroot}/opt/fboss/
%define _fboss_target_bin %{_fboss_target_opt}/bin/
%define _fboss_target_lib %{_fboss_target_opt}/lib/
%define _fboss_target_share %{_fboss_target_opt}/share/
%define _fboss_target_systemd %{_fboss_target_share}/systemd/
%define _swtest_samples %{_fboss_target_bin}/fboss/platform/configs/sample/
%define _fboss_target_platform_mappings %{_fboss_target_bin}/fboss/lib/platform_mapping_v2/

%description
This package provides core utilities to run Meta FBOSS OSS on Arista switches.

%install
# Install core binaries.
mkdir -p %{_fboss_target_bin}
cp -rf %{_scratch_dir}/fboss_bins-*/* %{_fboss_target_opt}
# Remove non-executable files from fboss_bins-*/bin
find %{_fboss_target_opt}/bin -maxdepth 1 -type f ! -perm /0111 -exec rm {} \;
find %{_scratch_dir}/build/fboss -maxdepth 1 -type f -executable -exec cp {} %{_fboss_target_opt}/bin \;

# Darwin qsfp config needs to be renamed for fboss_init.sh assumptions to hold
mv %{_fboss_target_share}/qsfp_test_configs/darwin_original.materialized_JSON \
   %{_fboss_target_share}/qsfp_test_configs/darwin.materialized_JSON

# Darwin48v doesn't have configs of its own so copy darwin's configs
cp %{_fboss_target_share}/qsfp_test_configs/darwin.materialized_JSON \
   %{_fboss_target_share}/qsfp_test_configs/darwin48v.materialized_JSON
cp %{_fboss_target_share}/hw_test_configs/darwin.agent.materialized_JSON \
   %{_fboss_target_share}/hw_test_configs/darwin48v.agent.materialized_JSON
cp %{_fboss_target_share}/link_test_configs/darwin.materialized_JSON \
   %{_fboss_target_share}/link_test_configs/darwin48v.materialized_JSON

# Install known unsupported sai hwtest list. It is not packaged by package-fboss.py
mkdir -p %{_fboss_target_share}/_sai_hw_unsupported_tests
cp -r %{_fboss_dir}/fboss/oss/sai_hw_unsupported_tests/* %{_fboss_target_share}/_sai_hw_unsupported_tests

# Copy python thrift libraries
mkdir -p %{_fboss_target_lib}/fb-py-libs
cp -rf %{_scratch_dir}/gen-py %{_fboss_target_lib}/fb-py-libs
cp -rf %{_scratch_dir}/installed/fbthrift/lib/fb-py-libs/thrift_py/thrift/ %{_fboss_target_lib}/fb-py-libs

# Copy arista fboss scripts
cp -f  %{_fboss_repo_core}/scripts/fboss_init.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/run_data_corral_service.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/run_fan_service.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/run_sensor_service.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/run_qsfp_service.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/run_wedge_agent.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/run_sw_agent.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/run_hw_agent.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/run_hw_tests_dnx.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/fboss-state-sync.py %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/cpu-oob-eeprom-util.sh %{_fboss_target_bin}
cp -f  %{_fboss_repo_core}/scripts/switch-to-bmc.sh %{_fboss_target_bin}

# Install utility binaries
cp -f %{_fboss_dir}/arista/psu-upgrade/psu-upgrade %{_fboss_target_bin}

# Install swtest artifacts
mkdir -p %{_swtest_samples}
mkdir -p %{_fboss_target_platform_mappings}
cp -rf %{_fboss_dir}/fboss/platform/configs/sample/* %{_swtest_samples}
cp -rf %{_fboss_dir}/fboss/lib/platform_mapping_v2/platforms %{_fboss_target_platform_mappings}
cp -rf %{_fboss_dir}/fboss/lib/platform_mapping_v2/test %{_fboss_target_platform_mappings}
cp -rf %{_fboss_dir}/fboss/lib/platform_mapping_v2/generated_platform_mappings %{_fboss_target_platform_mappings}

cp -f %{_fboss_repo_core}/scripts/run_sw_tests.sh %{_fboss_target_opt}

# Install thriftctl utility
cp -f %{_fboss_dir}/arista/util/thriftctl/thriftctl.py %{_fboss_target_bin}/thriftctl

# Copy kernel modules
cp -r %{_sai_sdk_dir}/modules %{_fboss_target_lib}

# Copy firmware files
cp -r %{_sai_sdk_dir}/firmwares/* %{_fboss_target_opt}

# Install systemd services.
mkdir -p %{_fboss_target_systemd}
install %{_fboss_repo_core}/systemd/platform_manager.service %{_fboss_target_systemd}
install %{_fboss_repo_core}/systemd/data_corral_service.service %{_fboss_target_systemd}
install %{_fboss_repo_core}/systemd/sensor_service.service %{_fboss_target_systemd}
install %{_fboss_repo_core}/systemd/fan_service.service %{_fboss_target_systemd}
install %{_fboss_repo_core}/systemd/qsfp_service.service %{_fboss_target_systemd}
install %{_fboss_repo_core}/systemd/wedge_agent.service %{_fboss_target_systemd}
install %{_fboss_repo_core}/systemd/fboss_sw_agent.service %{_fboss_target_systemd}
install %{_fboss_repo_core}/systemd/fboss_hw_agent@.service %{_fboss_target_systemd}
install %{_fboss_repo_core}/systemd/rackmon.service %{_fboss_target_systemd}

%files
/opt/fboss/*
