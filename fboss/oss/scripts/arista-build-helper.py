#!/usr/bin/env python3
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

"""
Arguments remapping (This takes precendece over argument description):
  * Repurpose _libsai_impl_path argument to take in already archived tar of 
    libsai_impl and headers
  * Repurpose _experiments_path argument to take in sha256 checksum of the tar
"""

import importlib
import os
import shutil
import subprocess

bh = importlib.import_module("build-helper")

class AristaBuildHelper(bh.BuildHelper):
    def _copy_input_files(self):
        os.makedirs(self._output_path)
    
    def _create_archive(self):
        # Expects archived tar to be passed to _libsai_impl_path
        outputTar = os.path.join(
            self._output_path,
            bh.BuildHelper.LIBSAI_IMPL_COMPRESSED_TAR
        )
        shutil.copy(self._libsai_impl_path, outputTar)

    def _get_csum(self):
        # Expects checksum to be passed to experiments_path
        return self._experiments_path

if __name__ == "__main__":
    args = bh.parse_args()
    AristaBuildHelper(args).run()
