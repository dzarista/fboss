#!/usr/bin/env python3
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import csv

def string_to_bool(s):
   s = s.lower()
   if s == "true":
      return True
   elif s == "false":
      return False
   else:
      raise ValueError("Invalid boolean string")


def string_to_int_empty_as_zero(val):
   if val == "":
      return 0
   return int(val)

class TestRun:
   def __init__(self, has_run, suite, package, test, aggregate, test_type,
                passes, fails, NAs, timeouts, last_result, last_date,
                last_build_version, variants):
      self.has_run = string_to_bool(has_run)
      self.suite = suite
      self.package = package
      self.test_name = test
      self.test_type = test_type
      self.aggregate = string_to_bool(aggregate)
      self.last_result = last_result
      self.last_date = last_date
      self.last_build_version = last_build_version
      self.variants = variants
      self.passes = string_to_int_empty_as_zero(passes)
      self.fails = string_to_int_empty_as_zero(fails)
      self.NAs = string_to_int_empty_as_zero(NAs)
      self.timeouts = string_to_int_empty_as_zero(timeouts)
      self.runs = self.passes + self.fails + self.timeouts
      self.pass_rate = self.passes / self.runs if self.runs else 0


class SuiteReport:
   def __init__(self, fullname, runs, passed, failed, pass_rate,
                residual_pass_rate, coverage, children=None):
      # These fields are populated by 'a suite report --json' json file
      self.custom_name = ""
      self.fullname = fullname
      self.runs = runs
      self.passed = passed
      self.failed = failed
      self.pass_rate = pass_rate
      self.residual_pass_rate = residual_pass_rate
      self.coverage = coverage
      self.children = [] if children is None else children

      # Tests are populated by 'a suite report --cr' csv file
      self.test_runs = []

   @classmethod
   def from_json(cls, json_data):
      if isinstance(json_data, dict):
         suite_rp = cls(
            json_data["full_name"],
            json_data["runs"],
            json_data["passed"],
            json_data["failed"],
            json_data["pass%"],
            json_data["residual_pass%"],
            json_data["coverage"],
         )
         for child_data in json_data["children"]:
            child_node = cls.from_json(child_data)
            suite_rp.children.append(child_node)
         return suite_rp
      else:
         raise ValueError("Unexpected JSON data format")

   def set_custom_name(self, name):
      self.custom_name = name

   def update_passed_failed(self, passed, failed):
      self.passed = passed
      self.failed = failed
      self.pass_rate = self.passed / (self.passed + self.failed) * 100

   def add_tests_from_csv(self, csv_file):
      with open(csv_file, "r") as csvfile:
         reader = csv.DictReader(csvfile)
         for row in reader:
            if not bool(string_to_bool(row["aggregate"])):
               test_run = TestRun(**row)
               self.test_runs.append(test_run)
