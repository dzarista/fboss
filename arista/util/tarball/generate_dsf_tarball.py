# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

# ===================================================================================
# This script generates an EFT tarball for the Distributed Switch Fabric (DSF)
# platforms Viper and Whistler. Please see the README.md file in this directory
# for detailed instructions.
# ===================================================================================

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import tempfile

def runCmd(cmd: list, captureOutput = False):
   if captureOutput:
      return subprocess.run(cmd, capture_output=True, text=True).stdout.strip('\n')
   subprocess.run(cmd)

# ===================================================================================
# The ConfigElement base class and all of its subclasses model elements that can
# appear in the DSF bundle configuration JSON file. The base class defines two
# abstract methods that must be implemented by the subclasses; these methods are:
#
# 1) install: this method installs the ConfigElement's files into the correct
#             subdirectory of the target directory that will be compressed into
#             the final tarball.
#
# 2) readmeStr: this method returns a string containing a section of the tarball
#               README for the ConfigElement.
#
# With these methods, every ConfigElement subclass tells the main function how to
# install and document the information contained in the JSON config. Additionally,
# every ConfigElement subclass is expected to validate the data in its fields,
# throwing AssertionErrors if fields are missing.
# ===================================================================================

class ConfigElement:
   def install(self, targetDir):
      raise NotImplementedError

   def readmeStr(self):
      raise NotImplementedError

class ReleaseNotes(ConfigElement):
   def __init__(self, name, notesFile):
      self.name = name
      self.notesFile = notesFile
      assert self.name, 'ReleaseNotes is missing field name'
      assert self.notesFile, 'ReleaseNotes is missing field notesFile'
      assert os.path.isfile(self.notesFile), (
            f'ReleaseNotes notesFile {notesFile} not found'
      )

   def __eq__(self, other):
      if isinstance(other, ReleaseNotes):
         return self.name == other.name
      return False

   def install(self, targetDir):
      # ReleaseNotes only go in the README.
      pass

   def readmeStr(self):
      raise NotImplementedError

class LatestReleaseNotes(ReleaseNotes):
   def readmeStr(self):
      with open(self.notesFile) as f:
         content = f.read().strip()
         return ( '\nRelease Notes:'
                  '\n-------------------------------'
                  f'\n{content}\n\n' )

class PastReleaseNotes(ReleaseNotes):
   def readmeStr(self):
      with open(self.notesFile) as f:
         content = f.read().strip()
         return ( f'\n{self.name}:'
                  '\n-----------------------'
                  f'\n{content}\n' )

class KnownIssuesFile(ConfigElement):
   def __init__(self, filename):
      self.filename = filename
      assert os.path.isfile(self.filename), (
            f'KnownIssuesFile {filename} not found'
      )

   def install(self, targetDir):
      # KnownIssuesFile only goes in the README.
      pass

   def readmeStr(self):
      with open(self.filename) as f:
         content = f.read().strip()
         return ( '\nKnown Issues:'
                  '\n-------------------------------'
                  f'\n{content}\n\n' )

class Patch(ConfigElement):
   def __init__(self, name, patchFile, instructionsFile):
      self.name = name
      self.patchFile = patchFile
      self.instructionsFile = instructionsFile
      assert self.name, 'Patch is missing field name'
      assert self.patchFile, 'Patch is missing field patchFile'
      assert os.path.isfile(self.patchFile) or os.path.isdir(self.patchFile), (
         f'Patch patchFile {patchFile} not found'
      )
      assert self.instructionsFile, 'Patch is missing field instructionsFile'
      assert os.path.isfile(self.instructionsFile), (
            f'Patch instructionsFile {instructionsFile} not found'
      )
      self.patchFileIsDir = os.path.isdir(self.patchFile)

   def install(self, targetDir):
      destDir = os.path.join(targetDir, os.path.basename(self.patchFile))
      if self.patchFileIsDir:
         shutil.copytree(self.patchFile, destDir)
      else:
         shutil.copyfile(self.patchFile, destDir)

   def readmeStr(self):
      with open(self.instructionsFile) as f:
         content = f.read().strip()
         return ( f'\n{self.name}:'
                  '\n----------'
                  f'\n{content}\n' )

class Programmable(ConfigElement):
   def __init__(self, name, imageFile):
      self.name = name
      self.imageFile = imageFile
      assert self.name, 'Programmable is missing field name'
      assert self.imageFile, 'Programmable is missing field imageFile'
      assert os.path.isfile(self.imageFile), (
            f'Programmable imageFile {imageFile} not found'
      )
      self.destFile = None

   def install(self, targetDir):
      self.destFile = os.path.join(targetDir, os.path.basename(self.imageFile))
      shutil.copyfile(self.imageFile, self.destFile)

   def readmeStr(self):
      sha1sum = runCmd(['sha1sum', self.destFile], True)
      return ( f'\n{self.name}:'
               '\n-------------------------------'
               f'\n{sha1sum}\n' )

