// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef SHOWTECH_H
#define SHOWTECH_H

#include <filesystem>
#include <set>
#include <string>

namespace showtech {
class Showtech {
public:
  Showtech() : ramdisk_{std::filesystem::exists("/etc/ramdisk")} {}
  virtual ~Showtech() = default;
  void printShowtech();

  std::string version = "1.5";

protected:
  // These should be common between platforms.
  void printVersion();
  void printCpuDetails();
  void printFbossDetails();
  void printLspci();
  void printI2cDetect();
  void printL1Info();
  void printLogs();
  void printSensors();
  void printWeutilDetails();
  void printFwutilDetails();
  void print_fboss2_show_cmd(std::string cmd);

  // Each platform overrides platform-specific info here.
  virtual void printPlatformInfo() = 0;
  virtual std::set<int> i2cBusIgnore() = 0;

  bool ramdisk_;
};

class GenericShowtech : public Showtech {
public:
  GenericShowtech() : Showtech() {}
  void printPlatformInfo() override {};
  std::set<int> i2cBusIgnore() override { return {}; }
};
} // namespace showtech

#endif // SHOWTECH_H
