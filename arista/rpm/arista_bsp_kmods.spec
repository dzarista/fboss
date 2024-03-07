Name: arista_bsp_kmods
Version: 0.5.0
Release: 1%{?dist}
Summary: Arista kernel modules support

License: GPLv2
URL: https://github.com/aristanetworks/apl.facebook
Source: %{expand:%%(pwd)}

%define _kversion  $(uname -r)

%description
This package provides Linux kernel drivers to manage Arista switch devices
This assumes the kernel version in http://dist/storage/fboss/centos8.tar

%prep
# clean out old files
set -x
find . -mindepth 1 -delete
cp -af %{SOURCEURL0}/. .

%build
make build-drivers \
   KVERSION=%{_kversion}

%install
make install-drivers \
   DESTDIR=%{buildroot} \
   KVERSION=%{_kversion}

%files
%license LICENSE
/lib/modules/*