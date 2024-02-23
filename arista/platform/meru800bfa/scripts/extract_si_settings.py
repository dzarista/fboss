#!/bin/env python
import csv

"""
Extract the relevant fields to map SI settings from
Whistler_port_mapping_SI_settings_v3.csv, which itself is a csv file from
https://docs.google.com/spreadsheets/d/1_IAStZOz2Xc7oQuB0oRmaBqd-IlNKUEh13mVHr6wkMQ/edit#gid=1100430376

Output of this script is Whistler_Hw_SI_Settings_v3.csv, which can then be used by the
gen_*vendor_mapping script to update SI settings in the vendor mapping sheet.
"""

with open( "Whistler_port_mapping_SI_settings_v3.csv" ) as fh, open(
   "Whistler_Hw_SI_Settings_v3.csv", "w") as siFh:
   reader = csv.reader( fh )
   writer = csv.writer(siFh, lineterminator='\n', quoting=csv.QUOTE_NONE)
   header = [ "OSFP Port", "OSFP Lane", "Pre3", "Pre2", "Pre", "Main", "Post",
             "Post2" ]
   writer.writerow(header)
   for row in reader:
      # Crude way to skip the first line with field names
      if not row[4].isdigit():
         continue
      writeRow = [ row[ 4 ], row[ 5 ] ]
      writeRow.extend(row[ 22 : 28 ])
      writer.writerow( writeRow )
