Name: arista-fboss-core
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Core Utilities
Requires: kernel-arista

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _fboss_build_dir tmp_build_dir/build/fboss
%define _fboss_core_dir fboss.git/arista/core

%define _fboss_target_opt %{buildroot}/opt/fboss/
%define _fboss_target_bin %{buildroot}/opt/fboss/bin/
%define _fboss_target_systemd %{buildroot}/opt/fboss/share/systemd/

%description
This package provides core utilities to run Meta FBOSS OSS on Arista switches.

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/tmp_build_dir/fboss_bins-* .
cp -af %{SOURCEURL0}/%{_fboss_core_dir}/* .
find %{SOURCEURL0}/%{_fboss_build_dir} -maxdepth 1 -type f -executable -exec cp {} ./fboss_bins-*/bin/ \;

%install
# Install core binaries.
mkdir -p %{_fboss_target_bin}
cp -rf fboss_bins-*/* %{_fboss_target_opt}
cp -f scripts/fboss_init.sh %{_fboss_target_bin}
cp -f scripts/run_sensor_service.sh %{_fboss_target_bin}
cp -f scripts/run_qsfp_service.sh %{_fboss_target_bin}
cp -f scripts/run_wedge_agent.sh %{_fboss_target_bin}

# Install systemd services.
mkdir -p %{_fboss_target_systemd}
install systemd/data_corral_service.service %{_fboss_target_systemd}
install systemd/sensor_service.service %{_fboss_target_systemd}
install systemd/fan_service.service %{_fboss_target_systemd}
install systemd/qsfp_service.service %{_fboss_target_systemd}
install systemd/wedge_agent.service %{_fboss_target_systemd}
install systemd/rackmon.service %{_fboss_target_systemd}

%files
/opt/fboss/*
