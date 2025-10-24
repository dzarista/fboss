Name: arista-fboss-util
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS Utilities

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _showtech_build_dir %{_fboss_dir}/fboss.bsp.arista/showtech
%define _fboss_repo_core %{_fboss_dir}/arista/core
%define _bin_dir %{buildroot}/usr/bin
%define _fboss_target_opt %{buildroot}/opt/fboss/
%define _fboss_target_bin %{_fboss_target_opt}/bin/
%define _fboss_target_share %{_fboss_target_opt}/share/
%define _fboss_target_systemd %{_fboss_target_share}/systemd/

%description
This package provide utils to support FBOSS for Arista switch devices

%install
# Install showtech binary
make -C %{_showtech_build_dir} install DESTDIR=%{_bin_dir}

# Install psu-upgrade binary
mkdir -p %{_fboss_target_bin}
cp -f %{_fboss_dir}/arista/psu-upgrade/psu-upgrade %{_fboss_target_bin}

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

# Install thriftctl utility
cp -f %{_fboss_dir}/arista/util/thriftctl/thriftctl.py %{_fboss_target_bin}/thriftctl

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
%{_bindir}/platform-showtech
/opt/fboss/*

