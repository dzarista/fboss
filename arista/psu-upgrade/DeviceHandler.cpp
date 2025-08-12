// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "DeviceHandler.h"
#include "smbus.h"
#include <fcntl.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <linux/i2c-dev.h>
#include <string>
#include <sys/ioctl.h>
#include <syslog.h>
#include <unistd.h>
#include <vector>

namespace update {

bool writeNullByte(int psuFd, uint8_t regAddr) {
  if (i2c_smbus_write_byte(psuFd, regAddr) < 0) {
    return false;
  }
  return true;
}

bool writeByte(int psuFd, uint8_t regAddr, uint8_t value) {
  if (i2c_smbus_write_byte_data(psuFd, regAddr, value) < 0) {
    return false;
  }
  return true;
}

bool writeBlock(int psuFd, uint8_t regAddr, std::vector<uint8_t> &data) {
  uint8_t length = data.size() <= 32 ? data.size() : 32;
  if (i2c_smbus_write_block_data(psuFd, regAddr, length, data.data()) < 0) {
    return false;
  }
  return true;
}

int readByte(int psuFd, uint8_t regAddr) {
  int regVal = i2c_smbus_read_byte_data(psuFd, regAddr);
  return regVal;
}

int readWord(int psuFd, uint8_t regAddr) {
  int regVal = i2c_smbus_read_word_data(psuFd, regAddr);
  return regVal;
}

bool readBlock(int psuFd, uint8_t regAddr, std::vector<uint8_t> &buffer) {
  if (i2c_smbus_read_block_data(psuFd, regAddr, buffer.data()) < 0) {
    return false;
  }
  return true;
}

std::vector<uint8_t> readBinaryFile(const std::string &filename) {
  if (!std::filesystem::exists(filename)) {
    std::cerr << "File does not exist" << std::endl;
    return {};
  }

  std::ifstream file(filename, std::ios::binary);
  std::vector<uint8_t> buffer(std::istreambuf_iterator<char>(file), {});
  return buffer;
}

int getPsuCount() {
  int psuCount = 0;
  std::string sensorPath = "/run/devmap/sensors/";
  for (const auto &entry : std::filesystem::directory_iterator(sensorPath)) {
    std::string fileName = entry.path().filename().string();
    if (fileName.find("PSU") == 0) {
      psuCount++;
    }
  }
  return psuCount;
}

bool isFileContents1(const std::filesystem::path &filePath) {
  std::ifstream file(filePath);
  char content;
  file >> content;
  return content == '1';
}

bool isPsuPresent(int psuNum) {
  std::string suffix = "psu" + std::to_string(psuNum) + "_present";
  if (std::filesystem::exists(vprPsuInfoIn)) {
    return isFileContents1(vprPsuInfoIn / suffix);
  } else if (std::filesystem::exists(wlrPsuInfoIn)) {
    return isFileContents1(wlrPsuInfoIn / suffix);
  } else {
    std::cout << "Cannot find PSU info" << std::endl;
    return false;
  }
}

bool isPsuPowerOk(int psuNum) {
  std::string inputSuffix = "psu" + std::to_string(psuNum) + "_input_ok";
  std::string outputSuffix = "psu" + std::to_string(psuNum) + "_output_ok";
  if (std::filesystem::exists(vprPsuInfoIn)) {
    return isFileContents1(vprPsuInfoIn / inputSuffix) &&
           isFileContents1(vprPsuInfoIn / outputSuffix);
  } else if (std::filesystem::exists(wlrPsuInfoIn)) {
    return isFileContents1(wlrPsuInfoIn / inputSuffix) &&
           isFileContents1(wlrPsuInfoIn / outputSuffix);
  } else {
    std::cout << "Cannot find PSU info" << std::endl;
    return false;
  }
}

std::string getPsuI2cBus(int psuNum) {
  std::filesystem::path psuPath("/run/devmap/sensors/PSU" +
                                std::to_string(psuNum) + "_PMBUS");
  if (std::filesystem::exists(psuPath)) {
    std::filesystem::path psuSymlinkPath =
        std::filesystem::read_symlink(psuPath);
    auto it = psuSymlinkPath.begin();
    // Symlink is in the format: / sys / bus / i2c / devices / 23-0058
    // Fifth level directory contains i2c bus and chip address
    std::advance(it, 5);
    if (it != psuSymlinkPath.end()) {
      std::string i2cBusAndChipAddr = it->string();
      std::size_t dashPos = i2cBusAndChipAddr.find('-');
      if (dashPos != std::string::npos) {
        std::string i2cBus = i2cBusAndChipAddr.substr(0, dashPos);
        return i2cBus;
      }
    }
  }
  return "";
}

int openI2cBus(std::string i2cBus) {
  std::string devicePath = "/dev/i2c-" + i2cBus;
  int fd = open(devicePath.c_str(), O_RDWR);
  if (fd < 0) {
    syslog(LOG_WARNING, "Failed to open i2c device %s, errno=%d",
           i2cBus.c_str(), errno);
    return -1;
  }

  if (ioctl(fd, I2C_SLAVE_FORCE, chipAddr) < 0) {
    syslog(LOG_WARNING, "Failed to open slave @ address 0x%x, errno=%d",
           chipAddr, errno);
    close(fd);
    return -1;
  }
  return fd;
}

} // namespace update
