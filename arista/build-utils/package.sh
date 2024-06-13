#!/bin/bash
# Package FBOSS OSS into RPMs. RPMs to build can be specified as input. If not
# RPMs are given, all will be rebuilt.

if [[ ! -f /.dockerenv ]]; then
   echo "Please run this script from within the docker build container."
fi

args=()

while [[ $# -gt 0 ]];
do
   case $1 in
    --kernel)
      if [ "$2" == "4.18" ];
      then
         KERNEL="4.18"
      elif [ "$2" == "5.12" ];
      then
         KERNEL="5.12"
      elif [ "$2" == "5.19" ];
      then
         KERNEL="5.19"
      elif [ "$2" == "6.4" ];
      then
         KERNEL="6.4"
      else
         echo "Unsupported kernel $2, please provide one of 4.18, 5.12, 5.19, or 6.4."
         exit 1
      fi
      shift
      shift
      ;;
    -*|--*)
      echo "Unknown option $arg"
      exit 1
      ;;
    *)
      args+=("$1")
      shift
      ;;
   esac
done

if [ $KERNEL = "4.18" ]; then
   export KERNEL_SRC="4.18.0-408.el8.x86_64"
elif [ $KERNEL = "5.12" ]; then
   export KERNEL_SRC="5.12.0-0_fbk2_3390_g7ecb4ac46d7f"
elif [ $KERNEL = "6.4" ]; then
   export KERNEL_SRC="6.4.3-0_fbk747_rc2_1199_ga95cd85c72c4"
else
   export KERNEL_SRC="5.19.0"
fi

FBOSS_REPO_RPM_DIR="/var/FBOSS/fboss.git/arista/rpm"
FBOSS_RPM_DIR="/var/FBOSS/rpmbuild/RPMS/"
RPM_DIR="/root/rpmbuild/RPMS/x86_64"
RPMS=()
set -ex

mkdir -p "${FBOSS_RPM_DIR}"

# Find the RPMs to build.
if [[ ${#args[@]} -lt 1 ]]; then
   RPMS=($(find "${FBOSS_REPO_RPM_DIR}" -type f -name *.spec))
else
   for rpm in "${args[@]}"; do
      RPMS+=("${FBOSS_REPO_RPM_DIR}/${rpm}.spec")
   done
fi

for rpm in "${RPMS[@]}"; do
   rpmbuild -bb "${rpm}" --define 'root /'
   built_rpm=$(find "${RPM_DIR}" -type f -name "$(basename ${rpm%.*})*")
   cp -f "${built_rpm}" "${FBOSS_RPM_DIR}"
done
