Name: arista-fboss-core
Version: 1
Release: 1%{?dist}
Summary: Arista FBOSS OSS Core Utilities

License: GPLv2
URL: https://github.com/aristanetworks/arista-fboss

%define _fboss_target_opt %{buildroot}/opt/fboss/
%define _fboss_target_bin %{_fboss_target_opt}/bin/
%define _fboss_target_lib %{_fboss_target_opt}/lib/
%define _fboss_target_share %{_fboss_target_opt}/share/

%description
This package provides core utilities to run Meta FBOSS OSS on Arista switches.

%install
# Install core binaries.
pushd %{_fboss_dir}
mkdir -p %{_fboss_target_opt}
rm -rf %{_scratch_dir}/fboss_bins-1*
fboss/oss/scripts/package-fboss.py --scratch-path %{_scratch_dir}
cp -rf %{_scratch_dir}/fboss_bins-1*/* %{_fboss_target_opt}
echo arista-fboss@${SRC_0:-$(git -c safe.directory=$PWD rev-parse HEAD)} > \
   %{_fboss_target_opt}/arista-fboss-version
popd

# Remove non-executable files from fboss_bins-*/bin
find %{_fboss_target_opt}/bin -maxdepth 1 -type f ! -perm /0111 -exec rm {} \;
find %{_scratch_dir}/build/fboss -maxdepth 1 -type f -executable -exec cp {} %{_fboss_target_opt}/bin \;

# Darwin qsfp config needs to be renamed for fboss_init.sh assumptions to hold
mv %{_fboss_target_share}/qsfp_test_configs/darwin_original.materialized_JSON \
   %{_fboss_target_share}/qsfp_test_configs/darwin.materialized_JSON

# Darwin48v doesn't have configs of its own so copy darwin's configs
cp %{_fboss_target_share}/qsfp_test_configs/darwin.materialized_JSON \
   %{_fboss_target_share}/qsfp_test_configs/darwin48v.materialized_JSON
cp %{_fboss_target_share}/hw_test_configs/darwin.agent.materialized_JSON \
   %{_fboss_target_share}/hw_test_configs/darwin48v.agent.materialized_JSON
cp %{_fboss_target_share}/link_test_configs/darwin.materialized_JSON \
   %{_fboss_target_share}/link_test_configs/darwin48v.materialized_JSON

# Install known unsupported sai hwtest list. It is not packaged by package-fboss.py
mkdir -p %{_fboss_target_share}/_sai_hw_unsupported_tests
cp -r %{_fboss_dir}/fboss/oss/sai_hw_unsupported_tests/* %{_fboss_target_share}/_sai_hw_unsupported_tests

# Copy python thrift libraries
mkdir -p %{_fboss_target_lib}/fb-py-libs
cp -rf %{_scratch_dir}/gen-py %{_fboss_target_lib}/fb-py-libs
cp -rf %{_scratch_dir}/installed/fbthrift/lib/fb-py-libs/thrift_py/thrift/ %{_fboss_target_lib}/fb-py-libs

# Copy firmware files
cp -r %{_sai_sdk_dir}/firmwares/* %{_fboss_target_opt}

# Copy DB files
cp -rf %{_sai_sdk_dir}/db %{_fboss_target_share}/

# Cookie file to find where sdk kmods will be located
echo %{_sai_sdk_dir} > %{_fboss_target_bin}/.sdkkmoddir

%files
/opt/fboss/*
