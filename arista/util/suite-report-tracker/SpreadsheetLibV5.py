#!/usr/bin/env python3
# Copyright (c) 2017 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import googleapiclient.discovery
import datetime
import numbers

from ArGoogleApps import OAuthLib
from ArGoogleApps import SpreadsheetLibV4 as sslv4

# pylint: disable-msg=W0105
'''
SpreadsheetLib is a utility library that makes it easier to programatically
manipulate Google Spreadsheets.

The following abstractions are supported

Service:
   Abstraction of Google Sheets REST service based on the V4 API
   The Google API is completely abstracted by the library, use does
   not require understanding REST or the V4 API
   Use getSpreadsheet() to load a Spreadsheet

Spreadsheet:
   Abstracts a Google Sheet document, and all accompanying Sheets
   Use sheet() to access a desired Sheet by name (title)

Sheet:
   Abstracts a single Sheet within the Spreadsheet
   The Key Column _must_ be set before accessing data with setrKeyCol()
   Use getRow() to locate a specific SheetRow by its key
   Use getRows() to retreieve all non-header SheetRows sorted by row number
   in ascending order
   Use getRowKey() to obtain the key value for a given SheetRow
   Use addRow() to create a new SheetRow with the given key
   Use deleteRow() to delete a SheetRow from the Sheet
   Use commitChanges() to submit all adds/edits/deletes to the Google Sheet
   Changes are not persisted until commitChanges() is invoked
   Use sort() to sort the Google Doc by a given column

SheetRow:
   Abstracts a row within the Sheet
   Rows in the existing document are accessed via Sheet.getRow() or Sheet.getRows()
   Rows are added to the Sheet with Sheet.addRow()
   Edits to SheetRows with set() mark the row as modified. To apply the change
   to the Google Sheet use Sheet.commitChanges()
   Use rowNum() to determine the row number, 2 is the first non-header row
   Use get() to get the value for a column by its name
   Use set() to update a column by its name and mark the SheetRow as edited

Before using it, you need to:
1. Create a Google Sheet with column names in the first row
2. Assign it world writeable permissions.

For sample use, see README.md
'''

# Row within a Sheet of a Spreadsheet
class SheetRow( object ):
   # When representing existing sheet rowNum and colVals are included
   # colNames and colVals are simple arrays of values (string/numbers/booleans)
   def __init__( self, sheet, colNames, rowNum=None, colVals=None ):
      self.values_ = {}
      self.sheet_ = sheet
      self.rowNum_ = rowNum
      if colVals is None:
         colVals = [None] * len( colNames )
      self._resetRow( colNames, colVals )

   def rowNum( self ):
      return self.rowNum_

   # Column value by name
   def get( self, name ):
      return self.values_[ name ]

   # Set column value by name
   # Calls Sheet.updateRow() behind the scenes
   def set( self, name, value ):
      if name not in self.values_:
         raise KeyError( "Missing column " + name )
      # google sheets only likes utf-8, so remove offending characters
      # if isinstance( value, str ):
      #    value = value.encode( 'utf-8' )
      self.values_[ name ] = value
      # Mark as edited
      self.sheet_.editRow( self )

   # Clean up all data and references from this row
   # Used when a Sheet is reloaded to cleanup previous references to Sheet
   def cleanUp( self ):
      self.values_ = None
      self.sheet_ = None
      self.rowNum_ = None

   # Internal row initialization
   def _resetRow( self, colNames, colVals ):
      assert len( colNames ) == len( colVals ), "Must have 1 value for all columns"
      self.values_ = {}
      for idx in range( len( colNames ) ):
         self.values_[ colNames[ idx ] ] = colVals[ idx ]

