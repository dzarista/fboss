#! /bin/bash

# helper script to test FBOSS live image creation tool

a pj branchpackage FbossTest
cd /src/FbossTest
a p4 edit FbossEdut.py
sed -i "s/rootfs = hwDesc.KERNEL.getKernelTarball( self.linuxKernel )/rootfs = 'fboss_live_image_test.tar'/g" FbossEdut.py
a ws make -p FbossTest
a dut sanitize --os=fbossOss
python3 ptest/FbossOssSanityTest.py
