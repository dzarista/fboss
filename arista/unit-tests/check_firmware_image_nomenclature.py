# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import os
import re

def checkFilenameFormat(fileName, platformName):
   """
   Checks if a filename matches the format:
   P_<platformName>_F_*_V_*.*

   Args:
      fileName (str): The filename to check.
      platformName (str): The platform associated with the file.

   Returns:
      bool: True if the filename matches the format, False otherwise.
   """
   pattern = rf"^P_{re.escape(platformName)}_F_.+_V_.+\..+$"
   match = re.match(pattern, fileName)
   return bool(match)

def getPackagePath(parentDirectory):
   """
   Finds the subdirectory named 'package_n' with the largest integer 'n'
   within the given parent directory and returns its full path.

   Args:
      parentDirectory (str): The path to the directory containing the
                              'package_0', 'package_1', ..., 'package_n'
                              subdirectories.

   Returns:
      str: The full path to the 'package_n' directory with the largest 'n',
           or None if no such subdirectory is found.
   """
   largestN = -1
   packageNPath = None

   try:
      for item in os.listdir(parentDirectory):
         item_path = os.path.join(parentDirectory, item)
         if os.path.isdir(item_path) and item.startswith("package_"):
            try:
               nValue = int(item.split("_")[1])
               if nValue > largestN:
                  largestN = nValue
                  packageNPath = item_path
            except ValueError:
               # Ignore items that start with "package_" but don't have a valid integer suffix
               pass
   except FileNotFoundError:
      print(f"Error: Parent directory '{parentDirectory}' not found.")
      return None
   except OSError as e:
      print(f"Error accessing directory '{parentDirectory}': {e}")
      return None

   return packageNPath

def processSubdirectoriesFromList(parentDirectory, subdirectoryNames):
   """
   Iteratively visits each subdirectory in the provided list (which are
   assumed to be within the parent directory) and prints the names of
   all files found within them.

   Args:
      parentDirectory (str): The path to the directory containing
                              the subdirectories.
      subdirectoryNames (list): A list of subdirectory names (strings).
   """
   try:
      if not os.path.isdir(parentDirectory):
         print(f"Error: Parent directory '{parentDirectory}' not found or is not a directory.")
         return

      print(f"Processing subdirectories from the list within: {parentDirectory}")

      for subdirName in subdirectoryNames:
         intermediatePath = os.path.join(parentDirectory, subdirName, "firmware")
         subdirectoryPath = getPackagePath(intermediatePath)
         if subdirectoryPath is None:
            continue

         if os.path.isdir(subdirectoryPath):
            print(f"\nFiles in subdirectory: {subdirName}")
            try:
               filesInSubdir = os.listdir(subdirectoryPath)
               onlyFiles = [item for item in filesInSubdir if os.path.isfile(os.path.join(subdirectoryPath, item))]

               if onlyFiles:
                  for fileName in onlyFiles:
                     print(f"  - {fileName}")
                     if fileName == "README.md":
                        continue;
                     if not checkFilenameFormat(fileName, subdirName):
                        raise Exception( f"File name ({fileName}) not following the naming convention" )
               else:
                  print("  No files found in this subdirectory.")

            except OSError as e:
               print(f"Error accessing subdirectory '{subdirName}': {e}")
         else:
            print(f"Warning: Subdirectory '{subdirName}' not found or is not a directory within '{parentDirectory}'.")

   except OSError as e:
      print(f"Error accessing directory '{parentDirectory}': {e}")

if __name__ == "__main__":
   subtreeRoot = "/arista-fboss-apr-16/arista-fboss/fboss.bsp.arista"
   platformList = ["meru800bia", "meru800bfa"]

   processSubdirectoriesFromList(subtreeRoot, platformList)