# Sheet within a spreadsheet
class Sheet( object ):
   # gSheet from v4 API
   def __init__( self, gSheet, spreadsheet ):
      self.spreadsheet_ = spreadsheet
      self.id_ = None
      self.name_ = None
      # List of colmns, in order
      self.columns_ = None
      self.keyCol_ = None
      self.numRows_ = 0
      self.numCols_ = 0
      self.data_ = None
      self.edits_ = None
      self.rowVals_ = None
      self.dateTimeFormat_ = "yyyy-mm-dd hh:mm"
      self.dateFormat_ = "yyyy-mm-dd"
      self._resetSheet( gSheet )

   # Google Sheet id within Soreadsheet
   def id( self ):
      assert self.id_ is not None, "Sheet not loaded"
      return self.id_

   def name( self ):
      return self.name_

   # Name of singular column representing key
   def setKeyCol( self, keyCol ):
      self.keyCol_ = keyCol

   def getColumns( self, frozenRows=0 ):
      if self.data_ is None:
         self._loadData( frozenRows )
      return self.columns_

   # Returns SheetRow given key value
   def getRow( self, key, frozenRows=0 ):
      if self.data_ is None:
         self._loadData( frozenRows )
      return self.data_.get( key, None )

   # Return list of rows sorted by colun number
   def getRows( self, frozenRows=0 ):
      if self.data_ is None:
         self._loadData( frozenRows )

      def compareRows( r1, r2 ):
         if r1 is not None:
            return r1 - r2 if r2 is not None else 1
         else:
            return 1 if r2 is not None else 0

      return sorted( self.data_.values(), key=lambda row: row.rowNum(),
                     reverse=False )

   # Returns key value for row
   def getRowKey( self, row ):
      return row.get( self.keyCol_ )

   def getDateFormat( self ):
      return self.dateFormat_

   # Set the format for datetime.date instances
   # see: https://developers.google.com/sheets/api/guides/formats
   def setDateFormat( self, dateFormat ):
      self.dateFormat_ = dateFormat

   def getDateTimeFormat( self ):
      return self.dateTimeFormat_

   # Set the format for datetime.datetime instances
   # see: https://developers.google.com/sheets/api/guides/formats
   def setDateTimeFormat( self, dateTimeFormat ):
      self.dateTimeFormat_ = dateTimeFormat

   # Insert a new row into the Sheet
   # Must be committed with commitChange() to update Google Sheet
   def addRow( self, keyVal, frozenRows=0 ):
      if self.columns_ is None:
         self._loadData( frozenRows )
      nullVals = [None] * len( self.columns_ )
      newRow = SheetRow( self, self.columns_, nullVals )
      newRow.set( self.keyCol_, keyVal )
      self.data_[ keyVal ] = newRow
      edits = self._getEdits()
      edits.addRow( newRow )
      return newRow

   # Indicate that a row is modified
   # Must use commitChanges() to update Google Sheet
   def editRow( self, row ):
      edits = self._getEdits()
      edits.editRow( row )

   # Remove a row from the sheet
   # Must use commitChanges() to update Google Sheet
   def deleteRow( self, row ):
      edits = self._getEdits()
      edits.delRow( row )
      del self.data_[ row.get( self.keyCol_ ) ]

   # Invoke the changes on the Sheet
   # Reload the sheet with the current values
   # Previous references to SheetRows are invalidated
   def commitChanges( self, frozenRows=0 ):
      sheetEdits = self.getEdits()
      if sheetEdits:
         self.spreadsheet_.execCmds( sheetEdits )
      # Reset so sheet has latest data
      self._clearData()
      # Must reload metadata to account for all rows
      self._loadMetadata()
      self._loadData( frozenRows )

   # Sort the existing Google Sheet
   # Must commitChanges() prior to sort(), if needed
   def sort( self, colName, ascending=True, frozenRows=1, endRowOffset=0 ):
      colIdx = self.columns_.index( colName ) if self.columns_ is not None else None
      sortCmd = {
         "sortRange": {
            "range": {
               "sheetId": self.id_,
               "startRowIndex": frozenRows,
               "endRowIndex": self.numRows_ + endRowOffset,
               "startColumnIndex": 0,
               "endColumnIndex": len( self.columns_ )
            },
            "sortSpecs": [ {
               "dimensionIndex": colIdx,
               "sortOrder": "ASCENDING" if ascending else "DESCENDING"
            } ]
         }
      }
      self.spreadsheet_.execCmds( [ sortCmd ] )

   # Get edits for batchUpdate
   def getEdits( self ):
      return self.edits_.getBatchEdits() if self.edits_ is not None else None

   # Calculate the A1 range representing the entire sheet
   def sheetRange( self, startRow=None, endRow=None ):
      assert self.numRows_ > 0 and self.numCols_ > 0
      if startRow is None:
         startRow = 1
      if endRow is None:
         endRow = self.numRows_
      maxCol = self.numCols_ if self.numCols_ <= 26 else 26
      minColName = "A"
      maxColName = chr( ord( minColName ) + maxCol - 1 )
      return "%s!%s%d:%s%d" % ( self.name_, minColName, startRow,
                                maxColName, endRow )

   # Load sheet metadata from the Google V4 Sheet response
   def _resetSheet( self, gSheet ):
      gProps = gSheet[ "properties" ]
      self.id_ = gProps.get( "sheetId", None )
      self.name_ = gProps.get( "title", None )
      gridProps = gProps[ "gridProperties" ]
      self.numRows_ = gridProps.get( "rowCount", 0 )
      self.numCols_ = gridProps.get( "columnCount", 0 )

   # Reload sheet properties
   def _loadMetadata( self ):
      sheetProps = self.spreadsheet_.getSheetProperties( self.name_ )
      assert sheetProps
      self._resetSheet( sheetProps )

   # Load sheet data from Google V4 Sheet response
   def _loadData( self, frozenRows=0 ):
      assert self.keyCol_, "Key column must be set before loading data"
      self.rowVals_ = self.spreadsheet_.getData( self.sheetRange() )
      self.columns_ = self.rowVals_[ frozenRows ] # hack here :)
      self.numCols_ = len( self.columns_ )
      self.numRows_ = len( self.rowVals_ )
      keyIdx = self.columns_.index( self.keyCol_ )
      self.data_ = {}
      self._formatData()
      for rowNum, rowVal in enumerate( self.rowVals_[ 1: ], start=2 ):
         sheetRow = SheetRow( self, self.columns_, rowNum, rowVal )
         self.data_[ rowVal[ keyIdx ] ] = sheetRow

   # Ensure each row has a value per column
   def _formatData( self ):
      for row in self.rowVals_:
         while len( row ) < self.numCols_:
            row.append( None )

   # Clear data state and ongoing edits
   # Note columns and key column are unchanged
   def _clearData( self ):
      for rowData in self.data_.values():
         rowData.cleanUp()
      self.numRows_ = 1
      self.edits_ = None

   # Get the edit container, instantiating if necessary
   def _getEdits( self ):
      if self.edits_ is None:
         self.edits_ = Sheet.Edits( self )
      return self.edits_

   # Edit Container of accumulated changes to Sheet
   class Edits( object ):
      def __init__( self, sheet ):
         self.sheet_ = sheet
         self.adds_ = set()
         self.dels_ = set()
         self.edits_ = set()

      # Indicate a new row added to sheet
      def addRow( self, row ):
         # Prevent add if previously deleted
         assert row not in self.dels_, "Adding row previously deleted?"
         # Insure not previously edited
         self.edits_.discard( row )
         self.adds_.add( row )

      # Indicate a row edited within sheet
      def editRow( self, row ):
         # Don't track edit if adding or deleting
         if row not in self.adds_ and row not in self.dels_:
            self.edits_.add( row )

      # Indicate a row deleted from sheet
      def delRow( self, row ):
         # If added - must have been temporary
         if row in self.adds_:
            self.adds_.remove( row )
         else:
            # Clear any temporary deletes
            self.edits_.discard( row )
            self.dels_.add( row )

      # Format all edits into Google Sheets batchUpdate request format
      def getBatchEdits( self ):
         batchEdits = []
         # First edits - so row numbers match
         for editRow in self.edits_:
            editRqst = {
               "rows": [ self._formatRowData( editRow ) ],
               "fields": "userEnteredValue",
               "range": {
                  "sheetId": self.sheet_.id(),
                  "startRowIndex": editRow.rowNum() - 1,
                  "endRowIndex": editRow.rowNum(),
                  "startColumnIndex": 0,
                  "endColumnIndex": len( self.sheet_.getColumns() )
               }
            }
            batchEdits.append( { "updateCells": editRqst } )

         # Next deletes - because they are based on row numbers
         # Must delete last first as row numbers are based on state after each action
         for deleteRow in sorted( self.dels_, key=lambda delRow: delRow.rowNum(),
                                  reverse=True ):
            deleteRqst = {
               "range": {
                  "sheetId": self.sheet_.id(),
                  "dimension": "ROWS",
                  "startIndex": deleteRow.rowNum() - 1,
                  "endIndex": deleteRow.rowNum()
               }
            }
            batchEdits.append( { "deleteDimension": deleteRqst } )
         # Lastly new rows, sort according to key
         sheet = self.sheet_
         for addRow in sorted( self.adds_, key=sheet.getRowKey ):
            addRqst = {
               "sheetId": self.sheet_.id(),
               "rows": [ self._formatRowData( addRow ) ],
               "fields": "userEnteredValue"
            }
            batchEdits.append( { "appendCells": addRqst } )
         return batchEdits

      # Format the values within a single row for Google Sheets 'userEnteredValue'
      def _formatRowData( self, sheetRow ):
         cols = self.sheet_.getColumns()
         values = [ None ] * len( cols )
         for idx, col in enumerate( cols ):
            colVal = sheetRow.get( col )
            colTypeName = "stringValue"
            userFormat = None
            if colVal is None:
               colVal = ""
            elif isinstance( colVal, bool ):
               colTypeName = "boolValue"
            elif isinstance( colVal, numbers.Number ):
               colTypeName = "numberValue"
            elif isinstance( colVal, datetime.datetime ):
               colTypeName = "numberValue"
               # Convert full date-time to 'serial number' format
               colVal = self._convertDateTime( colVal )
               userFormat = {
                  "numberFormat": {
                     "type": "DATE_TIME",
                     "pattern": self.sheet_.getDateTimeFormat()
                  }
               }
            elif isinstance( colVal, datetime.date ):
               colTypeName = "numberValue"
               # Convert natural date to 'serial number' format
               colVal = self._convertDateTime( colVal )
               userFormat = {
                  "numberFormat": {
                     "type": "DATE",
                     "pattern": self.sheet_.getDateFormat()
                  }
               }
            elif not isinstance( colVal, str ):
               colVal = str( colVal )
            values[ idx ] = {
               "userEnteredValue": {
                  colTypeName: colVal
               }
            }
            if userFormat is not None:
               values[ idx ][ "userEnteredFormat" ] = userFormat
         return {
            "values": values
         }

      # Dates represented in serial format
      # see: https://developers.google.com/sheets/api/reference +
      #      /rest/v4/DateTimeRenderOption#ENUM_VALUES.SERIAL_NUMBER
      EXCEL_DATE = datetime.datetime( 1899, 12, 30 )
      def _convertDateTime( self, inst ):
         # Determine the conversion based on the type
         if isinstance( inst, datetime.datetime ):
            delta = inst - Sheet.Edits.EXCEL_DATE
            return float( delta.days ) + ( float( delta.seconds ) / 86400 )
         else:
            assert isinstance( inst, datetime.date )
            delta = inst - Sheet.Edits.EXCEL_DATE.date()
            return float( delta.days )

