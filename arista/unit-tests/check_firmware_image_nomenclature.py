# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

"""
Unit test to verify nomenclature for firmware image files.
The test examines all the firmware images in the latest firmware package
for the platforms listed in platformList to verify the firmware image file names
match the format P_platform_F_target_V_version.
"""

import os
import re
import pathlib

def checkFilenameFormat( fileName, platformName ):
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
   match = re.match( pattern, fileName )
   return bool( match )

def getPackagePath( parentDirectory ):
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

   for item in os.listdir( parentDirectory ):
      item_path = os.path.join( parentDirectory, item )
      if os.path.isdir( item_path ) and item.startswith( "package_" ):
         try:
            nValue = int( item.split( "_" )[ 1 ] )
            if nValue > largestN:
               largestN = nValue
               packageNPath = item_path
         except ValueError as e:
            # Subdirectory starts with "package_",
            # but doesn't have a valid integer suffix
            raise Exception( f"Encountered unexpected directory - {item}" ) from e

   return packageNPath

def processSubdirectoriesFromList( parentDirectory, subdirectoryNames ):
   """
   Iteratively visits each subdirectory in the provided list (which are
   assumed to be within the parent directory) and verify the firmware image
   naming convention in the latest firmware package within the subdirectory.

   Args:
      parentDirectory (str): The path to the directory containing
                              the subdirectories.
      subdirectoryNames (list): A list of subdirectory names (strings).
   """
   if not os.path.isdir( parentDirectory ):
      raise Exception( f"Error: Parent directory '{parentDirectory}' "
                       "not found or is not a directory." )

   for subdirName in subdirectoryNames:
      intermediatePath = os.path.join( parentDirectory, subdirName, "firmware" )
      subdirectoryPath = getPackagePath( intermediatePath )
      if subdirectoryPath is None:
         continue

      if os.path.isdir( subdirectoryPath ):
         print( f"\n{subdirName} firmware images:" )
         filesInSubdir = os.listdir( subdirectoryPath )
         onlyFiles = [ item for item in filesInSubdir
                      if os.path.isfile( os.path.join( subdirectoryPath, item ) ) ]

         for fileName in onlyFiles:
            if fileName == "README.md":
               continue
            print( f"  - {fileName}" )
            if not checkFilenameFormat( fileName, subdirName ):
               raise Exception( f"File name ({fileName}) "
                                 "not following the naming convention" )
      else:
         raise Exception( f"Warning: Subdirectory '{subdirName}' not found or "
                          "is not a directory within '{parentDirectory}'." )

if __name__ == "__main__":
   scriptDir = pathlib.Path( __file__ ).resolve().parent
   subtreeRoot = os.path.join( scriptDir, "..", "..", "fboss.bsp.arista" )
   platformList = [ "meru800bia", "meru800bfa", "glath05a-64o", "darwin", "elbert",
                    "yamp" ]

   processSubdirectoriesFromList( subtreeRoot, platformList )
