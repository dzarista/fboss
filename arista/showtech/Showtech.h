// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef SHOWTECH_H
#define SHOWTECH_H

#include <set>
#include <string>

namespace showtech {
class Showtech {
public:
  Showtech(bool verbose) { verbose_ = verbose; }
  virtual ~Showtech() = default;
  void printShowtech();

protected:
  // These should be common between platforms.
  void printVersion();
  void printCpuDetails();
  void printWeutil(std::string target);
  void printI2cDetect();
  void printL1Info();
  void printLogs();

  // Each platform overrides platform-specific info here.
  virtual std::string getVersion() { return "0.0"; }
  virtual void printPlatformInfo() = 0;
  virtual std::set<int> i2cBusIgnore() = 0;

  bool verbose_;
};
} // namespace showtech

#endif // SHOWTECH_H