# Represents the top-level Google Sheet
class Spreadsheet( object ):
   # Instantiate shheet from Google V4 Sheet response
   def __init__( self, gSpreadsheet, ssid, service ):
      self.sheets_ = {}
      self.id_ = ssid
      self.service_ = service
      self._resetSheets( gSpreadsheet )

   def sheets( self ):
      return self.sheets_.values()

   def sheet( self, sheetName ):
      return self.sheets_.get( sheetName, None )

   # Create a new sheet (note the sheet name cannot match an existing sheet)
   # Specify the column names and key column (which must be an existing column)
   def addSheet( self, sheetName, sheetColNames, keyColName ):
      assert sheetName not in self.sheets_, "Sheet: %s exists" % sheetName
      assert keyColName in sheetColNames, "Key column does not exist"

      # Create the sheetsheet
      sheetRequest = {
         "addSheet": {
            "properties": {
               "title": sheetName,
               "gridProperties": {
                  "rowCount": 0,
                  "columnCount": len( sheetColNames )
               }
            }
         }
      }
      responses = self.execCmds( sheetRequest )[ 'replies' ]
      if responses is None or len( responses ) == 0 or \
         "addSheet" not in responses[ 0 ]  :
         raise Exception( "Error creating sheet" )

      addSheetResponse = responses[ 0]["addSheet" ]
      headerRows = [ None ] * len( sheetColNames )
      for idx, sheetColName in enumerate( sheetColNames ):
         headerRows[ idx ] = {
            "userEnteredValue": {
               "stringValue": sheetColName
            }
         }

      # Add the headers
      headerRqst = [ {
         "appendCells": {
            "sheetId": addSheetResponse[ "properties" ][ "sheetId" ],
            "rows": {
               "values": headerRows
            },
            "fields": "*"
      } } ]
      self.execCmds( headerRqst )

      # And build internal Sheet
      sheetProps = self.getSheetProperties( sheetName )
      newSheet = Sheet( sheetProps, self )
      newSheet.setKeyCol( keyColName )

      return newSheet

   # Request data for sheet from Google Sheets
   def getData( self, sheetRange ):
      return self.service_.getValues( spreadsheetId=self.id_,
                                      sheetRange=sheetRange )

   # Get current spreadsheet properties (num rows, columns & id )
   def getSheetProperties( self, sheetName ):
      sheetRange = "%s!A1:A1" % sheetName
      ssProps = self.service_.getSpreadsheetProperties( self.id_, sheetRange )
      return ssProps[ "sheets" ][0] if len( ssProps[ "sheets" ] ) == 1 else None

   # Execute Google Sheet batchUpdate request for specified commands
   def execCmds( self, commands ):
      return self.service_.batchUpdates( self.id_, commands )

   def service( self ):
      return self.service_

   # Reset all sheets given Google V4 Sheet response
   def _resetSheets( self, gSpreadsheet ):
      sheets = {}
      for gSheet in gSpreadsheet[ "sheets" ]:
         sheet = Sheet( gSheet, self )
         sheets[ sheet.name() ] = sheet
      self.sheets_ = sheets


