#!/bin/env python3
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
import sys

def escape_for_inline( s: str ) -> str:
    return s.replace( '\\', '\\\\' ).replace( '"', '\\"' ).replace( '\n', '\\n' )

def main():
    p = argparse.ArgumentParser(
        description="Convert a YAML pipe (|) block into a single-line string."
    )
    p.add_argument( 'infile', help="YAML file containing the `yamlConfig: |` block" )
    p.add_argument( '-o','--outfile',
                    help="Where to write the result (stdout if omitted)" )
    args = p.parse_args()


    if args.infile == '-':
        text = sys.stdin.read()
    else:
        open( args.infile, 'r' ).read()

    text = text.rstrip('\n')

    inline = escape_for_inline( text )
    output = f'"{inline}"'

    if args.outfile:
        with open( args.outfile, 'w' ) as f:
            f.write( output )
    else:
        print( output )

if __name__ == '__main__':
    main()
