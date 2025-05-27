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

class PowerSupply {
public:
  using Register = std::tuple<std::string, int, int, ValueType>;

  PowerSupply(int bus, int chipAddr = 0x58, int voutModeReg = 0x20);

  int getBus() const { return m_bus; }
  int getVoutModeReg() const { return m_voutModeReg; }
  int getChipAddr() const { return m_chipAddr; }
  const std::vector<Register> &getAllRegisters() const { return m_registers; }

protected:
  int m_bus{};
  int m_chipAddr{};
  int m_voutModeReg{};
  std::vector<Register> m_registers{};

  void _removeRegisters(const std::vector<Register> &toRemove);
  void _addRegisters(const std::vector<Register> &toAdd);
};

class GenericPsu : public PowerSupply {
public:
  GenericPsu(int bus, int chipAddr = 0x58, int voutModeReg = 0x20);
};

class LiteonPsu : public GenericPsu {
public:
  LiteonPsu(int bus, int chipAddr = 0x58, int voutModeReg = 0x20);
};

class AristaPsu : public GenericPsu {
public:
  AristaPsu(int bus, int chipAddr = 0x58, int voutModeReg = 0x20);
};

class Delta1600WPsu : public GenericPsu {
public:
  Delta1600WPsu(int bus, int chipAddr = 0x58, int voutModeReg = 0x20);
};

} // namespace showtech
#endif // SHOWTECH_PSUSHOWTECH_H
