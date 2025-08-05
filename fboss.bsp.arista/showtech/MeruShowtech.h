// Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef MERU_SHOWTECH_H
#define MERU_SHOWTECH_H

#include "Showtech.h"
#include "ShowtechUtils.h"
#include <filesystem>
#include <memory>
#include <set>
#include <utility>
#include <vector>

namespace showtech {
class MeruShowtech : public Showtech {
public:
  MeruShowtech() : Showtech() {}
  void printPlatformInfo() override;
  // The first CPU i2c bus is unused and takes a long time to scan,
  // so skip scanning.
  std::set<int> i2cBusIgnore() override { return {0}; }

protected:
  std::unique_ptr<PciScdDevice> cpuCpld;
  std::vector<std::unique_ptr<PciScdDevice>> switchcardScds;
  std::unique_ptr<I2cDevice> switchcardCpld;
  // Pair of Power Controller Device and number of pages
  std::vector<std::pair<std::unique_ptr<I2cDevice>, int>> powerCtrlers;
  std::vector<std::unique_ptr<I2cHwmonDevice>> fanCplds;

private:
  int numFansPerCpld = 4;
  void printWeutilInfo();
  void printAllFpgaVersions();
  void printFanInfo();
  void printI2cInfo();
  void printPsuShowtechInfo();
  void printCfmShowtechInfo();
};

class Meru800BiaShowtech : public MeruShowtech {
public:
  Meru800BiaShowtech();
};

class Meru800BfaShowtech : public MeruShowtech {
public:
  Meru800BfaShowtech();
  std::set<int> i2cBusIgnore() override;

private:
  std::set<int> i2cBusesToIgnore;
};

class Glath05a_64oShowtech : public MeruShowtech {
public:
  Glath05a_64oShowtech();
};

} // namespace showtech

#endif // MERU_SHOWTECH_H
