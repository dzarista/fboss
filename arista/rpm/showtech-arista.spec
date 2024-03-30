Name: showtech-arista
Version: 1
Release: 1%{?dist}
Summary: Arista showtech support

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss
Source: %{expand:%%(pwd)}

%define _showtech_src fboss.git/arista/showtech
%define _showtech_build_dir tmp_build_dir/showtech
%define _destdir %{root}/%{buildroot}/usr/bin

%description
This package provide utils to collect support information for Arista switch devices

%prep
# clean out old files
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/%{_showtech_src}/* .
cp -af %{SOURCEURL0}/%{_showtech_build_dir}/* .

%install
make install DESTDIR=%{_destdir}

%files
%{_bindir}/platform-showtech