class Repo(ConfigElement):
   def __init__(self, name, url, branch, commitHash, note):
      self.name = name
      self.url = url
      self.branch = branch
      self.commitHash = commitHash
      self.note = note or ''
      assert self.name, 'Repo is missing field name'
      assert self.url, 'Repo is missing field url'
      assert self.branch, 'Repo is missing field branch'
      assert self.commitHash, 'Repo is missing field commitHash'

      with tempfile.TemporaryDirectory() as repoWorkDir: 
         repoSubDir = os.path.join(
               repoWorkDir,
               f'{"".join(self.name.split())}_repo'
         )

         # Make sure the repo can be cloned.
         try:
            subprocess.check_call(['git', 'clone', self.url, repoSubDir])
         except subprocess.CalledProcessError as e:
            print(f'Error cloning repo {self.name}:\n{str(e)}')
            sys.exit(1)

         # Verify that the commit hash exists.
         try:
            subprocess.check_output(
                  ['git', '-C', f'{repoSubDir}/', 'cat-file', '-t', self.commitHash]
            )
         except subprocess.CalledProcessError as e:
            print(f'Invalid commit hash {self.commitHash} for repo {self.name}:\n'
                  f'{str(e)}')
            sys.exit(1)

   def install(self, targetDir):
      # Repos only go in the README.
      pass

   def readmeStr(self):
      repoName = os.path.basename(self.url).strip('.git')
      readme = ( '\n----------------------------------------'
                 f'\n   {self.name}'
                 '\n----------------------------------------'
                 f'\n\n{repoName} ({self.branch} branch):'
                 '\n-------------------------------'
                 f'\nCommit Hash: {self.commitHash}' )
      if self.note:
         readme += f'\n\n{self.note}\n\n'
      else:
         readme += '\n\n'
      return readme

class TestResults(ConfigElement):
   def __init__(self, name, resultsFile):
      self.name = name
      self.resultsFile = resultsFile
      assert self.name, 'TestResults is missing field name'
      assert self.resultsFile, 'TestResults is missing field resultsFile'
      assert os.path.isfile(self.resultsFile), (
            f'TestResults resultsFile {resultsFile} not found'
      )

   def install(self, targetDir):
      shutil.copyfile(
            self.resultsFile,
            os.path.join(targetDir, os.path.basename(self.resultsFile))
      )

   def readmeStr(self):
      pass

class DsfBundleConfig:
   def __init__(self, configFile):
      self.configFile = configFile
      self.configJson = {}
      self.latestReleaseNotes = None
      self.pastReleaseNotes = []
      self.knownIssuesFile = None
      self.patches = []
      self.programmables = []
      self.repos = []
      self.testResults = []

   def load(self):
      try:
         with open(self.configFile) as f:
            self.configJson = json.load(f)
      except OSError as e:
         print(f'Unable to open config file {self.configFile}:\n{str(e)}')
         sys.exit(1)
      except ValueError as e:
         print(f'Unable to parse config file {self.configFile}:\n{str(e)}')
         sys.exit(1)

      # Config classes will do all validation during __init__.
      try:
         latestReleaseNotes = self.configJson.get('latestReleaseNotes')
         if not latestReleaseNotes:
            print('latestReleaseNotes must be provided in bundle config JSON')
            sys.exit(1)
         self.latestReleaseNotes = LatestReleaseNotes(
               latestReleaseNotes.get('name'),
               latestReleaseNotes.get('notesFile')
         )

         self.pastReleaseNotes = [
               PastReleaseNotes(r.get('name'), r.get('notesFile'))
               for r in self.configJson.get('pastReleaseNotes', [])
         ]

         knownIssuesFile = self.configJson.get('knownIssuesFile')
         if knownIssuesFile:
            self.knownIssuesFile = KnownIssuesFile(knownIssuesFile)

         self.patches = [
               Patch(p.get('name'), p.get('patchFile'), p.get('instructionsFile'))
               for p in self.configJson.get('patches', [])
         ]
         self.programmables = [
               Programmable(p.get('name'), p.get('imageFile'))
               for p in self.configJson.get('programmables', [])
         ]
         self.repos = [
               Repo(r.get('name'), r.get('url'), r.get('branch'),
                    r.get('commitHash'), r.get('note'))
               for r in self.configJson.get('repos', [])
         ]
         self.testResults = [
               TestResults(t.get('name'), t.get('resultsFile'))
               for t in self.configJson.get('testResults', [])
         ]
      except AssertionError as e:
         print(f'Error parsing config JSON:\n{str(e)}')
         sys.exit(1)

