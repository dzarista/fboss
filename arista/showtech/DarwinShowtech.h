// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef DARWIN_SHOWTECH_H
#define DARWIN_SHOWTECH_H

#include "Showtech.h"
#include "ShowtechUtils.h"
#include <memory>
#include <set>
#include <string>

namespace showtech {
class DarwinShowtech : public Showtech {
public:
  DarwinShowtech(bool verbose, std::string product)
      : Showtech(verbose), product(product) {}
  void printPlatformInfo() override;
  std::set<int> i2cBusIgnore() override { return {}; }

private:
  void printSwitchcardPowergood();
  void printFpgaVersion(std::string target, std::string sysfsPath);
  void printAllFpgaVersions();
  void printPemInfo();
  void printFanspinnerInfo();
  void printFanInfo();
  void printPsuShowtechInfo();
  void printRackmonInfo();
  void printI2cInfo();
  std::string product;

  // Platform devices defined here.
  std::unique_ptr<PciScdDevice> cpuCpld;
  std::unique_ptr<PciScdDevice> switchcardScd;
  std::unique_ptr<I2cDevice> switchcardCpld;
  std::unique_ptr<I2cHwmonDevice> fanCpld;
  std::unique_ptr<I2cHwmonDevice> fanspinner;
  std::unique_ptr<I2cGpioDevice> pca9539;
};
} // namespace showtech

#endif // DARWIN_SHOWTECH_H
