#!/usr/bin/env python3
# Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

# This is a utility to generate heat maps based on raw transceiver thermal
# data for a specific platform.

import argparse
from collections import defaultdict
import csv
from datetime import date
from pathlib import Path
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
      PageBreak,
      Paragraph,
      SimpleDocTemplate,
      Spacer,
      Table,
      TableStyle
)
import sys
import Tac

class PortHeatMap:
   '''This base class takes thermal data and generates stylized heat map tables.'''

   # A 2D array that physically models the front panel of the switch.
   portMap = [ [] ]
   # Used to know how many tables should be printed in the PDF per page.
   mapsPerPage = 0

   def __init__( self, pwmToPortMaxTemp ):
      # Map of PWM : { portName: portMaxTemp }
      self.pwmToPortMaxTemp = pwmToPortMaxTemp

   def getHeatMapForPwm( self, pwm ):
      '''Based on the set portMap, generate the heat map table.'''

      # Creates a copy of the portMap with the temperature values added.
      data = [ portRow[ : ] for portRow in self.portMap ]
      portNameToTemp = self.pwmToPortMaxTemp[ pwm ]
      for portRow in data:
         for index, portName in enumerate( portRow[ : ] ):
            if not portName:
               continue
            portRow[ index ] = f'{portName}: {portNameToTemp[portName]:.2f}'

      # Generates the heat map table. The table is modeled as a 2D array with
      # coordinates (col,row). The TableStyle is composed of a list of format
      # commands, the second and third arguments of which indicate the cell
      # range.
      portTable = Table( data )
      fmtCmds = [
            ( 'GRID', ( 0, 0 ), ( -1, -1 ), 1, colors.black ),
            ( 'ALIGN', ( 0, 0 ), ( -1, -1 ), 'LEFT' ),
            ( 'VALIGN', ( 0, 0 ), ( -1, -1 ), 'MIDDLE' ),
      ]
      for rowIndex, row in enumerate( data ):
         for columnIndex, val in enumerate( row ):
            if not val:
               continue
            coord = ( columnIndex, rowIndex )
            temp = float( val.split( ': ' )[ 1 ] )
            # TODO: could have this be configurable in the class based on optic.
            if temp <= 50:
               color = colors.lightblue
            elif temp <= 60:
               color = colors.palegreen
            elif temp <= 65:
               color = colors.yellow
            elif temp <= 70:
               color = colors.orange
            else:
               color = colors.palevioletred
            fmtCmds.append( ( 'BACKGROUND', coord, coord, color ) )

      style = TableStyle( fmtCmds )
      portTable.setStyle( style )
      return portTable

class ViperPortHeatMap( PortHeatMap ):
   # TODO: add the QSFP port 39
   portMap = [
      [ 'Fab1', 'Fab5', '',      'Eth11', 'Eth15', '',      'Eth21', 'Eth25', '',      'Fab31', 'Fab35' ],
      [ 'Fab2', 'Fab6', '',      'Eth12', 'Eth16', '',      'Eth22', 'Eth26', '',      'Fab32', 'Fab36' ],
      [ 'Fab3', 'Fab7', 'Fab9',  'Eth13', 'Eth17', 'Eth19', 'Eth23', 'Eth27', 'Fab29', 'Fab33', 'Fab37' ],
      [ 'Fab4', 'Fab8', 'Fab10', 'Eth14', 'Eth18', 'Eth20', 'Eth24', 'Eth28', 'Fab30', 'Fab34', 'Fab38' ],
   ]
   mapsPerPage = 3

class WhistlerPortHeatMap( PortHeatMap ):
   portMap = [
      [ 'Fab1',   'Fab2',   'Fab3',   'Fab4',   'Fab5',   'Fab6',   'Fab7',   'Fab8'   ],
      [ 'Fab9',   'Fab10',  'Fab11',  'Fab12',  'Fab13',  'Fab14',  'Fab15',  'Fab16'  ],
      [ 'Fab17',  'Fab18',  'Fab19',  'Fab20',  'Fab21',  'Fab22',  'Fab23',  'Fab24'  ],
      [ 'Fab25',  'Fab26',  'Fab27',  'Fab28',  'Fab29',  'Fab30',  'Fab31',  'Fab32'  ],
      [ 'Fab33',  'Fab34',  'Fab35',  'Fab36',  'Fab37',  'Fab38',  'Fab39',  'Fab40'  ],
      [ 'Fab41',  'Fab42',  'Fab43',  'Fab44',  'Fab45',  'Fab46',  'Fab47',  'Fab48'  ],
      [ 'Fab49',  'Fab50',  'Fab51',  'Fab52',  'Fab53',  'Fab54',  'Fab55',  'Fab56'  ],
      [ 'Fab57',  'Fab58',  'Fab59',  'Fab60',  'Fab61',  'Fab62',  'Fab63',  'Fab64'  ],
      [ 'Fab65',  'Fab66',  'Fab67',  'Fab68',  'Fab69',  'Fab70',  'Fab71',  'Fab72'  ],
      [ 'Fab73',  'Fab74',  'Fab75',  'Fab76',  'Fab77',  'Fab78',  'Fab79',  'Fab80'  ],
      [ 'Fab81',  'Fab82',  'Fab83',  'Fab84',  'Fab85',  'Fab86',  'Fab87',  'Fab88'  ],
      [ 'Fab89',  'Fab90',  'Fab91',  'Fab92',  'Fab93',  'Fab94',  'Fab95',  'Fab96'  ],
      [ 'Fab97',  'Fab98',  'Fab99',  'Fab100', 'Fab101', 'Fab102', 'Fab103', 'Fab104' ],
      [ 'Fab105', 'Fab106', 'Fab107', 'Fab108', 'Fab109', 'Fab110', 'Fab111', 'Fab112' ],
      [ 'Fab113', 'Fab114', 'Fab115', 'Fab116', 'Fab117', 'Fab118', 'Fab119', 'Fab120' ],
      [ 'Fab121', 'Fab122', 'Fab123', 'Fab124', 'Fab125', 'Fab126', 'Fab127', 'Fab128' ],
   ]
   mapsPerPage = 1

