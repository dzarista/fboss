Name: arista_bsp_kmods
Version: 0.5.0
Release: 1%{?dist}
Summary: Arista kernel modules support

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _kversion %{getenv:KERNEL_SRC}

%define _kmods_build_dir tmp_build_dir/bsp-kmods
%define _drv_destdir %{root}/%{buildroot}/lib/modules/%{_kversion}

%description
This package provides Linux kernel drivers to manage Arista switch devices

%prep
set -x
find %{SOURCEURL0}/%{_kmods_build_dir} -type f -name "*.ko" -exec cp {} . \;

%install
mkdir -p %{_drv_destdir}
cp -f *.ko %{_drv_destdir}

%files
/lib/modules/*