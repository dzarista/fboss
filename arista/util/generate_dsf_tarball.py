# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
import os
import subprocess
import sys
import time

# -----------------------------------------------------------------------------------
# NOTE: Ensure the used links and commit hashes are valid

# BMC VERSION
BMC_REPO = 'https://github.com/aristanetworks/arista-openbmc.git'
BMC_FW_FILENAME = 'flash-meru-jun13'
BMC_FW_LINK = f'http://dist/openbmc/mfgrelease/meru/20230613/{BMC_FW_FILENAME}'
BMC_COMMIT_HASH = 'e7a7f0e0ac675e8c9bd02f125b5ad291946496d8'

# Aboot
ABOOT_FILENAME = 'Aboot-norcal13-13.1.0-32240247.rom'
ABOOT_LINK = f'http://dist/storage/arajeev/{ABOOT_FILENAME}'

# Fairywren CPLD
FWN_CPLD_FILENAME = 'cpld-scd_fwn_p1_m2gl025t.stp'
FWN_CPLD_LINK = f'http://dist/storage/fboss/programmables/{FWN_CPLD_FILENAME}'

# FBOSS
FBOSS_REPO = 'https://github.com/aristanetworks/arista-fboss.git'
FBOSS_COMMIT_HASH = '632c2d06c77e775c4c24c2feadf17937fc633562'

# apl.facebook
APL_REPO = 'https://github.com/aristanetworks/apl.facebook'
APL_COMMIT_HASH = '176b7c87ea31b5ce23dd7611104a8c11bbe7c3ff'

# Release Notes
RELEASE_NOTES = '''N/A'''

# Known Issues
KNOWN_ISSUES = '''N/A'''

# Test Results
TEST_RESULTS_FILENAME = 'test_results.txt'
TEST_RESULTS_LINK = f'http://dist/storage/alamsi/{TEST_RESULTS_FILENAME}'
# -----------------------------------------------------------------------------------

def runCmd(cmd: list, captureOutput = False):
   if captureOutput:
      return subprocess.run(cmd, capture_output=True, text=True).stdout.strip('\n')
   subprocess.run(cmd)

def cloneRepo(repo, dest):
   try:
      subprocess.check_call(['git', 'clone', repo, dest])
      print(f'Repo {repo} has been cloned to {dest}')
   except subprocess.CalledProcessError as e:
      print(f'Error occurred while cloning the repo: {str(e)}')

def removeRepo(dest):
   if not os.path.exists(dest):
      raise ValueError(f'No repo found at {dest}')

   try:
      runCmd(['rm', '-rf', dest])
      print(f'Repo at {dest} has been cleaned')
   except OSError as e:
      print(f'Error occurred when cleaning the {dest} repo: {str(e)}')

def verifyCommit(repoDir, hash):
   try:
      subprocess.check_output(['git', '-C', f'{repoDir}/', 'cat-file', '-t', hash])
      return True
   except subprocess.CalledProcessError:
      return False

def verifyInput():
   # Verify BMC commit hash
   print("Verifying commit hashes...")

   openbmcDest = 'OpenBmc'
   cloneRepo(BMC_REPO, openbmcDest)
   if not verifyCommit(openbmcDest, BMC_COMMIT_HASH):
      removeRepo(openbmcDest)
      print(f'Openbmc commit hash {BMC_COMMIT_HASH} is invalid')
      return False
   print('OpenBmc commit hash is valid!')
   removeRepo(openbmcDest)

   fbossDest = 'fboss'
   cloneRepo(FBOSS_REPO, fbossDest)
   if not verifyCommit(fbossDest, FBOSS_COMMIT_HASH):
      removeRepo(fbossDest)
      print(f'Fboss commit hash {FBOSS_COMMIT_HASH} is invalid')
      return False
   print('fboss commit hash is valid!')
   removeRepo(fbossDest)

   aplDest = 'apl'
   cloneRepo(APL_REPO, aplDest)
   if not verifyCommit(aplDest, APL_COMMIT_HASH):
      removeRepo(aplDest)
      print(f'apl.facebook commit hash {APL_COMMIT_HASH} is invalid')
      return False
   print('apl.facebook commit hash is valid!')
   removeRepo(aplDest)

   return True

