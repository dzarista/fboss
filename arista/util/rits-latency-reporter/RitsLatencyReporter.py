#!/usr/bin/env python3
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

'''
RitsLatencyReporter tool gets info on all passing RITS autotest jobs
and generates weekly trend on average latency. This info is stored in 
a google sheet where charts can be made from the data.
This tool needs to be run from a homebus or an a4c container.

* Target google sheets document should contain the following sheets 
  and columns in them:
  JobsData: JobId, Test, Dut, Product, ScheduledAt, TestStartTime, Latency
  Trendlines: Product, -4W, -3W, -2W, -1W

* To use a different google sheet document update SHEET_ID variable

* To generate trends for more weeks update NUM_WEEKS variable and update
  Trendlines sheet to contain columns for the additional week
'''

import ArGoogleApps.SpreadsheetLibV4 as spreadsheetLib
import functools
from datetime import datetime
from ArPyOAuth2 import retryHttpSession
from PerforceCommon import P4
from A4.Project import Utils
from A4.Project.Commands import CommandsLib
import pandas as pd
import math

ARJOB_API_URL = "https://arjob-service.infra.corp.arista.io"
NUM_WEEKS = 4
SHEET_ID = "1oi2JQXzzXuJ91JFhPd0xpw8_WLwz3Lg2Zeyqj7RyJTk"

class GSheetColumn:
    JOB_ID = "JobId"
    TEST = "Test"
    DUT = "Dut"
    PRODUCT = "Product"
    SCHEDULE_TIME = "ScheduledAt"
    START_TIME = "TestStartTime"
    LATENCY = "Latency"
    WEEK = "Week"

class RitsLatencyReporter:
    def __init__( self ):
        self.primaryProject = "fboss"
        self.package = "FbossTest"
        self.p4 = P4.p4()
        self.mostRecentChangenum = self.p4.mostRecentChangenum()
        self.setupGSheet()
    
    def setupGSheet( self ):
        self.spreadsheet = spreadsheetLib.Service().getSpreadsheet( SHEET_ID )
        # JobsData sheet for raw data storage
        self.jobsSheet = self.spreadsheet.sheet( "JobsData" )
        assert self.jobsSheet, "JobsData sheet not found" 
        self.jobsSheet.setKeyCol( GSheetColumn.JOB_ID, mustHaveKeyValue=True )
        # TrendLine sheet for trends
        self.trendSheet = self.spreadsheet.sheet( "Trendlines" )
        assert self.trendSheet, "Trendlines sheet not found" 
        self.trendSheet.setKeyCol( GSheetColumn.PRODUCT, mustHaveKeyValue=True )

    def isRitsProject( self, pj ):
        projectConfig = Utils.projectConfigFromP4( self.p4, pj, self.mostRecentChangenum )
        return projectConfig.setting( "bipTopicName" ) != ""

    def currentRitsProjects( self ):
        children = CommandsLib.getChildren( self.p4, self.primaryProject, self.mostRecentChangenum )
        return [ pj[ 1 ] for pj in children.keys() if self.isRitsProject( pj[ 1 ] ) ]

    def queryAristaApi( self, url ):
        with retryHttpSession() as session:
            resp = session.get( url=url )
        assert resp.status_code == 200, f"Api query failed for { url }"
        return resp.json()

    def queryArjob( self, queries ):
        return self.queryAristaApi( f"{ARJOB_API_URL}/jobs?q={queries}" )[ "jobs" ]

    def autotestJobs( self, pj ):
        # Only query passing jobs since failing builds sometimes are scheduled
        # and run immediately while the dut is still grabbed and does not correctly
        # reflect the latency
        queries = f"project=={ pj };type==ptest;package=={ self.package };result==PASS"
        return self.queryArjob( queries )

    def writeJobToSheet( self, testRun ):
        jId = testRun[ "id" ]
        # Calculate latency
        scheduleTime = datetime.fromisoformat( testRun[ "scheduleTime" ] )
        startTime = datetime.fromisoformat( testRun[ "startTime" ] )
        latency = startTime - scheduleTime
        # Write job info to sheet rows
        row = self.jobsSheet.getRow( jId ) or self.jobsSheet.addRow( jId )
        row.set( GSheetColumn.TEST, testRun[ "test" ] )
        # All arista-fboss RITS tests use a single dut
        row.set( GSheetColumn.DUT, testRun[ "duts" ][ 0 ][ "name" ] )
        row.set( GSheetColumn.PRODUCT, testRun[ "duts" ][ 0 ][ "product" ] )
        row.set( GSheetColumn.SCHEDULE_TIME, str(scheduleTime) )
        row.set( GSheetColumn.START_TIME, str(startTime) )
        row.set( GSheetColumn.LATENCY, round( latency.total_seconds() / 3600, 2 ) )

    def writeJobsToSheet( self ):
        projects = self.currentRitsProjects()
        for pj in projects:
            testRuns = self.autotestJobs( pj )
            for tr in testRuns:
                self.writeJobToSheet( tr )
        self.jobsSheet.commitChanges()

    def getJobsAndProductsFromSheet( self ):
        jobs = []
        products = set()
        now = datetime.utcnow()
        for row in self.jobsSheet.getRows():
            product = row.get( GSheetColumn.PRODUCT )
            products.add( product )
            scheduleTime = datetime.fromisoformat( row.get( GSheetColumn.SCHEDULE_TIME ) )
            startTime = datetime.fromisoformat( row.get( GSheetColumn.START_TIME ) )
            latency = startTime - scheduleTime
            week = math.ceil( ( now - startTime ).days / 7 )
            jobs.append( { GSheetColumn.PRODUCT: product, 
                           GSheetColumn.START_TIME: startTime,
                           GSheetColumn.LATENCY: latency,
                           GSheetColumn.WEEK: week } )
        return jobs, products
    
    def generateWeeklyTrends( self ):
        jobs, products = self.getJobsAndProductsFromSheet()
        jobs = pd.DataFrame( jobs )
        result = {}
        for product in products:
            jobsForProduct = jobs.loc[ jobs[ GSheetColumn.PRODUCT ] == product ]
            for i in range( 1, NUM_WEEKS + 1 ):
                weeklyJobs = jobsForProduct.loc[ jobsForProduct[ GSheetColumn.WEEK ] == i ]
                meanLatency = weeklyJobs[ GSheetColumn.LATENCY ].mean()
                result[ product ] = result.get( product, [] ) + [ meanLatency ]
        return result

    def writeTrendsToSheet( self ):
        trend = self.generateWeeklyTrends()
        for product, series in trend.items():
            row = self.trendSheet.getRow( product ) or self.trendSheet.addRow( product )
            for weekN, mean in enumerate( series ):
                mean = round( mean.total_seconds() / 3600, 2 ) if not pd.isnull( mean ) else 0
                row.set( f"-{ weekN + 1 }W", mean )
        self.trendSheet.commitChanges()

    def writeTimestamp( self ):
        label = "Last Updated"
        row = self.trendSheet.getRow( label ) or self.trendSheet.addRow( label )
        timestamp = f"{ datetime.utcnow().isoformat( timespec='minutes' ) } UTC"
        row.set( f"-{ NUM_WEEKS }W", timestamp )
        self.trendSheet.commitChanges()

    def run( self ):
        # Get rits projects, their test runs and record each job in google sheet
        self.writeJobsToSheet()
        # Get data from google sheet and generate trends from it
        self.writeTrendsToSheet()
        self.writeTimestamp()

if __name__ == "__main__":
    reporter = RitsLatencyReporter()
    reporter.run()