class ThermalDataParser:
   '''Helper class for parsing transceiver thermal data collected by the
   CollectFanSweepData.py script.'''

   def __init__( self, csvFileName ):
      self.csvFileName = csvFileName

   def _getFieldToPort( self, fields ):
      '''Create a map of CSV field name to front panel port name.'''

      # Map of port name to columns for lanes.
      fieldToPort = defaultdict( list )
      for field in fields:
         portMatch = re.match( r'(Ethernet|Fabric)(\d+)/\d+', field )
         if portMatch:
            name = 'Eth' if portMatch.group( 1 ) == 'Ethernet' else 'Fab'
            num = portMatch.group( 2 )
            fieldToPort[ field ] = name + num
      return fieldToPort

   def parse( self ):
      '''Go through the CSV file and create map of average PWM (rounded to the
      nearest percent) to a dict of { portName: temp }.'''

      pwmToPortMaxTemp = defaultdict( lambda: defaultdict( list ) )
      with open( self.csvFileName ) as csvFile:
         reader = csv.DictReader( csvFile )
         fieldToPort = self._getFieldToPort( reader.fieldnames )
         for row in reader:
            pwm = round( float( row[ 'AvgFanPwm' ] ) )
            portNameToTemps = defaultdict( list )
            for portField, portName in fieldToPort.items():
               portNameToTemps[ portName ].append( float( row[ portField ] ) )
            for portName in set( fieldToPort.values() ):
               laneTemps = portNameToTemps[ portName ]
               pwmToPortMaxTemp[ pwm ][ portName ] = sum( laneTemps ) / len( laneTemps )
      return pwmToPortMaxTemp

def beginPdf( csvFileName, dut ):
   '''Begin a PDF file with the correct header page.'''

   pdfName = Path( csvFileName ).stem + '-PortHeatMaps.pdf'
   doc = SimpleDocTemplate( pdfName, pagesize=A4 )
   doc.pagesize = landscape( A4 )

   content = [
         Paragraph(
            'Front Panel Port Transceiver Temperature Heat Maps<br/>'
            f'dut: {dut}<br/>'
            f'data file: {csvFileName}<br/>'
            f'date: {date.today()}',
            ParagraphStyle(
               'pdfHeader',
               alignment=TA_CENTER,
               fontSize=20,
               leading = 20 * 1.2
            )
         ),
         PageBreak()
   ]
   return doc, content

dutPrefixToMapper = {
      'vpr': ViperPortHeatMap,
      'wlr': WhistlerPortHeatMap,
}

def parseArgs( argv ):
   parser = argparse.ArgumentParser(
         description='Program to generate a consolidated PDF of port temperature '
                     'heat maps at various fan speeds from an input CSV file of '
                     'raw data.'
   )
   parser.add_argument(
         'dut',
         help='Name of the dut'
   )
   parser.add_argument(
         'rawDataCsvFile',
         help='CSV file containing raw thermal data'
   )
   return parser.parse_args( argv )

def main():
   '''Parse the thermal data, then generate a PDF with heat map tables for
   every PWM.'''

   args = parseArgs( sys.argv[ 1: ] )

   thermalData = ThermalDataParser( args.rawDataCsvFile ).parse()

   mapperClass = None
   for dutPrefix, heatMapperClass in dutPrefixToMapper.items():
      if args.dut.startswith( dutPrefix ):
         mapperClass = heatMapperClass
         break
   if not mapperClass:
      print( f'No mapper class found for dut: {args.dut}' )
      sys.exit( 1 )

   mapper = mapperClass( thermalData )
   pdfDoc, pdfContent = beginPdf( args.rawDataCsvFile, args.dut )
   for index, pwm in enumerate( sorted( thermalData ) ):
      heatMap = mapper.getHeatMapForPwm( pwm )
      header = Paragraph(
            f'PWM={pwm}% (temperature in degrees C)',
            ParagraphStyle( 'tableHeader', fontSize=20 )
      )
      pwmContent = [ header, Spacer( 0, 20 ), heatMap ]
      # Every Nth heat map, add a newline.
      if ( index + 1 ) % mapper.mapsPerPage == 0:
         pwmContent.append( PageBreak() )
      else:
         pwmContent.append( Spacer( 0, 20 ) )
      pdfContent.extend( pwmContent )

   pdfDoc.build( pdfContent )

if __name__ == '__main__':
   main()
