#!/usr/bin/env python3

import json
from optparse import OptionParser
import os
import re

def parseArgs():
   parser = OptionParser( usage="usage: %prog [options] srcFile ..." )
   parser.add_option( "-d", "--dstDir", dest="dstDir", default="",
      help="destination directory where json mapping files will be saved" )

   ( options, args ) = parser.parse_args()
   if len( args ) < 1:
      parser.error( "At least one src file must be provided" )
   if options.dstDir:
      print( f"Writing mapping to: {options.dstDir}" )

   for arg in args:
      if not os.path.isfile( arg ):
         parser.error( f"srcFile '{arg}' is not a file" )
   return ( options, args )

def extractMapping( srcFile, dstDir ):
   # Mapping definition start line, we use part of it in output file name if there
   # are more than one mapping in a single file. Examples:
   # - constexpr auto kJsonPlatformMappingStr = R"( -> group(1)=""
   # - constexpr auto kJsonMultiNpuPlatformMappingStr = R"( -> group(1)="MultiNpu"
   startRe = re.compile(
      R'constexpr\s+auto\s+kJson(.*)PlatformMappingStr\s+=\s+R"\(\s*' )

   # End mapping line
   endRe = re.compile( R'^\)";$' )

   # File name regex to extract platform name like 'Meru800bfaPlatformMapping.cpp'
   pMatch = re.match( R".*?([^/]+)PlatformMapping.*", srcFile )
   assert pMatch, f'Couldn\'t find platform name in path {srcFile}'
   platform = pMatch.group( 1 )

   insideMapping = False
   dst = None
   dstFile = None
   dstFiles = []
   with open( srcFile ) as src:
      for line in src:
         sMatch = startRe.match( line )
         if sMatch:
            insideMapping = True
            suffix = sMatch.group( 1 )
            dstFile = os.path.join( dstDir, f"{platform}{suffix}Mapping.json" )
            dst = open( dstFile, 'w' )
         elif insideMapping:
            if endRe.match( line ):
               insideMapping = False
               dst.write( "" )
               dst.close()
               dstFiles.append( dstFile )
            else:
               dst.write( line )
   assert not insideMapping, f"Mapping end pattern not found in {srcFile}"
   assert dstFile, f"Mapping (start pattern) not found in {srcFile}"
   return dstFiles

def verifyMapping( filePath ):
   # Just check if written json is properly formatted and not empty.
   print(f'Checking: {filePath}')
   with open( filePath ) as file:
      mapping = json.load( file )
      assert mapping, "Mapping in file is empty"

def main():
   ( options, args ) = parseArgs()
   if options.dstDir:
      os.makedirs( options.dstDir, exist_ok=True )
   for arg in args:
      mappingPaths = extractMapping( arg, options.dstDir )
      for mappingPath in mappingPaths:
         verifyMapping( mappingPath )

if __name__ == "__main__":
   main()

