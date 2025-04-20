Name: showtech-arista
Version: 1
Release: 1%{?dist}
Summary: Arista showtech support

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _showtech_build_dir %{_fboss_dir}/fboss.bsp.arista/showtech
%define _destdir %{buildroot}/usr/bin

%description
This package provide utils to collect support information for Arista switch devices

%install
make -C %{_showtech_build_dir} install DESTDIR=%{_destdir}

%files
%{_bindir}/platform-showtech
