// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "PsuShowtech.h"
#include <cmath>
#include <cstdint>
#include <dirent.h>
#include <fcntl.h>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <linux/i2c-dev.h>
#include <linux/i2c.h>
#include <regex>
#include <set>
#include <sstream>
#include <string>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <tuple>
#include <unistd.h>
#include <vector>

namespace showtech {

double linear11ToDecimal(uint16_t linear11) {
  int16_t exponent = (linear11 >> 11) & 0x1F;
  int16_t mantissa = linear11 & 0x7FF;

  if (exponent & 0x10) {
    exponent = exponent | 0xFFE0;
  }

  if (mantissa & 0x400) {
    mantissa = mantissa | 0xF800;
  }

  double value = mantissa * std::pow(2, exponent);
  return value;
}

// PMBUS Register formats can be found in aid/11144 (Delta), aid/6989 (Arista)
Generic::Generic()
    : commonRegisters{{
          std::make_tuple("MFR_ID", 0x99, 0, ValueType::ASCII),
          std::make_tuple("MFR_MODEL", 0x9A, 0, ValueType::ASCII),
          std::make_tuple("MFR_REVISION", 0x9B, 0, ValueType::ASCII),
          std::make_tuple("MFR_LOCATION", 0x9C, 0, ValueType::ASCII),
          std::make_tuple("MFR_DATE", 0x9D, 0, ValueType::ASCII),
          std::make_tuple("MFR_SERIAL", 0x9E, 0, ValueType::ASCII),
          std::make_tuple("MFR_POUT_MAX", 0xA7, 2, ValueType::LINEAR_11),
          std::make_tuple("PRI_MCU_FW_VERSION", 0xE0, 0, ValueType::ASCII),
          std::make_tuple("SEC_MCU_FW_VERSION", 0xE1, 0, ValueType::ASCII),
          std::make_tuple("STATUS_BYTE", 0x78, 1, ValueType::HEX),
          std::make_tuple("STATUS_WORD", 0x79, 2, ValueType::HEX),
          std::make_tuple("STATUS_VOUT", 0x7A, 1, ValueType::HEX),
          std::make_tuple("STATUS_IOUT", 0x7B, 1, ValueType::HEX),
          std::make_tuple("STATUS_INPUT", 0x7C, 1, ValueType::HEX),
          std::make_tuple("STATUS_TEMPERATURE", 0x7D, 1, ValueType::HEX),
          std::make_tuple("STATUS_CML", 0x7E, 1, ValueType::HEX),
          std::make_tuple("STATUS_FANS_1_2", 0x81, 1, ValueType::HEX),
          std::make_tuple("READ_VIN", 0x88, 2, ValueType::LINEAR_11),
          std::make_tuple("READ_IIN", 0x89, 2, ValueType::LINEAR_11),
          std::make_tuple("READ_VOUT", 0x8B, 2, ValueType::LINEAR_16),
          std::make_tuple("READ_IOUT", 0x8C, 2, ValueType::LINEAR_11),
          std::make_tuple("READ_TEMPERATURE_1", 0x8D, 2, ValueType::LINEAR_11),
          std::make_tuple("READ_TEMPERATURE_2", 0x8E, 2, ValueType::LINEAR_11),
          std::make_tuple("READ_TEMPERATURE_3", 0x8F, 2, ValueType::LINEAR_11),
          std::make_tuple("READ_FAN SPEED_1", 0x90, 2, ValueType::LINEAR_11),
          std::make_tuple("READ_FAN SPEED_2", 0x91, 2, ValueType::LINEAR_11),
          std::make_tuple("READ_POUT", 0x96, 2, ValueType::LINEAR_11),
          std::make_tuple("READ_PIN", 0x97, 2, ValueType::LINEAR_11),
          std::make_tuple("PMBUS_REVISION", 0x98, 1, ValueType::LINEAR_11),
      }},
      voutModeReg(0x20), chipAddr(0x58) {}

std::vector<uint8_t> makeI2cRdwrRequest(const char *i2cDevice, int chipAddr,
                                        uint8_t regAddr, int numBytesToRead) {
  int file;
  std::vector<uint8_t> readBuffer(numBytesToRead);

  if ((file = open(i2cDevice, O_RDWR)) < 0) {
    std::cerr << "Failed to open the i2c bus" << std::endl;
    return {};
  }

  struct i2c_rdwr_ioctl_data ioctlData;
  struct i2c_msg messages[2];

  messages[0].addr = chipAddr;
  messages[0].flags = 0;
  messages[0].len = 1;
  messages[0].buf = &regAddr;

  messages[1].addr = chipAddr;
  messages[1].flags = I2C_M_RD;
  messages[1].len = numBytesToRead;
  messages[1].buf = reinterpret_cast<uint8_t *>(&readBuffer[0]);

  ioctlData.msgs = messages;
  ioctlData.nmsgs = 2;

  if (ioctl(file, I2C_RDWR, &ioctlData) < 0) {
    std::cerr << "Failed to communicate with the device" << std::endl;
    close(file);
    return {};
  }

  close(file);

  return readBuffer;
}

std::vector<uint8_t> readI2c(const char *i2cDevice, int chipAddr,
                             uint8_t regAddr, int numBytesToRead) {
  std::vector<uint8_t> readBuffer;
  uint8_t lengthByte = 0;
  if (numBytesToRead == 0) {
    lengthByte = makeI2cRdwrRequest(i2cDevice, chipAddr, regAddr, 1)[0];
    numBytesToRead = lengthByte + 1;
    readBuffer =
        makeI2cRdwrRequest(i2cDevice, chipAddr, regAddr, numBytesToRead);
    readBuffer.erase(readBuffer.begin());
    return readBuffer;
  } else {
    readBuffer =
        makeI2cRdwrRequest(i2cDevice, chipAddr, regAddr, numBytesToRead);
    return readBuffer;
  }
  return {};
}

/*
 * Searches for the PSU I2C buses in /run/devmap/sensors
 * Extracts the PSU number from the file name
 * Extracts the I2C bus from the symlink
 */
std::vector<std::pair<std::string, std::string>> getPsuI2cBuses() {
  std::string sensorPath = "/run/devmap/sensors/";
  std::set<std::pair<std::string, std::filesystem::path>> psus;

  for (const auto &entry : std::filesystem::directory_iterator(sensorPath)) {
    std::string fileName = entry.path().filename().string();
    if (fileName.find("PSU") == 0) {
      std::filesystem::path psuSymlinkPath =
          std::filesystem::read_symlink(entry.path());
      // Get PSU number from filename, which is in the format PSU#_PMBUS
      static const std::regex pattern("PSU(\\d*)_");
      std::smatch match;
      std::regex_search(fileName, match, pattern);
      std::string psuNum;
      if (match[1].str().empty()) {
        psuNum = "1";
      } else {
        psuNum = match[1].str();
      }

      psus.emplace(psuNum, psuSymlinkPath);
    }
  }

  std::vector<std::pair<std::string, std::string>> psuI2cBusNums;

  for (const auto &[psuNum, psuSymlink] : psus) {
    auto it = psuSymlink.begin();
    // Symlink is in the format: / sys / bus / i2c / devices / 23-0058
    // Fifth level directory contains i2c bus and chip address
    std::advance(it, 5);
    if (it != psuSymlink.end()) {
      std::string i2cBusAndChipAddr = it->string();
      std::size_t dashPos = i2cBusAndChipAddr.find('-');
      if (dashPos != std::string::npos) {
        std::string i2cBus = i2cBusAndChipAddr.substr(0, dashPos);
        psuI2cBusNums.emplace_back(psuNum, i2cBus);
      }
    }
  }

  return psuI2cBusNums;
}

void printPsuInfo() {
  std::vector<std::pair<std::string, std::string>> psuI2cBusNums =
      getPsuI2cBuses();
  for (const auto &psu : psuI2cBusNums) {
    std::cout << "POWER SUPPLY SLOT " << psu.first << " DETAILS" << std::endl;
    std::string device = "/dev/i2c-" + psu.second;
    const char *i2cDevice = device.c_str();
    Generic genericPsu;

    for (const auto &reg : genericPsu.getAllRegisters()) {
      std::vector<uint8_t> regInfo =
          readI2c(i2cDevice, genericPsu.getChipAddr(), std::get<1>(reg),
                  std::get<2>(reg));
      std::cout << std::get<0>(reg) << ": ";
      ValueType valueType = std::get<3>(reg);
      if (valueType == ValueType::ASCII) {
        for (const auto &val : regInfo) {
          std::cout << val;
        }
      } else if (valueType == ValueType::HEX) {
        if (regInfo.size() == 1) {
          std::cout << std::hex << "0x" << std::setw(2) << std::setfill('0')
                    << static_cast<int>(regInfo[0]) << " ";
        } else if (regInfo.size() == 2) {
          uint16_t combinedRegInfo =
              (static_cast<uint16_t>(regInfo[0]) << 8) | regInfo[1];
          std::cout << std::hex << "0x" << std::setw(4) << std::setfill('0')
                    << combinedRegInfo;
        } else {
          std::cout << "Incorrect register data amount read" << std::endl;
        }
      } else if (valueType == ValueType::LINEAR_11) {
        if (regInfo.size() == 1) {
          std::cout << std::hex << "0x" << std::setw(2) << std::setfill('0')
                    << static_cast<int>(regInfo[0]) << " ";
        } else if (regInfo.size() == 2) {
          uint16_t combinedRegInfo =
              (static_cast<uint16_t>(regInfo[1]) << 8) | regInfo[0];
          std::cout << linear11ToDecimal(combinedRegInfo);
        } else {
          std::cout << "Incorrect register data amount read" << std::endl;
        }
      } else if (valueType == ValueType::LINEAR_16) {
        // Special Case: VOUT = VOUT_REG * 2^(VOUT_MODE as 5 bit signed)
        uint16_t combinedRegInfo =
            (static_cast<uint16_t>(regInfo[1]) << 8) | regInfo[0];
        std::vector<uint8_t> voutMode =
            readI2c(i2cDevice, genericPsu.getChipAddr(),
                    genericPsu.getVoutModeReg(), 1);
        voutMode[0] = (voutMode[0] & 0x10)
                          ? (static_cast<int8_t>(voutMode[0] | 0xE0))
                          : voutMode[0];

        double result = static_cast<double>(combinedRegInfo) *
                        std::pow(2.0, static_cast<int8_t>(voutMode[0]));
        std::cout << result;
      }
      std::cout << std::endl;
    }
    std::cout << std::endl;
  }
}

} // namespace showtech
