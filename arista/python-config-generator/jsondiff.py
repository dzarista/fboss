#!/usr/bin/env python3
# Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import sys
import json


def pathRep( path ):
   return "/".join( path )

def truncatedValue( obj ):
   res = str( obj )
   if len( res ) > 40:
      res = res[ : 40 ] + "..."
   return res

def compareSimple( data1, data2, path ):
   if data1 != data2:
      print( f"{pathRep(path)}: {data1} != {data2}" )

def compareList( data1, data2, path ):
   lenData1 = len( data1 )
   lenData2 = len( data2 )
   for i in range( max( lenData1, lenData2 ) ):
      if i < lenData1 and i < lenData2:
         compare( data1[ i ], data2[ i ], path + [ f"[{i}]" ] )
         continue

      if i < lenData1: # Only in first
         print( f"{pathRep(path)} [{i}]: First has {truncatedValue(data1[i])}" )
      else: # Only in second
         print( f"{pathRep(path)} [{i}]: Second has {truncatedValue(data2[i])}" )


def compareDict( data1, data2, path ):
   keys1 = set( data1.keys() )
   keys2 = set( data2.keys() )

   for key in sorted( keys1 | keys2 ):
      if key in keys1 & keys2:
         compare( data1[ key ], data2[ key ], path=path + [ key ] )
      elif key in keys1:
         print( f"{pathRep(path)}: First has extra key {key}: {truncatedValue(data1[key])}" )
      else: # only in second set
         print( f"{pathRep(path)}: Second has extra key {key}: {truncatedValue(data2[key])}" )

def compare( data1, data2, path ):
   if type( data1 ) != type( data2 ):
      assert False, f"{pathRep(path)}: Can't compare {type(data1)} against {type(data2)}"

   if isinstance( data1, dict ):
      compareDict( data1, data2, path )

   elif isinstance( data1, list ):
      compareList( data1, data2, path )

   elif isinstance( data1, ( int, str, bool ) ):
      compareSimple( data1, data2, path )

   else:
      print( f"Unhandled type {type(data1)} at {pathRep(path)}" )

def main( fname1, fname2 ):
   data1 = json.load( open( fname1 ) )
   data2 = json.load( open( fname2 ) )

   print( f"First {fname1}, second {fname2}" )
   compare( data1, data2, [] )

if __name__ == "__main__":
   main( fname1=sys.argv[ 1 ], fname2=sys.argv[ 2 ] )
