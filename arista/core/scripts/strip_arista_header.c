// Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <assert.h>

unsigned char copyBuf[1024];

int main( int argc, char* argv[] )
{
   FILE *ipFile;
   FILE *opFile;
   const char *fileExtension;
   size_t bytesRead, bytesWritten, bytesToRead, bytesToWrite;
   char headerKey;
   uint16_t sectionSize;
   uint32_t contentSize;
   int outputSizeMB;
   uint32_t outputSize;
   uint32_t outputSizeRemaining = 0;
   int returnVal = 0;

   for ( int i = 1; i < argc; i++ ) {
      if ( strcmp( argv[i], "--help" ) == 0 ) {
         printf( "usage: strip_arista_header input_file(.abit) output_file output_file_size(in MB)\n" );
         return 0;
      }
   }
   if ( argc != 4 ) {
      printf( "please pass file names and output file size as arguments\n" );
      printf( "usage: strip_arista_header input_file(.abit) output_file output_file_size(in MB)\n" );
      return -1;
   }
   fileExtension = strrchr( argv[1], '.' );
   if( fileExtension == argv[1] ) {
      fileExtension = NULL;
   }
   else {
      fileExtension = fileExtension + 1;
   }
   if( strcmp( fileExtension, "abit" ) ) {
      printf( "input file must be .abit file \n" );
      return -1;
   }

   ipFile = fopen( argv[1], "rb" );
   if ( ipFile == NULL ) {
      printf( "cannot open input file for reading\n" );
      return -1;
   }
   opFile = fopen( argv[2], "wb" );
   if ( opFile == NULL ) {
      printf( "cannot open output for writing\n" );
      if ( fclose( ipFile ) ) {
         printf( "error closing input file\n" );
      }
      return -1;
   }
   outputSizeMB = atoi( argv[3] );
   outputSize = outputSizeMB * 1024 * 1024;

   // First read through the Arista header, which is terminated by null character.
   while( fread( copyBuf, 1, 1, ipFile ) != 0 ) {
      if( *copyBuf == 0x0 ) {
         break;
      }
   }
   // The first 13 bytes of a .BIT file are always the same. Discard them.
   bytesRead = fread( copyBuf, 1, 13, ipFile );
   assert( bytesRead == 13 );
   // There are 5 headers in the file - from 'a' through 'e' ( in ascii ).
   headerKey = 'a';
   while( headerKey != 'e' ) {
      bytesRead = fread( copyBuf, 1, 1, ipFile );
      assert( bytesRead == 1 );
      assert( *copyBuf == headerKey );
      // Read the size of this section, which is the next two bytes.
      bytesRead = fread( copyBuf, 1, 2, ipFile );
      assert( bytesRead == 2 );
      sectionSize = ( ( uint8_t )copyBuf[0] ) << 8
         | ( uint8_t )copyBuf[1];
      // Read and discard 'sectionSize' number of bytes.
      fseek( ipFile, sectionSize, SEEK_CUR );
      headerKey += 1;
   }
   // We are at the header 'e', which specifies, in the next four bytes, the
   // size of the image content in bytes.
   bytesRead = fread( copyBuf, 1, 1, ipFile );
   assert( *copyBuf == headerKey );
   bytesRead = fread( copyBuf, 1, 4, ipFile );
   contentSize = ( ( uint8_t )copyBuf[0] ) << 24
      | ( ( uint8_t )copyBuf[1] ) << 16
      | ( ( uint8_t )copyBuf[2] ) << 8
      | ( ( uint8_t )copyBuf[3] );
   if ( outputSize > contentSize ) {
      outputSizeRemaining = outputSize - contentSize;
   }

   // Copy bytes from the input file to the output file
   while ( contentSize > 0) {
      if ( contentSize > sizeof copyBuf ) {
         bytesToRead = sizeof copyBuf;
      }
      else {
         bytesToRead = contentSize;
      }
      bytesRead = fread( copyBuf, 1, bytesToRead, ipFile );
      if ( bytesRead ) {
         bytesWritten = fwrite( copyBuf, 1, bytesRead, opFile );
      }
      else {
         bytesWritten = 0;
      }
      if ( bytesRead == bytesWritten ) {
         contentSize -= bytesRead;
      }
      else {
         break;
      }
   }
   if ( contentSize ) {
      printf( "error in copying file\n" );
      returnVal = -1;
   }
   else {
      // Add null bytes to the output file in order to have the desired size
      memset( copyBuf, 0, sizeof copyBuf );
      while ( outputSizeRemaining > 0 ) {
         if ( outputSizeRemaining > sizeof copyBuf ) {
            bytesToWrite = sizeof copyBuf;
         }
         else {
            bytesToWrite = outputSizeRemaining;
         }
         bytesWritten = fwrite( copyBuf, 1, bytesToWrite, opFile );
         if ( bytesWritten == bytesToWrite ) {
            outputSizeRemaining -= bytesWritten;
         }
         else {
            break;
         }
      }
      if ( outputSizeRemaining ) {
         printf( "error in truncating output file\n" );
         returnVal = -1;
      }
   }

   if ( fclose ( ipFile ) ) {
      printf( "error closing input file\n" );
      returnVal = -1;
   }
   if ( fclose( opFile ) ) {
      printf( "error closing output file\n" );
      returnVal = -1;
   }

   return returnVal;
}