def createTarball(targetDir):
   print('Creating .tar file...\n')
   tarFileName = f'{targetDir}.tar'
   runCmd(['tar', '-cvf', tarFileName, targetDir])
   runCmd(['sha1sum', tarFileName])

def handleBmc(targetDir) -> str:
   runCmd(['wget', BMC_FW_LINK, '-O', os.path.join(targetDir, BMC_FW_FILENAME)])
   sha1sum = runCmd(['sha1sum', os.path.join(targetDir, BMC_FW_FILENAME)], True)

   BMC_README = f'''
BMC Image:
---------------------
{sha1sum}
Commit Hash: {BMC_COMMIT_HASH}
'''

   return BMC_README
    
def handleAboot(targetDir) -> str:
   runCmd(['wget', ABOOT_LINK, '-O', os.path.join(targetDir, ABOOT_FILENAME)])
   sha1sum = runCmd(['sha1sum', os.path.join(targetDir, ABOOT_FILENAME)], True)

   ABOOT_README = f'''
Aboot Image:
---------------------
{sha1sum}
'''

   return ABOOT_README

def handleFwnCPLD(targetDir) -> str:
   runCmd(['wget', FWN_CPLD_LINK, '-O', os.path.join(targetDir, FWN_CPLD_FILENAME)])
   sha1sum = runCmd(['sha1sum', os.path.join(targetDir, FWN_CPLD_FILENAME)], True)

   FWN_CPLD_README = f'''
Fairywren CPLD Image:
---------------------
{sha1sum}
'''

   return FWN_CPLD_README

def packageProgrammables(targetDir) -> str:
   programmablesDir = 'programmables'
   newTargetDir = f'{targetDir}/{programmablesDir}'

   # Create new programmables directory
   runCmd(['mkdir', newTargetDir])

   README = '''
----------------------------------------
   Programmables
----------------------------------------
'''

   # BMC
   README += handleBmc(newTargetDir)
   # Aboot
   README += handleAboot(newTargetDir)
   # Fairywren CPLD
   README += handleFwnCPLD(newTargetDir)

   return README

def handleFboss() -> str:
   FBOSS_README = f'''
FBOSS:
---------------------
Commit Hash: {FBOSS_COMMIT_HASH}
'''

   return FBOSS_README

def handleAplFacebook() -> str:
   APL_README = f'''
apl.facebook:
---------------------
Commit Hash: {APL_COMMIT_HASH}
'''

   return APL_README

def handleReleaseNotes() -> str:
   RELEASE_NOTES_README = f'''
Release Notes:
---------------------
{RELEASE_NOTES}
'''

   return RELEASE_NOTES_README

def handleKnownIssues() -> str:
   KNOWN_ISSUES_README = f'''
Known Issues:
---------------------
{KNOWN_ISSUES}
'''

   return KNOWN_ISSUES_README

def handleTestResults(targetDir) -> str:
   runCmd(['wget', TEST_RESULTS_LINK, '-O', 
            os.path.join(targetDir, TEST_RESULTS_FILENAME)])
   
   TR_README = f'''
Test Results:
---------------------
Find in {targetDir}\{TEST_RESULTS_FILENAME}
'''

   return TR_README

def generateTarball(targetDir, echoReadme=False, createTarFile=False):
   if os.path.exists(targetDir):
      print(f'./{targetDir} already exists, please delete this directory first.')
      sys.exit(1)

   if os.path.exists(targetDir + '.tar') and createTarFile:
      print(f'./{targetDir}.tar already exists, please delete it first.')
      sys.exit(1)

   if not verifyInput():
      return

   runCmd(['mkdir', targetDir])

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
      description=f'''
Generate DSF drop bundle that includes:
Programmables, release notes tracking known issues, testing report, 
commit hashes of apl.facebook and fboss, and OpenBMC version.

e.g To generate DSF-EFT7 directory and tarball
generate_dsf_tarball.py --target-dir DSF-EFT7 --create-tarball

NOTE: This is using the following hardcoded versions:
BMC: {BMC_FW_FILENAME}
ABOOT: {ABOOT_FILENAME}
CPLD: {FWN_CPLD_FILENAME}
Please update this script if those versions changes''',
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
