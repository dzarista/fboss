// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef SHOWTECH_PSUSHOWTECH_H
#define SHOWTECH_PSUSHOWTECH_H

#include <array>
#include <string>
#include <tuple>
#include <vector>

namespace showtech {

double linear11ToDecimal(uint16_t linear11);
double linear16ToDecimal(uint16_t linear16);
std::vector<uint8_t> makeI2cRdwrRequest(const char *i2cDevice, int chipAddr,
                                        uint8_t regAddr, int numBytesToRead);
std::vector<uint8_t> readI2c(const char *i2cDevice, int chipAddr,
                             uint8_t regAddr, int numBytesToRead);
std::vector<std::pair<std::string, std::string>> getPsuI2cBuses();
void printPsuInfo();

enum class ValueType { ASCII, HEX, LINEAR_11, LINEAR_16 };

class Generic {
public:
  Generic();
  static const int REGISTER_COUNT = 29;
  int getVoutModeReg() const { return voutModeReg; }
  int getChipAddr() const { return chipAddr; }
  const std::array<std::tuple<std::string, int, int, ValueType>, REGISTER_COUNT>
      &getAllRegisters() const {
    return commonRegisters;
  }

private:
  std::array<std::tuple<std::string, int, int, ValueType>, REGISTER_COUNT>
      commonRegisters;
  int voutModeReg;
  int chipAddr;
};

} // namespace showtech
#endif // SHOWTECH_PSUSHOWTECH_H
