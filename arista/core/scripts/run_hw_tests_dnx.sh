#!/usr/bin/env bash
function runTest() {
   testNameAndFilter="$1"
   testName=$(echo $testNameAndFilter | sed 's/\(.*\)\(\..*\)/\1/g')
   testCases=$(sai_test-sai_impl-1.11.0 --gtest_filter="$testNameAndFilter" --gtest_list_tests | grep -v "$testName")
   if [ -n "$2" ];
   then
      echo "***************Running test cases"
      for testCase in $testCases; do echo "$testName.$testCase"; done
   fi
   failedTestCases=""
   for testCase in $testCases
   do
      if [ -n "$2" ];
      then
         DPP_DB_PATH=/opt/fboss/share/db sai_test-sai_impl-1.11.0 --config /opt/fboss/share/wedge_agent/platform_wedge_agent.conf --gtest_filter="$testName"."$testCase" --mgmt-if enp1s0
      else
         { 
           DPP_DB_PATH=/opt/fboss/share/db sai_test-sai_impl-1.11.0 --config /opt/fboss/share/wedge_agent/platform_wedge_agent.conf --gtest_filter="$testName"."$testCase" --mgmt-if enp1s0
         } > /dev/null 2>&1
      fi
      if [ $? -ne 0 ]; then
         if [ -z "$2" ];
         then
            echo "$testName.$testCase FAILED"
         fi
         failedTestCases="$failedTestCases$testName.$testCase\n"
      else
         echo "$testName.$testCase PASSED"
      fi
   done
   if [ -n "$failedTestCases" -a -n "$2" ]; then echo -ne "FAILED TEST CASES\n$failedTestCases"; fi
}

if [ -n "$1" ];
then
   runTest "$1" "DEBUG"
else
   # NOTE, these test filters are picked from what is expected to pass on meru400biu from
   # https://github.com/facebook/fboss/blob/main/installer/centos-7-x86_64/run_scripts/run_test.py
   # Voq switch init tests.
   for test in HwVoqSwitchTest.*
   do runTest "$test"
   done
   # Batch A Neighbor tests
   for test in HwNeighborTest/0.*:-*LookupClass HwNeighborTest/2.*:-*LookupClass
   do runTest "$test"
   done
   # Batch A Route tests
   for test in HwRouteTest/0.*:-*Mpls*:*ClassId*:*ClassID* HwRouteTest/1.*:-*Mpls*:*ClassId*:*ClassID*
   do runTest "$test"
   done
   # Batch A Control Plane tests
   for test in HwCoppTest/0.Ipv6LinkLocalMcastToMidPriQ HwCoppTest/0.Ipv6LinkLocalMcastNetworkControlDscpToHighPriQ HwCoppTest/0.L3MTUErrorToLowPriQ HwCoppTest/0.UnresolvedRoutesToLowPriQueue
   do runTest "$test"
   done
   for test in HwPacketSendTest.PortTxEnableTest
   do runTest "$test"
   done
   # Test is stuck and does not pass.
   #for test in HwRxReasonTests.*
   #do runTest "$test"
   #done
   # Batch A Queues Tests
   for test in HwSendPacketToQueueTest.*
   do runTest "$test"
   done
   for test in HwDscpQueueMappingTest.*
   do runTest "$test"
   done
   # Batch A Queues tests - PortBandwidth tests don't have a valid test enumeration in run_test.py yet.
   # Batch A ACL Tests
   for test in HwAclPriorityTest.*:-*AclsChanged*
   do runTest "$test"
   done
   for test in HwAclCounterTest.*
   do runTest "$test"
   done
   for test in SaiAclTableRecreateTests.*
   do runTest "$test"
   done
   for test in HwAclStatTest.*:-*AclStatCreate:*AclStatCreateShared:*AclStatCreateMultiple:*AclStatMultipleActions:*AclStatDeleteShared*:*AclStatDeleteSharedPostWarmBoot:*AclStatRename*:*AclStatModify:*AclStatShuffle:*StatNumberOfCounters:*AclStatChangeCounterType
   do runTest "$test"
   done
fi
