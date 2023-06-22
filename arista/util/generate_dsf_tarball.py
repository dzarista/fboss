# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
import os
import sys
import time

import Tac

# -----------------------------------------------------------------------------------
# NOTE: Ensure the used links and commit hashes are valid

# BMC VERSION
BMC_FW_FILENAME = 'flash-meru-jun13'
BMC_FW_LINK = f'http://dist/openbmc/mfgrelease/meru/20230613/{BMC_FW_FILENAME}'
BMC_COMMIT_HASH = 'da2689d72193865c66d5d74927be64fb02639f68'

# Aboot
ABOOT_FILENAME = 'Aboot-norcal13-13.1.0-32240247.rom'
ABOOT_LINK = f'http://dist/storage/arajeev/{ABOOT_FILENAME}'

# Fairywren CPLD
FWN_CPLD_FILENAME = 'cpld-scd_fwn_p1_m2gl025t.stp'
FWN_CPLD_LINK = f'http://dist/storage/fboss/programmables/{FWN_CPLD_FILENAME}'

# FBOSS
FBOSS_COMMIT_HASH = '632c2d06c77e775c4c24c2feadf17937fc633562'

# apl.facebook
APL_COMMIT_HASH = '632c2d06c77e775c4c24c2feadf17937fc633562'

# Release Notes
RELEASE_NOTES = '''N/A'''

# Known Issues
KNOWN_ISSUES = '''N/A'''

# Test Results
TEST_RESULTS_FILENAME = 'test_results.txt'
TEST_RESULTS_LINK = f'http://dist/storage/alamsi/{TEST_RESULTS_FILENAME}'
# -----------------------------------------------------------------------------------

def createTarball(targetDir):
   print('Creating .tar file...')
   tarFileName = '{}.tar'.format(targetDir)
   Tac.run(['tar', '-cvf', tarFileName, targetDir])
   print('')
   Tac.run(['sha1sum', tarFileName])

def handleBmc(targetDir) -> str:
   Tac.run(['wget', BMC_FW_LINK, '-O', os.path.join(targetDir, BMC_FW_FILENAME)])
   sha1sum = Tac.run(['sha1sum', os.path.join(targetDir, BMC_FW_FILENAME)],
                     stdout=Tac.CAPTURE)
   BMC_README = f'\nBMC Image:\n---------------------\n{sha1sum}'
   BMC_README += f'Commit Hash: {BMC_COMMIT_HASH}\n'

   return BMC_README
    
def handleAboot(targetDir) -> str:
   Tac.run(['wget', ABOOT_LINK, '-O', os.path.join(targetDir, ABOOT_FILENAME)])

   sha1sum = Tac.run(['sha1sum', os.path.join(targetDir, ABOOT_FILENAME)],
                     stdout=Tac.CAPTURE)
   ABOOT_README = f'\nAboot Image:\n---------------------\n{sha1sum}'

   return ABOOT_README

def handleFwnCPLD(targetDir) -> str:
   Tac.run(['wget', FWN_CPLD_LINK, '-O',
            os.path.join(targetDir, FWN_CPLD_FILENAME)])
   sha1sum = Tac.run(['sha1sum', os.path.join(targetDir, FWN_CPLD_FILENAME)],
                     stdout=Tac.CAPTURE)
   FWN_CPLD_README = f'\nFairywren CPLD Image:\n---------------------\n{sha1sum}'

   return FWN_CPLD_README

def packageProgrammables(targetDir) -> str:
   programmablesDir = 'programmables'
   newTargetDir = f'{targetDir}/{programmablesDir}'

   # Create new programmables directory
   Tac.run(['mkdir', newTargetDir])

   README = \
      f'''\n----------------------------------------
      Programmables \n----------------------------------------\n'''

   # BMC
   README += handleBmc(newTargetDir)
   # Aboot
   README += handleAboot(newTargetDir)
   # Fairywren CPLD
   README += handleFwnCPLD(newTargetDir)

   return README

def handleFboss() -> str:
   FBOSS_README = f'\nFBOSS:\n---------------------\n'
   FBOSS_README += f'Commit Hash: {FBOSS_COMMIT_HASH}\n'

   return FBOSS_README

def handleAplFacebook() -> str:
   APL_README = f'\napl.facebook:\n---------------------\n'
   APL_README += f'Commit Hash: {APL_COMMIT_HASH}\n'

   return APL_README

def handleReleaseNotes() -> str:
   RELEASE_NOTES_README = f'\nRelease Notes:\n---------------------\n'
   RELEASE_NOTES_README += f'{RELEASE_NOTES}\n'

   return RELEASE_NOTES_README

def handleKnownIssues() -> str:
   KNOWN_ISSUES_README = f'\nKnown Issues:\n---------------------\n'
   KNOWN_ISSUES_README += f'{KNOWN_ISSUES}\n'

   return KNOWN_ISSUES_README

def handleTestResults(targetDir) -> str:
   Tac.run(['wget', TEST_RESULTS_LINK, '-O', 
            os.path.join(targetDir, TEST_RESULTS_FILENAME)])
   TR_README = '\nTest Results:\n---------------------\n'
   TR_README += f'Find in {targetDir}\{TEST_RESULTS_FILENAME}\n'

   return TR_README

def generateTarball(targetDir, echoReadme=False, createTarFile=False):
   if os.path.exists(targetDir):
      print('targetDir already exists, please delete this directory first.')
      sys.exit(1)

   if os.path.exists(targetDir + '.tar') and createTarFile:
      print('targetDir tarball already exists, please delete this directory first.')
      sys.exit(1)

   Tac.run(['mkdir', targetDir])

   date = time.asctime()
   README = \
      f'''----------------------------------------
      DSF Bundle Summary
      Date: {date}\n----------------------------------------\n'''
      
   # Fboss
   README += handleFboss()

   # apl.facebook
   README += handleAplFacebook()

   # Release Notes
   README += handleReleaseNotes()

   # Known Issues
   README += handleKnownIssues()

   # Test Results
   README += handleTestResults(targetDir)

   # Programmables
   README += packageProgrammables(targetDir)

   with open(os.path.join(targetDir, 'README'), 'w+') as f:
      f.write(README)

   if echoReadme:
      print(README)

   if createTarFile:
      createTarball(targetDir)


def main():
   parser = argparse.ArgumentParser(
      description='''
Generate DSF drop bundle that includes:
Programmables, release notes tracking known issues, testing report, 
commit hashes of apl.facebook and fboss, and OpenBMC version.

e.g To generate DSF-EFT7 directory and tarball
generate_dsf_tarball.py --target-dir DSF-EFT7 --create-tarball

NOTE: This is using the following hardcoded versions:
BMC {}
ABOOT: {}
CPLD: {}
Please update this script if those versions changes'''.format(
         BMC_FW_FILENAME, ABOOT_FILENAME, FWN_CPLD_FILENAME),
      formatter_class=argparse.RawTextHelpFormatter)
   parser.add_argument(
      '--target-dir', required=True,
      help='Target directory name to create tarball with.\n'
      'e.g: --target-dir EOS-EFT-7')
   parser.add_argument(
      '--create-tarball', action='store_true',
      help='create tarball file in addition to directory.')
   parser.add_argument(
      '--show-readme', action='store_true',
      help='print README output to stdout as well.')
   args = parser.parse_args()

   generateTarball(args.target_dir, args.show_readme, args.create_tarball)

if __name__ == "__main__":
   main()
