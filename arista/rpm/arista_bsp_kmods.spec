Name: arista_bsp_kmods
Version: 0.5.0
Release: 1%{?dist}
Summary: Arista kernel modules support

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _kversion %{getenv:KERNEL_SRC}

%define _module_src fboss.git/arista/bsp-kmods
%define _drv_destdir %{root}/%{buildroot}/lib/modules/%{_kversion}

%description
This package provides Linux kernel drivers to manage Arista switch devices
This assumes the kernel version in http://dist/storage/fboss/centos8.tar

%prep
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/%{_module_src}/* .

%install
mkdir -p %{_drv_destdir}
cp -f *.ko %{_drv_destdir}

%files
/lib/modules/*