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
  Showtech(bool verbose)
      : verbose_{verbose}, ramdisk_{std::filesystem::exists("/etc/ramdisk")} {}
  virtual ~Showtech() = default;
  void printShowtech();

  std::string version = "1.5";

protected:
  // These should be common between platforms.
  void printVersion();
  void printCpuDetails();
  void printFbossDetails();
  void printWeutil(std::string target);
  void printLspci();
  void printI2cDetect();
  void printL1Info();
  void printLogs();
  void printSensors();
  void printFpgaVersion(std::string name, std::string sysfsPath,
                        std::string combinedRevPath);
  void printFpgaVersion(std::string name, std::string sysfsPath,
                        std::string majorRevPath, std::string minorRevPath);

  // Each platform overrides platform-specific info here.
  virtual void printPlatformInfo() = 0;
  virtual std::set<int> i2cBusIgnore() = 0;

  bool verbose_;
  bool ramdisk_;
};

class GenericShowtech : public Showtech {
public:
  GenericShowtech(bool verbose) : Showtech(verbose) {}
  void printPlatformInfo() override {};
  std::set<int> i2cBusIgnore() override { return {}; }
};
} // namespace showtech

#endif // SHOWTECH_H
