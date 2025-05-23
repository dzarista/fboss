#!/usr/bin/env python3
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import importlib
import os
import subprocess

bh = importlib.import_module("build-helper")

class AristaBuildHelper(bh.BuildHelper):
    def _create_archive(self):
        subprocess.run(
            [
                "tar",
                "--sort=name",
                "--owner=root:0",
                "--group=root:0",
                "--mtime=2000-01-01 00:00:00",
                "-cvf",
                os.path.join(
                    self._output_path, bh.BuildHelper.LIBSAI_IMPL_COMPRESSED_TAR
                ),
                "-C",
                self._output_path,
                "lib",
                "include",
            ]
        )

if __name__ == "__main__":
    args = bh.parse_args()
    AristaBuildHelper(args).run()
