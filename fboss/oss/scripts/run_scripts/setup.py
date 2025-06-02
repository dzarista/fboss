#!/usr/bin/env python3
# Copyright 2004-present Facebook. All Rights Reserved.

import argparse
import os
import platform
import shutil
import subprocess
import sys

from run_test import setup_fboss_env


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reload", help="Clear setup config, and reload", action="store_true"
    )
    return parser.parse_args()


class SetupFboss:
    FRUID_CONF = "fruid.json"
    FRUID_DIR_PATH = "/var/facebook/fboss"
    FRUID_FULL_PATH = os.path.join(FRUID_DIR_PATH, FRUID_CONF)

    BDE_CONF = "bde.conf"
    BDE_CONF_FULL_PATH = os.path.join("/etc/modprobe.d", BDE_CONF)

    USER_BDE = "linux-user-bde"
    KERNEL_BDE = "linux-kernel-bde"
    KERNEL_NGBDE = "linux_ngbde"

    USER_BDE_KO = USER_BDE + ".ko"
    KERNEL_BDE_KO = KERNEL_BDE + ".ko"
    KERNEL_NGBDE_KO = KERNEL_NGBDE + ".ko"

    KMOD_FULL_PATH = os.path.join("/lib/modules/" + platform.uname().release)
    USER_BDE_KO_FULL_PATH = os.path.join(KMOD_FULL_PATH, USER_BDE_KO)
    KERNEL_BDE_KO_FULL_PATH = os.path.join(KMOD_FULL_PATH, KERNEL_BDE_KO)
    KERNEL_NGBDE_KO_FULL_PATH = os.path.join(KMOD_FULL_PATH, KERNEL_NGBDE_KO)

    # Unfortunately, lsmod prints _ (underscore) for - (dash)
    LSMOD_USER_BDE = "linux_user_bde"
    LSMOD_KERNEL_BDE = "linux_kernel_bde"
    LSMOD_KERNEL_NGBDE = "linux_ngbde"

    SRC_USER_BDE_KO_FULL_PATH = os.path.join(os.environ["FBOSS_KMODS"], USER_BDE_KO)
    SRC_KERNEL_BDE_KO_FULL_PATH = os.path.join(os.environ["FBOSS_KMODS"], KERNEL_BDE_KO)
    SRC_KERNEL_NGBDE_KO_FULL_PATH = os.path.join(os.environ["FBOSS_KMODS"], KERNEL_NGBDE_KO)

    useNgbde = False

    TH = "th"
    TH3 = "th3"
    J2CP = "j2cp"
    ### ARISTA START ###
    J3 = "j3"
    J3B = "j3b"
    J3C = "j3c"
    R3 = "r3"
    TH5 = "th5"
    ### ARISTA END ###

    def __init__(self):
        output = subprocess.check_output(["lspci"]).decode("utf-8").split("\n")

        if [x for x in output if "Broadcom" in x and "BCM56960" in x]:
            self.src_fruid_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.TH, SetupFboss.FRUID_CONF]
            )
            self.src_bde_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.TH, SetupFboss.BDE_CONF]
            )

        elif [x for x in output if "Broadcom" in x and "b980" in x]:
            self.src_fruid_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.TH3, SetupFboss.FRUID_CONF]
            )
            self.src_bde_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.TH3, SetupFboss.BDE_CONF]
            )

        elif [x for x in output if "Broadcom" in x and "8850" in x]:
            self.src_fruid_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.J2CP, SetupFboss.FRUID_CONF]
            )
            self.src_bde_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.J2CP, SetupFboss.BDE_CONF]
            )
    ### ARISTA START ###
        # TODO: Add j3+/j3ai+
        elif [x for x in output if "Broadcom" in x and "8860" in x and "rev 11" in x]:
            self.src_fruid_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.J3B, SetupFboss.FRUID_CONF]
            )
            self.src_bde_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.J3, SetupFboss.BDE_CONF]
            )
        elif [x for x in output if "Broadcom" in x and "8890" in x]:
            self.src_fruid_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.J3, SetupFboss.FRUID_CONF]
            )
            self.src_bde_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.J3, SetupFboss.BDE_CONF]
            )
        elif [x for x in output if "Broadcom" in x and "8920" in x]:
            self.src_fruid_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.R3, SetupFboss.FRUID_CONF]
            )
            self.src_bde_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.R3, SetupFboss.BDE_CONF]
            )
        elif [x for x in output if "Broadcom" in x and "8900" in x]:
            self.src_fruid_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.TH5, SetupFboss.FRUID_CONF]
            )
            self.src_bde_full_path = os.path.join(
                *[os.environ["FBOSS_DATA"], SetupFboss.TH5, SetupFboss.BDE_CONF]
            )
    ### ARISTA END ###

        self.useNgbde = "linux_ngbde" in open(self.src_bde_full_path).read()

    def _cleanup_old_setup(self):
        if os.path.exists(SetupFboss.FRUID_FULL_PATH):
            ### ARISTA START ###
            pass # os.remove(SetupFboss.FRUID_FULL_PATH)
            ### ARISTA END ###

        if os.path.exists(SetupFboss.BDE_CONF_FULL_PATH):
            os.remove(SetupFboss.BDE_CONF_FULL_PATH)

        if self.useNgbde:
            subprocess.run(["modprobe", "-r", SetupFboss.KERNEL_NGBDE])
        else:
            subprocess.run(["modprobe", "-r", SetupFboss.KERNEL_BDE])
            subprocess.run(["modprobe", "-r", SetupFboss.USER_BDE])

        if os.path.exists(SetupFboss.USER_BDE_KO_FULL_PATH):
            os.remove(SetupFboss.USER_BDE_KO_FULL_PATH)

        if os.path.exists(SetupFboss.KERNEL_BDE_KO_FULL_PATH):
            os.remove(SetupFboss.KERNEL_BDE_KO_FULL_PATH)

        if os.path.exists(SetupFboss.KERNEL_NGBDE_KO_FULL_PATH):
            os.remove(SetupFboss.KERNEL_NGBDE_KO_FULL_PATH)

    def _copy_configs(self):
        if not os.path.exists(SetupFboss.FRUID_FULL_PATH):
            if not os.path.exists(SetupFboss.FRUID_DIR_PATH):
                os.makedirs(SetupFboss.FRUID_DIR_PATH)

            shutil.copy(self.src_fruid_full_path, SetupFboss.FRUID_FULL_PATH)

        if not os.path.exists(SetupFboss.BDE_CONF_FULL_PATH):
            os.path.join("/tmp", "target")
            shutil.copy(self.src_bde_full_path, SetupFboss.BDE_CONF_FULL_PATH)

    def _link_kmods(self):
        new_kmod = False

        if (self.useNgbde and
            not os.path.exists(SetupFboss.KERNEL_NGBDE_KO_FULL_PATH)):
            subprocess.run(
                [
                    "ln",
                    "-s",
                    SetupFboss.SRC_KERNEL_NGBDE_KO_FULL_PATH,
                    "-t",
                    SetupFboss.KMOD_FULL_PATH,
                ]
            )
            new_kmod = True
        else:
            if not os.path.exists(SetupFboss.USER_BDE_KO_FULL_PATH):
                subprocess.run(
                    [
                        "ln",
                        "-s",
                        SetupFboss.SRC_USER_BDE_KO_FULL_PATH,
                        "-t",
                        SetupFboss.KMOD_FULL_PATH,
                    ]
                )
                new_kmod = True

            if not os.path.exists(SetupFboss.KERNEL_BDE_KO_FULL_PATH):
                subprocess.run(
                    [
                        "ln",
                        "-s",
                        SetupFboss.SRC_KERNEL_BDE_KO_FULL_PATH,
                        "-t",
                        SetupFboss.KMOD_FULL_PATH,
                    ]
                )
                new_kmod = True

        if new_kmod:
            subprocess.run(["depmod", "-a"])

    def _load_kmods(self):
        output = subprocess.check_output(["lsmod"]).decode("utf-8").split("\n")

        if (self.useNgbde and
            not [x for x in output if SetupFboss.LSMOD_KERNEL_NGBDE in x]):
            subprocess.run(["modprobe", SetupFboss.KERNEL_NGBDE])
        else:
            if not [x for x in output if SetupFboss.LSMOD_USER_BDE in x]:
                subprocess.run(["modprobe", SetupFboss.USER_BDE])
            if not [x for x in output if SetupFboss.LSMOD_KERNEL_BDE in x]:
                subprocess.run(["modprobe", SetupFboss.KERNEL_BDE])

    def run(self, args):
        if args.reload:
            self._cleanup_old_setup()

        self._copy_configs()
        self._link_kmods()
        self._load_kmods()


if __name__ == "__main__":
    # Set env variables for FBOSS
    setup_fboss_env()
    print(f"Running setup.py with FBOSS={os.environ['FBOSS']}")

    args = parse_args()
    SetupFboss().run(args)