# Google V4 Sheets Service interface
class Service( sslv4.Service ):

   # Request the Google Sheet properties for 1+ sheets of a given Spreadsheet
   def getSpreadsheetProperties( self, ssId, sheetRange=None ):
      svc = self._spreadsheets()
      if sheetRange is None:
         gSs = svc.get( spreadsheetId=ssId,
                        fields="sheets.properties" ).execute()
      else:
         gSs = svc.get( spreadsheetId=ssId,
                        fields="sheets.properties",
                        ranges=sheetRange ).execute()
      return gSs

   # Create wrapper for Google Sheet and all Sheets
   def getSpreadsheet( self, ssId, sheetRange=None ):
      gSs = self.getSpreadsheetProperties( ssId, sheetRange )
      assert gSs
      return Spreadsheet( gSs, ssId, self )

   # Returns in data in column major order
   def getValues( self, spreadsheetId, sheetRange ):
      userFields = "sheets.data.rowData.values.effectiveValue"
      result = self._spreadsheets().get( spreadsheetId=spreadsheetId,
                                         fields=userFields,
                                         ranges=sheetRange ).execute()
      # Convert to simple matrix
      sheetData = result[ "sheets" ][0] \
                  if "sheets" in result and len( result[ "sheets" ] ) > 0 else {}
      sheetRows = sheetData[ "data" ][0] \
                  if "data" in sheetData and len( sheetData[ "data" ] ) > 0 else {}
      sheetRowData = sheetRows[ "rowData" ] \
                     if "rowData" in sheetRows else []
      retVal = [ None ] * len( sheetRowData )
      for idx, gRow in enumerate( sheetRowData ):
         cols = gRow[ "values" ] if "values" in gRow else []
         retCol = [ None ] * len( cols )
         for jdx, gCol in enumerate( cols ):
            colVal = None
            if "effectiveValue" in gCol:
               gUserVal = gCol[ "effectiveValue" ]
               if "stringValue" in gUserVal:
                  colVal = gUserVal[ "stringValue" ]
               elif "numberValue" in gUserVal:
                  colVal = gUserVal[ "numberValue" ]
               elif "boolValue" in gUserVal:
                  colVal = gUserVal[ "boolValue" ]
            retCol[ jdx ] = colVal
         retVal[ idx ] = retCol
      return retVal

   # Execute a batchUpdate() for the specified Google Sheet
   # Return value depends on executed request
   def batchUpdates( self, ssId, commands ):
      request = {
         "requests": commands,
         "includeSpreadsheetInResponse": False
      }
      return self._spreadsheets().batchUpdate( spreadsheetId=ssId,
                                               body=request ).execute()

   def _spreadsheets( self ):
      return self.service_.spreadsheets()  # pylint: disable=no-member