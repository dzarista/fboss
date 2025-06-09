# DSF EFT Tarball Generator

## About
This script generates an EFT tarball for the Distributed Switch Fabric (DSF)
platforms Viper and Whistler. The script is config-driven, meaning the user
specifies which information should be included in the tarball entirely via a JSON
configuration file. The accepted keys in the JSON config file are defined in
the section below.

## How to Generate a Tarball for a New EFT
The process to generate a new tarball is as follows:

1) Write a new release notes file in ./release_notes.
2) Edit the dsf-eft.json config file so that your new release notes file is
   the latestReleaseNotes. Move the current latestReleaseNotes to the beginning
   of the pastReleaseNotes list.
3) Edit the ./release_notes/known_issues.txt file to reflect the known issues
   in the new EFT drop.
4) If a new patch is included with the new EFT drop, place the patch file and
   a instructions.txt file in the patches directory and update the patches
   config in dsf-eft.json to include your new patch.
5) If programmable images in the new EFT have changed, copy the new programmable
   image files to the ./programmables directory and update the programmables
   config in dsf-eft.json accordingly.
6) If some deliverables in the current EFT drop are found in GitHub repos,
   update the repos config in dsf-eft.json to include the correct repo(s)
   with the correct commit hashes.
7) If test results are expected with the EFT drop, add the test results to a
   ./test_results directory and update the testResults section in dsf-eft.json.
8) Run the generate_dsf_tarball.py script to create the new tarball.
9) Publish your new tarball to dist:/dist/storage/fboss/programmables and send
   out an internal email to the team for review.
10) Once internal review is complete, generate an FTP link to the tarball
    using `a ftp up`, then email the link and the latest release notes to
    fboss_dsf_dev@meta.com (making sure to CC dsf-support@arista.com). Make
    sure to include the entire contents of the tarball README at the end of
    the email.

## Example Usage
This script will typically be run as follows:
```
python3 generate_dsf_tarball.py --config dsf-eft.json --target-dir Meru-EFT-Sep20
        --show-readme --create-tarball
```
Run `python3 generate_dsf_tarball.py --help` to see the full usage.

## JSON Config File Format
See dsf-eft.json for the latest working config.

The JSON config file is a single object containing the following keys:

1) latestReleaseNotes: this is a single object which describes where to find the
   release notes text for the latest EFT drop.

Format:
```
       {
          "name" : <name string for the latest EFT release>,
          "notesFile": <file path of text file containing release notes>
       }
```
Only one latestReleaseNotes key may be specified in the JSON config, and in fact
one must be specified or the script will complain.

2) pastReleaseNotes: this is a list of objects in the same format as the object in
   the latestReleaseNotes. Multiple objects can be included in the list, or no
   objects can be included in the list. Each object describes where to find the
   release notes text for a previous EFT drop. The old release notes are included
   at the end of the tarball README for customer convenience.

3) knownIssuesFile: this is a single string containing the file path of a text file
   which describes the known issues with the EFT. This is not required if the
   latest EFT drop has no issues.

4) patches: this is a list of patch objects, each of which describes where to find
   a patch file and a text file describing how to apply the patch.

Format:
```
      {
         "name" : <string name of the utility being patched>,
         "patchFile" : <file path of the patch file>,
         "instructionsFile" : <text file containing instructions on how to apply
                               the path>
      }
```
Many patch objects can be included in the list, but none are required. All
patches will get packaged in the tarball in the patches/ directory.

5) programmables: this is a list of programmable objects, each of which describes
   a programmable image that will be packaged in the tarball.

Format:
```
      {
         "name" : <string name of programmable, used in README>,
         "imageFile" : <file path of programmable image file>
      }
```
Many programmable objects can be included in the list, but none are required.
All programmables will get packaged in the tarball in the programmables/
directory.

6) repos: this is a list of repo objects, each of which describes a GitHub
   repository that contains deliverables that are part of the latest EFT drop.

Format:
```
      {
         "name" : <string name of the repo, used for README header>,
         "url" : <URL of repo in GitHub, used to clone the repo>,
         "branch" : <string name of the branch used in the repo>,
         "commitHash" : <full commit hash string at which customer should pull
                         repo; this gets checked by cloning the repo>,
         "note" : <a string note to be included in the README (not required)>
      }
```

7) testResults: this is a list of test result objects, each of which describes
   a test results file produced by a test suite that has been run against the
   software shared in the latest EFT bundle.

Format:
```
      {
         "name" : <string name of test suite, used in README>,
         "resultsFile" : <file path containing test results>
      }
```
Many test result objects can be included in the list, but none are required.
All test results will get packaged in the tarball in the test_results/
directory.
