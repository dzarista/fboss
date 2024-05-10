// Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef MERU_SHOWTECH_H
#define MERU_SHOWTECH_H

#include "Showtech.h"
#include "ShowtechUtils.h"
#include <filesystem>
#include <memory>
#include <set>

namespace showtech {
class MeruShowtech : public Showtech {
public:
  MeruShowtech(bool verbose) : Showtech(verbose) {}
  std::string getVersion() override { return "1.1"; }
  void printPlatformInfo() override;
  // The first CPU i2c bus is unused and takes a long time to scan,
  // so skip scanning.
  std::set<int> i2cBusIgnore() override { return {0}; }

private:
  int numFansPerCpld = 4;
  void printFpgaVersion(std::string name,
                        std::string major_rev_path,
                        std::string minor_rev_path);
  void printAllFpgaVersions();
  void printFanInfo();
  void printI2cInfo();
};
} // namespace showtech

#endif // MERU_SHOWTECH_H
