Name: arista_bsp_kmods
Version: 0.5.0
Release: 1%{?dist}
Summary: Arista kernel modules support

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _kmods_build_dir %{_fboss_dir}/fboss.bsp.arista/bsp-kmods

%description
This package provides Linux kernel drivers to manage Arista switch devices

%prep
set -x
find %{_kmods_build_dir} -type f -name "*.ko" -exec cp {} . \;
find %{_kmods_build_dir} -type f -name "kmods.json" -exec cp {} . \;
find %{_kmods_build_dir} -type f -name "fbsp-remove.sh" -exec cp {} . \;

%define _kversion `modinfo *.ko | grep vermagic | awk 'NR==1{print $2}'`
%define _drv_destdir %{buildroot}/lib/modules/%{_kversion}
%define _bspdir %{buildroot}/usr/local/arista_bsp/%{_kversion}

%install
mkdir -p %{_drv_destdir} %{_bspdir}
cp -f *.ko %{_drv_destdir}
cp -f kmods.json %{_bspdir}
cp -f fbsp-remove.sh %{_bspdir}
chmod 0755 %{_bspdir}/fbsp-remove.sh

%files
/lib/modules/*
/usr/local/arista_bsp/*