def createTarball(targetDir):
   print('Creating .tar.gz file...\n')
   tarFileName = f'{targetDir}.tar.gz'
   runCmd(['tar', '-zcvf', tarFileName, targetDir])
   runCmd(['sha1sum', tarFileName])

def generateTarball(configFile, targetDir, echoReadme=False, createTarFile=False):
   if os.path.exists(targetDir):
      print(f'./{targetDir} already exists, please delete this directory first.')
      sys.exit(1)

   if os.path.exists(targetDir + '.tar') and createTarFile:
      print(f'./{targetDir}.tar already exists, please delete it first.')
      sys.exit(1)

   config = DsfBundleConfig(configFile)
   config.load()

   os.mkdir(targetDir)

   date = time.asctime()
   readme = (
      f'''----------------------------------------
      DSF EFT Bundle Summary
      Date: {date}\n----------------------------------------\n\n'''
   )

   # Release Notes
   readme += config.latestReleaseNotes.readmeStr()

   # Known Issues
   if config.knownIssuesFile:
      readme += config.knownIssuesFile.readmeStr()

   # Repos
   for repo in config.repos:
      readme += repo.readmeStr()

   # Patches
   if config.patches:
      patchesDir = os.path.join(targetDir, 'patches')
      os.mkdir(patchesDir)
      for p in config.patches:
         p.install(patchesDir)
      patchFilenameStrs = []
      for p in config.patches:
         patchFileInTarball = os.path.join(patchesDir, os.path.basename(p.patchFile))
         patchFilenameStrs.append(f'- {patchFileInTarball}')
         if p.patchFileIsDir:
            for pFile in os.listdir(p.patchFile):
               patchFilenameStrs.append(
                     f'  - {os.path.join(patchFileInTarball, pFile)}'
               )

      readme += ( '\n----------------------------------------'
                  '\n   Patches'
                  '\n----------------------------------------'
                  '\n\nThe following patches are included in this bundle:\n' +
                  '\n'.join(patchFilenameStrs) +
                  '\n\nInstructions:'
                  '\n-------------------------------\n' +
                  ''.join(p.readmeStr() for p in config.patches) +
                  '\n' )

   # Programmables
   if config.programmables:
      programmablesDir = os.path.join(targetDir, 'programmables')
      os.mkdir(programmablesDir)
      for p in config.programmables:
         p.install(programmablesDir)
      readme += ( '\n----------------------------------------'
                  '\n   Programmables'
                  '\n----------------------------------------\n' +
                  ''.join(p.readmeStr() for p in config.programmables) +
                  '\n')

   # Test Results
   if config.testResults:
      resultsDir = os.path.join(targetDir, 'test_results')
      os.mkdir(resultsDir)
      resultFilenames = [
            os.path.join(resultsDir, os.path.basename(p.resultsFile))
            for tr in config.testResults
      ]

      readme += ( '\n----------------------------------------'
                  '\n   Test Results'
                  '\n----------------------------------------'
                  '\n\nThe following test results are included in this bundle:' +
                  '\n'.join(f'- {r}' for r in resultFilenames) +
                  '\n\n' )

   # Past Release Notes
   if config.pastReleaseNotes:
      readme += ( '\n----------------------------------------'
                  '\n   Past Releases'
                  '\n----------------------------------------\n' +
                  ''.join(prn.readmeStr() for prn in config.pastReleaseNotes) +
                  '\n' )

   # Footer
   readme += ( '\nNOTE: The contents of this package are for Meta use only'
               '\nand should not be open sourced.'
               '\n\nContact Arista if there are questions.' )
   
   with open(os.path.join(targetDir, 'README'), 'w+') as f:
      f.write(readme)

   if echoReadme:
      print(readme)

   if createTarFile:
      createTarball(targetDir)

def main():
   parser = argparse.ArgumentParser(
      description='''
Generate DSF drop bundle based on given JSON bundle config file.

e.g To generate DSF-EFT7 directory and tarball
generate_dsf_tarball.py --config DSF-EFT7.json --target-dir DSF-EFT7 --create-tarball

Please update this script if those versions changes''',
      formatter_class=argparse.RawTextHelpFormatter)
   parser.add_argument(
      '--config', required=True,
      help='create based on given JSON configuration file' )
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

   generateTarball(args.config, args.target_dir, args.show_readme,
                   args.create_tarball)

if __name__ == "__main__":
   main()
