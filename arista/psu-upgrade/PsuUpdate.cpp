// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "PsuUpdate.h"
#include "smbus.h"
#include <algorithm>
#include <cerrno>
#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstring>
#include <fcntl.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <linux/i2c-dev.h>
#include <linux/i2c.h>
#include <sys/ioctl.h>
#include <syslog.h>
#include <thread>
#include <unistd.h>
#include <vector>

namespace update {

static int globalFd = -1;
static const int chipAddr = 0x58;
static deltaHdrType deltaHdr;
static aristaHdrType aristaHdr;

bool writeNullByte(int psuFd, uint8_t regAddr) {
  if (i2c_smbus_write_byte(psuFd, regAddr) < 0) {
    std::cerr << "Failed to write null byte" << std::endl;
    return false;
  }
  return true;
}

bool writeByte(int psuFd, uint8_t regAddr, uint8_t value) {
  if (i2c_smbus_write_byte_data(psuFd, regAddr, value) < 0) {
    std::cerr << "Failed to write byte" << std::endl;
    return false;
  }
  return true;
}

bool writeBlock(int psuFd, uint8_t regAddr, std::vector<uint8_t> &data) {
  uint8_t length = data.size() <= 32 ? data.size() : 32;
  if (i2c_smbus_write_block_data(psuFd, regAddr, length, data.data()) < 0) {
    std::cerr << "Failed to write block" << std::endl;
    return false;
  }
  return true;
}

int readByte(int psuFd, uint8_t regAddr) {
  int regVal = i2c_smbus_read_byte_data(psuFd, regAddr);
  if (regVal < 0) {
    std::cerr << "Failed to read byte" << std::endl;
  }

  return regVal;
}

int readWord(int psuFd, uint8_t regAddr) {
  int regVal = i2c_smbus_read_word_data(psuFd, regAddr);
  if (regVal < 0) {
    std::cerr << "Failed to read word" << std::endl;
  }
  return regVal;
}

bool readBlock(int psuFd, uint8_t regAddr, std::vector<uint8_t> &buffer) {
  if (i2c_smbus_read_block_data(psuFd, regAddr, buffer.data()) < 0) {
    std::cerr << "Failed to read block" << std::endl;
    return false;
  }
  return true;
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
  if (std::filesystem::exists(vprPsuInfoIn)) {
    std::string suffix = "psu" + std::to_string(psuNum) + "_present";
    return isFileContents1(vprPsuInfoIn / suffix);
  } else if (std::filesystem::exists(wlrPsuInfoIn)) {
    std::string suffix = "psu" + std::to_string(psuNum) + "_prsnt";
    return isFileContents1(wlrPsuInfoIn / suffix);
  } else {
    std::cout << "Cannot find PSU info" << std::endl;
    return false;
  }
}

bool isPsuPowerOk(int psuNum) {
  if (std::filesystem::exists(vprPsuInfoIn)) {
    std::string inputSuffix = "psu" + std::to_string(psuNum) + "_input_ok";
    std::string outputSuffix = "psu" + std::to_string(psuNum) + "_output_ok";
    return isFileContents1(vprPsuInfoIn / inputSuffix) &&
           isFileContents1(vprPsuInfoIn / outputSuffix);
  } else if (std::filesystem::exists(wlrPsuInfoIn)) {
    std::string inputSuffix = "psu" + std::to_string(psuNum) + "_in_ok";
    std::string outputSuffix = "psu" + std::to_string(psuNum) + "_out_ok";
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

void exitHandler( int signum ) {
  std::cout << std::endl << "PSU update abort!" << std::endl;
  syslog(LOG_WARNING, "PSU update abort!");
  close(globalFd);
  std::filesystem::remove("/var/run/psu-upgrade.pid");
  exit(signum);
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

bool parseDeltaImgHdr(std::vector<uint8_t> header) {
  int index = 0;
  for (int i = 0; i < DELTA_ID_LEN; i++) {
    deltaHdr.fw_id[i] = header[index++];
  }

  if (std::memcmp(deltaHdr.fw_id, DELTA_MODEL, DELTA_ID_LEN) != 0) {
    std::cout << "PSU Model does not match with model of file" << std::endl;
    return false;
  }

  deltaHdr.compatibility = header[index++];
  deltaHdr.sec_data_start = header[index++];
  deltaHdr.sec_data_start |= header[index++] << 8;
  index += DELTA_RESERVED_LINE_0;
  deltaHdr.pri_fw_major = header[index++];
  deltaHdr.pri_fw_minor = header[index++];
  deltaHdr.pri_crc[0] = header[index++];
  deltaHdr.pri_crc[1] = header[index++];
  index += DELTA_RESERVED_LINE_1;
  deltaHdr.sec_fw_major = header[index++];
  deltaHdr.sec_fw_minor = header[index++];
  deltaHdr.sec_crc[0] = header[index++];
  deltaHdr.sec_crc[1] = header[index];

  std::cout << "Model: " << deltaHdr.fw_id << std::endl;
  std::cout << "HW Compatibility: "
            << static_cast<unsigned int>(deltaHdr.compatibility) << std::endl;
  std::cout << "Primary Ver: "
            << static_cast<unsigned int>(deltaHdr.pri_fw_major) << "."
            << static_cast<unsigned int>(deltaHdr.pri_fw_minor) << std::endl;
  std::cout << "Secondary Ver: "
            << static_cast<unsigned int>(deltaHdr.sec_fw_major) << "."
            << static_cast<unsigned int>(deltaHdr.sec_fw_minor) << std::endl;
  return true;
}

void psuSetWp(int psuFd, uint8_t mode) {
  if (mode == ENABLE_ALL_CMDS) {
    std::cout << "-- Write Protect Disabled --" << std::endl;
  } else {
    std::cout << "-- Write Protect Enabled --" << std::endl;
  }
  writeByte(psuFd, WRITE_PROTECT, mode);
}

void deltaUnlockUpgrade(int psuFd) {
  std::vector<uint8_t> data(DELTA_ID_LEN + 1);
  data[DELTA_ID_LEN] = deltaHdr.compatibility;
  for (int i = 0; i < DELTA_ID_LEN; i++) {
    data[i] = DELTA_MODEL[i];
  }
  psuSetWp(psuFd, ENABLE_ALL_CMDS);
  writeBlock(psuFd, DELTA_UNLOCK_UPGRADE, data);
}

int bootFlagRdwr(int psuFd, uint8_t regAddr, uint8_t mode, Operation op) {
  if (op == Operation::Write) {
    if (mode == BOOT_MODE) {
      std::cout << "-- Bootloader Mode --" << std::endl;
    } else {
      std::cout << "-- Reset PSU --" << std::endl;
    }
    return writeByte(psuFd, regAddr, mode);
  } else {
    return readByte(psuFd, regAddr);
  }
  return -1;
}

bool deltaCrcCheck(int psuFd, Section section) {
  uint8_t fileCrc[2];
  if (section == Section::Primary) {
    std::copy(deltaHdr.pri_crc, deltaHdr.pri_crc + 2, fileCrc);
  } else {
    std::copy(deltaHdr.sec_crc, deltaHdr.sec_crc + 2, fileCrc);
  }

  int rawCrc = readWord(psuFd, CRC_CHECK);
  uint8_t currCrc[2];
  currCrc[0] = rawCrc & 0xFF;
  currCrc[1] = (rawCrc >> 8) & 0xFF;
  if ((currCrc[0] != fileCrc[0]) || (currCrc[1] != fileCrc[1])) {
    std::cerr << "CRC check failed: " << std::hex
              << static_cast<int>(currCrc[0]) << " "
              << static_cast<int>(currCrc[1])
              << " != " << static_cast<int>(fileCrc[0]) << " "
              << static_cast<int>(fileCrc[1]) << std::endl;
    return false;
  }

  return true;
}

bool deltaFwTransmitLine(int psuFd, int lineNum,
                         const std::vector<uint8_t> &data, int delay,
                         Section section) {
  std::vector<uint8_t> block(BYTES_PER_LINE + 2);
  block[0] = lineNum & 0xFF;
  block[1] = (lineNum >> 8) & 0xFF;
  size_t startWriteFrom = lineNum * BYTES_PER_LINE;
  std::copy(data.begin() + startWriteFrom,
            data.begin() + startWriteFrom + BYTES_PER_LINE, block.begin() + 2);

  writeBlock(psuFd, DATA_TO_RAM, block);
  if (lineNum == 3) {
    delay += POST_HEADER_DELAY;
  }
  std::this_thread::sleep_for(std::chrono::milliseconds(delay));
  int deltaBootFlagVal =
      bootFlagRdwr(psuFd, DELTA_BOOT_FLAG, BOOT_MODE, Operation::Read);
  if ((deltaBootFlagVal & 0x20)) {
    std::cout << "-- FW transmission error --" << std::endl;
    return false;
  }

  if (section == Section::Secondary) {
    if ((deltaBootFlagVal & 0xF) != 0xD) {
      std::cout << "-- FW transmission error -- " << std::endl;
      return false;
    }
  } else {
    if ((deltaBootFlagVal & 0xF) != 0xC) {
      std::cout << "-- FW transmission error --" << std::endl;
      return false;
    }
  }
  return true;
}

bool deltaFwTransmitSection(int psuFd, int startLine, int endLine,
                            const std::vector<uint8_t> &data, int delay,
                            Section section) {
  int lineNum;
  int linesUploaded = 0;

  std::cout << std::dec << "Beginning transmit of lines " << startLine << " to "
            << endLine << std::endl;
  for (lineNum = startLine; lineNum < endLine; lineNum++) {

    if (!deltaFwTransmitLine(psuFd, lineNum, data, delay, section)) {
      std::cerr << "Failed to write a line, aborting" << std::endl;
      return false;
    }
    linesUploaded++;
    std::cout << "-- " << std::dec << linesUploaded << " lines uploaded --\r";
  }
  std::cout << std::endl;
  if (startLine < DELTA_NUM_HEADER_LINES) {
    std::this_thread::sleep_for(std::chrono::milliseconds(POST_HEADER_DELAY));
  } else {
    writeNullByte(psuFd, DATA_TO_FLASH);
    std::this_thread::sleep_for(std::chrono::milliseconds(FLASH_DELAY));

    if (startLine < deltaHdr.sec_data_start) {
      return deltaCrcCheck(psuFd, Section::Primary);
    } else {
      return deltaCrcCheck(psuFd, Section::Secondary);
    }
  }
  return true;
}

bool deltaFwTransmit(int psuFd, const std::string &filePath) {
  std::vector<uint8_t> data = readBinaryFile(filePath);
  if (data.empty()) {
    return false;
  }

  std::cout << "-- Transmit Header -- " << std::endl;
  if (!deltaFwTransmitSection(psuFd, 0, DELTA_NUM_HEADER_LINES, data,
                              HEADER_DELAY, Section::Header)) {
    return false;
  }

  std::cout << "-- Transmit Primary Firmware -- " << std::endl;
  if (!deltaFwTransmitSection(psuFd, DELTA_NUM_HEADER_LINES,
                              deltaHdr.sec_data_start, data, PRIMARY_DELAY,
                              Section::Primary)) {
    return false;
  }

  std::cout << "-- Transmit Secondary Firmware -- " << std::endl;
  if (!deltaFwTransmitSection(psuFd, deltaHdr.sec_data_start,
                              data.size() / BYTES_PER_LINE, data,
                              SECONDARY_DELAY, Section::Secondary)) {
    return false;
  }

  return true;
}

bool updateDeltaPsu(int psuFd, int psuNum, std::string file) {

  if (ioctl(psuFd, I2C_PEC, 1) < 0) {
    std::cerr << "Could not enable I2C_PEC" << std::endl;
    return false;
  }

  int deltaBootFlagVal =
      bootFlagRdwr(psuFd, DELTA_BOOT_FLAG, BOOT_MODE, Operation::Read);

  if (!(deltaBootFlagVal & DELTA_PSU_BOOT_UNLOCKED_BOOTLOADER_MASK) &&
      !isPsuPowerOk(psuNum)) {
    std::cout << "PSU " << psuNum
              << " power is not ok. Verify that the PSU is conneted to AC "
                 "power supply."
              << std::endl;
    return false;
  }

  deltaUnlockUpgrade(psuFd);
  std::this_thread::sleep_for(std::chrono::milliseconds(DELTA_UNLOCK_DELAY));
  bootFlagRdwr(psuFd, DELTA_BOOT_FLAG, BOOT_MODE, Operation::Write);
  std::this_thread::sleep_for(std::chrono::milliseconds(DELTA_BOOT_FLAG_DELAY));
  if ((bootFlagRdwr(psuFd, DELTA_BOOT_FLAG, BOOT_MODE, Operation::Read) &
       0xF) == 0xD) {
    std::cout << "-- Secondary MCU Selected, Reverting to Primary --"
              << std::endl;
    bootFlagRdwr(psuFd, DELTA_BOOT_FLAG, NORMAL_MODE, Operation::Write);
    std::this_thread::sleep_for(
        std::chrono::milliseconds(DELTA_BOOT_FLAG_DELAY));
    deltaUnlockUpgrade(psuFd);
    std::this_thread::sleep_for(std::chrono::milliseconds(DELTA_UNLOCK_DELAY));
    bootFlagRdwr(psuFd, DELTA_BOOT_FLAG, BOOT_MODE, Operation::Write);
    std::this_thread::sleep_for(
        std::chrono::milliseconds(DELTA_BOOT_FLAG_DELAY));
  }

  if ((bootFlagRdwr(psuFd, DELTA_BOOT_FLAG, BOOT_MODE, Operation::Read) &
       0xF) != 0xC) {
    std::cout << "-- Set Bootloader Mode Error --" << std::endl;
    return false;
  }

  deltaFwTransmit(psuFd, file);

  deltaBootFlagVal =
      bootFlagRdwr(psuFd, DELTA_BOOT_FLAG, NORMAL_MODE, Operation::Write);
  std::this_thread::sleep_for(std::chrono::milliseconds(DELTA_BOOT_FLAG_DELAY));

  psuSetWp(psuFd, DELTA_OPERATION_PAGE_ONLY);

  deltaBootFlagVal =
      bootFlagRdwr(psuFd, DELTA_BOOT_FLAG, BOOT_MODE, Operation::Read);
  if ((deltaBootFlagVal & 0x7) == 0x4) {
    if (deltaBootFlagVal & 0x80) {
      std::cout << "-- Primary FW Identifier Error --" << std::endl;
      return false;
    } else if (deltaBootFlagVal & 0x40) {
      std::cout << "-- Primary CRC16 Application Checksum Wrong --"
                << std::endl;
      return false;
    }
  } else if ((deltaBootFlagVal & 0x7) == 0x5) {
    if (deltaBootFlagVal & 0x80) {
      std::cout << "-- Secondary FW Identifier Error --" << std::endl;
      return -1;
    } else if (deltaBootFlagVal & 0x40) {
      std::cout << "-- Secondary CRC16 Application Checksum Wrong --"
                << std::endl;
      return false;
    }
  }

  std::cout << "-- Upgrade Done --" << std::endl;
  return true;
}

bool parseAristaImgHdr(std::vector<uint8_t> header) {
  int index = 0;
  for (int i = 0; i < ARISTA_ID_LEN; i++) {
    aristaHdr.fw_id[i] = header[index++];
  }

  if (std::memcmp(aristaHdr.fw_id, "ECD25010017", ARISTA_ID_LEN) != 0) {
    std::cout << "PSU Model does not match with model of file" << std::endl;
    return false;
  }

  aristaHdr.compatibility = header[index++];
  index += ARISTA_RESERVED_LINE_0;
  aristaHdr.pri_fw_end_line = header[index++];
  aristaHdr.pri_fw_end_line |= header[index++] << 8;
  aristaHdr.pri_crc[0] = header[index++];
  aristaHdr.pri_crc[1] = header[index++];
  index += ARISTA_RESERVED_LINE_1;
  aristaHdr.sec_fw_end_line = header[index++];
  aristaHdr.sec_fw_end_line |= header[index++] << 8;
  aristaHdr.sec_crc[0] = header[index++];
  aristaHdr.sec_crc[1] = header[index++];
  index += ARISTA_RESERVED_LINE_1;
  aristaHdr.pri_reset_flag = (uint16_t)(header[index++] << 8);
  aristaHdr.pri_reset_flag |= header[index++];
  aristaHdr.sec_reset_flag = (uint16_t)(header[index++] << 8);
  aristaHdr.sec_reset_flag |= header[index++];
  aristaHdr.pri_update_flag = (uint16_t)(header[index++] << 8);
  aristaHdr.pri_update_flag |= header[index++];
  aristaHdr.sec_update_flag = (uint16_t)(header[index++] << 8);
  aristaHdr.sec_update_flag |= header[index++];

  std::cout << "Model: " << aristaHdr.fw_id << std::endl;
  std::cout << "HW Compatibility: "
            << static_cast<unsigned int>(aristaHdr.compatibility) << std::endl;
  return true;
}

void aristaUnlockUpgrade(int psuFd) {
  std::vector<uint8_t> data(ARISTA_ID_LEN + 1);
  data[ARISTA_ID_LEN] = aristaHdr.compatibility;
  for (int i = 0; i < ARISTA_ID_LEN; i++) {
    data[i] = ARISTA_MODEL[i];
  }
  psuSetWp(psuFd, ENABLE_ALL_CMDS);
  writeBlock(psuFd, ARISTA_UNLOCK_UPGRADE, data);
}

bool updateAristaPsu(int psuFd, std::string file) {
  aristaUnlockUpgrade(psuFd);
  std::this_thread::sleep_for(std::chrono::milliseconds(ARISTA_UNLOCK_DELAY));
  bootFlagRdwr(psuFd, ARISTA_BOOT_FLAG, BOOT_MODE, Operation::Write);
  std::this_thread::sleep_for(
      std::chrono::milliseconds(ARISTA_BOOT_FLAG_DELAY));
  std::vector<uint8_t> data = readBinaryFile(file);

  for (int lineNum = 0; lineNum <= aristaHdr.sec_fw_end_line / 2; lineNum++) {
    std::vector<uint8_t> block(I2C_SMBUS_BLOCK_MAX);
    size_t startWriteFrom = lineNum * I2C_SMBUS_BLOCK_MAX;
    std::copy(data.begin() + startWriteFrom,
              data.begin() + startWriteFrom + I2C_SMBUS_BLOCK_MAX,
              block.begin());

    writeBlock(psuFd, ARISTA_DATA_REG, block);
    printf(" %d / %u lines written\r", lineNum, aristaHdr.sec_fw_end_line / 2);
    std::this_thread::sleep_for(std::chrono::milliseconds(ARISTA_LINE_DELAY));
  }
  std::cout << std::endl;
  bootFlagRdwr(psuFd, ARISTA_BOOT_FLAG, NORMAL_MODE, Operation::Write);
  std::this_thread::sleep_for(std::chrono::milliseconds(ARISTA_ENDING_DELAY));
  std::cout << "Upgrade Done" << std::endl;
  return true;
}

bool updatePsu(int psuNum, std::string file, std::string vendor) {

  std::signal( SIGHUP, exitHandler );
  std::signal( SIGINT, exitHandler );
  std::signal( SIGTERM, exitHandler );
  std::signal( SIGQUIT, exitHandler );

  std::string psuI2cBus = getPsuI2cBus(psuNum);
  int psuFd = openI2cBus(psuI2cBus);
  globalFd = psuFd;
  if (psuFd < 0) {
    std::cerr << "Failed to open i2c" << std::endl;
    close(psuFd);
    std::filesystem::remove("/var/run/psu-upgrade.pid");
    return false;
  }

  std::string i2cDevice = "/dev/i2c-" + psuI2cBus;

  if (vendor == "Delta") {
    std::vector<uint8_t> mfrModel(DELTA_ID_LEN);
    readBlock(psuFd, DELTA_MFR_MODEL_REG_ADDR, mfrModel);
    std::string mfrModelStr = std::string(mfrModel.begin(), mfrModel.end());
    if (mfrModelStr == DELTA_MODEL) {
      std::cout << "Updating Delta Model" << std::endl;
      std::vector<uint8_t> deltaHdrBinary = readBinaryFile(file);
      if (deltaHdrBinary.empty()) {
        return false;
      }
      if (!parseDeltaImgHdr(deltaHdrBinary)) {
        return false;
      }
      updateDeltaPsu(psuFd, psuNum, file);
    } else {
      std::cout << "PSU Model does not match with model of file" << std::endl;
      return false;
    }
  }

  else if (vendor == "Arista") {
    std::vector<uint8_t> mfrModel(ARISTA_ID_LEN);
    readBlock(psuFd, ARISTA_MFR_MODEL_REG_ADDR, mfrModel);
    std::string mfrModelStr = std::string(mfrModel.begin(), mfrModel.end());
    if (mfrModelStr == ARISTA_MODEL) {
      std::cout << "Updating Arista Model" << std::endl;

      std::vector<uint8_t> aristaHdrBinary = readBinaryFile(file);
      if (aristaHdrBinary.empty()) {
        return false;
      }

      if (!parseAristaImgHdr(aristaHdrBinary)) {
        return false;
      }

      updateAristaPsu(psuFd, file);
    } else {
      std::cout << "PSU Model does not match with model of file" << std::endl;
    }
  } else {
    std::cout << "Unrecognized vendor" << std::endl;
    return false;
  }

  return true;
}

} // namespace update
