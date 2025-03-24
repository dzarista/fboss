# The rpmbuild macros hardcoded __strip to be /usr/bin/strip.
# Change to /bin/llvm-strip to avoid lto compilation failure.
%define with_clang %{?using_clang: %{using_clang}} %{?!using_clang: 0}
%if %{with_clang}
%define __strip /bin/llvm-strip
%endif

%define has_kver %{?rpm_kernel_version: 1} %{?!rpm_kernel_version: 0}
%if !%{has_kver}
%define rpm_kernel_version %(uname -r)
%endif

%{!?kernel_module_package:%define kernel_module_package %nil}
%{!?kernel_module_package_buildreqs:%define kernel_module_package_buildreqs %nil}

%define debug_package %{nil}
%define kmod_dir /lib/modules/%{rpm_kernel_version}/extra/arista/
%define script_dir /usr/local/arista_bsp/%{rpm_kernel_version}/

Name: arista_bsp_kmods
Summary: Arista BSP (Board Support Package) Kernel Modules
Version: 0.8.0
Release: 1
Vendor: Arista
License: GPLv2
Group: System Environment/Kernel
Source: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-root
BuildRequires: %kernel_module_package_buildreqs rsync tar gcc make kernel-devel rpm-build

%description
The BSP (Board Support Package) of Arista/FBOSS Switches.

The BSP contains the necessary kernel modules/drivers for the FPGAs,
CPLDs, and various I/O controllers in the Arista/FBOSS switches.

%prep
%setup -q -n %{name}-%{version}

%build
export BUILD_KERNEL=%{rpm_kernel_version}
make -C kmods clean
%if %{with_clang}
make CC=clang LD=ld.lld NM=llvm-nm -C kmods
%else
make -C kmods
%endif

%install
install -d %{buildroot}%{kmod_dir}
install -t %{buildroot}%{kmod_dir} kmods/*.ko
install -t %{buildroot}%{kmod_dir} kmods/*/*.ko
install -d %{buildroot}%{script_dir}
install -m755 kmods/scripts/* %{buildroot}%{script_dir}

%clean
rm -rf %{buildroot}

%package -n %{name}-%{rpm_kernel_version}
Summary: Arista BSP (Board Support Package) Kernel Modules
Group: System Environment/Kernel
Provides: %{name}

%description -n %{name}-%{rpm_kernel_version}
The BSP (Board Support Package) of Arista/FBOSS Switches.

The BSP contains the necessary kernel modules/drivers for the FPGAs,
CPLDs, and various I/O controllers in the Arista/FBOSS switches.

%files -n %{name}-%{rpm_kernel_version}
%defattr (-, root, root)
%{kmod_dir}
%{script_dir}*

%post -n %{name}-%{rpm_kernel_version}
/sbin/depmod -a %{rpm_kernel_version}

%postun -n %{name}-%{rpm_kernel_version}
/sbin/depmod -a %{rpm_kernel_version}

%changelog
* Mon Nov 27 2023 Scott Smith <smithscott@meta.com> - 0.7.2-1
- Initial release
