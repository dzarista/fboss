Name: arista-fboss-core
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Core Utilities

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _fboss_build_dir tmp_build_dir/build/fboss
%define _fboss_core_dir fboss.git/arista/core

%define _fboss_target_opt %{root}/%{buildroot}/opt/fboss/
%define _fboss_target_bin %{root}/%{buildroot}/opt/fboss/bin/
%define _fboss_target_share %{root}/%{buildroot}/opt/fboss/share/
%define _fboss_target_systemd %{_fboss_target_share}/systemd/

%description
This package provides core utilities to run Meta FBOSS OSS on Arista switches.

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/tmp_build_dir/fboss_bins-* .
# Remove non-executable files from fboss_bins-*/bin, this trims all the static
# libraries which result in bloat.
find fboss_bins-*/bin -maxdepth 1 -type f ! -perm /0111 -exec rm {} \;
cp -af %{SOURCEURL0}/tmp_build_dir/psu-upgrade .
cp -af %{SOURCEURL0}/tmp_build_dir/sw_test .
cp -af %{SOURCEURL0}/fboss.git/arista/util/thriftctl/thriftctl.py .
cp -af %{SOURCEURL0}/%{_fboss_core_dir}/* .
find %{SOURCEURL0}/%{_fboss_build_dir} -maxdepth 1 -type f -executable -exec cp {} ./fboss_bins-*/bin/ \;

%install
# Install core binaries.
mkdir -p %{_fboss_target_bin}
cp -rf fboss_bins-*/* %{_fboss_target_opt}
# Darwin qsfp config needs to be renamed for fboss_init.sh assumptions to hold
mv %{_fboss_target_share}/qsfp_test_configs/darwin_original.materialized_JSON %{_fboss_target_share}/qsfp_test_configs/darwin.materialized_JSON
cp -f scripts/fboss_init.sh %{_fboss_target_bin}
cp -f scripts/run_data_corral_service.sh %{_fboss_target_bin}
cp -f scripts/run_fan_service.sh %{_fboss_target_bin}
cp -f scripts/run_sensor_service.sh %{_fboss_target_bin}
cp -f scripts/run_qsfp_service.sh %{_fboss_target_bin}
cp -f scripts/run_wedge_agent.sh %{_fboss_target_bin}
cp -f scripts/run_sw_agent.sh %{_fboss_target_bin}
cp -f scripts/run_hw_agent.sh %{_fboss_target_bin}
cp -f scripts/run_hw_tests_dnx.sh %{_fboss_target_bin}
cp -f scripts/fboss-state-sync.py %{_fboss_target_bin}
cp -f scripts/cpu-oob-eeprom-util.sh %{_fboss_target_bin}
cp -f scripts/switch-to-bmc.sh %{_fboss_target_bin}

# Install sw_test files
mkdir -p %{_fboss_target_opt}/sw_test/
cp -rf sw_test/sample/ %{_fboss_target_opt}/sw_test/
cp -f scripts/run_sw_tests.sh %{_fboss_target_opt}/sw_test/

# Install utility binaries
cp -f psu-upgrade/psu-upgrade %{_fboss_target_bin}

# Install thriftctl utility
cp -f thriftctl.py %{_fboss_target_bin}/thriftctl

# Install systemd services.
mkdir -p %{_fboss_target_systemd}
install systemd/platform_manager.service %{_fboss_target_systemd}
install systemd/data_corral_service.service %{_fboss_target_systemd}
install systemd/sensor_service.service %{_fboss_target_systemd}
install systemd/fan_service.service %{_fboss_target_systemd}
install systemd/qsfp_service.service %{_fboss_target_systemd}
install systemd/wedge_agent.service %{_fboss_target_systemd}
install systemd/fboss_sw_agent.service %{_fboss_target_systemd}
install systemd/fboss_hw_agent@.service %{_fboss_target_systemd}
install systemd/rackmon.service %{_fboss_target_systemd}

%files
/opt/fboss/*
