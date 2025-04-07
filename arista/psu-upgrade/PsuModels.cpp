// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.
#include "PsuModels.h"
#include "DeviceHandler.h"
#include "smbus.h"
#include <chrono>
#include <cstring>
#include <iostream>
#include <linux/i2c-dev.h>
#include <sys/ioctl.h>
#include <thread>

namespace update {

int Generic::bootFlagRdwr(uint8_t mode, Operation op) {
  if (op == Operation::Write) {
    if (mode == BOOT_MODE) {
      std::cout << "-- Bootloader Mode --" << std::endl;
    } else {
      std::cout << "-- Reset PSU --" << std::endl;
    }
    return writeByte(psuFd, BOOT_FLAG, mode);
  } else {
    return readByte(psuFd, BOOT_FLAG);
  }
  return -1;
}

void Generic::psuSetWp(uint8_t mode) {
  if (mode == WRITE_PROTECT_OFF_VAL) {
    std::cout << "-- Write Protect Disabled --" << std::endl;
  } else {
    std::cout << "-- Write Protect Enabled --" << std::endl;
  }
  writeByte(psuFd, WRITE_PROTECT_REG, mode);
}

void ECD15020056::unlockUpgrade() {
  std::vector<uint8_t> data(MFR_MODEL_LEN + 1);
  data[MFR_MODEL_LEN] = HEADER.compatibility;
  for (int i = 0; i < MFR_MODEL_LEN; i++) {
    data[i] = MFR_MODEL_NAME[i];
  }
  psuSetWp(WRITE_PROTECT_OFF_VAL);
  writeBlock(psuFd, UNLOCK_UPGRADE_REG, data);
}

bool ECD15020056::parseImageHeader(std::vector<uint8_t> header) {
  int index = 0;

  for (int i = 0; i < MFR_MODEL_LEN; i++) {
    HEADER.fw_id[i] = header[index++];
  }

  if (std::memcmp(HEADER.fw_id, MFR_MODEL_NAME.c_str(), MFR_MODEL_LEN) != 0) {
    std::cout << "PSU Model does not match with model of file" << std::endl;
    return false;
  }

  HEADER.compatibility = header[index++];
  HEADER.sec_data_start = header[index++];
  HEADER.sec_data_start |= header[index++] << 8;
  index += RESERVED_LINE_0;
  HEADER.pri_fw_major = header[index++];
  HEADER.pri_fw_minor = header[index++];
  HEADER.pri_crc[0] = header[index++];
  HEADER.pri_crc[1] = header[index++];
  index += RESERVED_LINE_1;
  HEADER.sec_fw_major = header[index++];
  HEADER.sec_fw_minor = header[index++];
  HEADER.sec_crc[0] = header[index++];
  HEADER.sec_crc[1] = header[index];

  std::cout << "Model: " << HEADER.fw_id << std::endl;
  std::cout << "HW Compatibility: "
            << static_cast<unsigned int>(HEADER.compatibility) << std::endl;
  std::cout << "Primary Ver: " << static_cast<unsigned int>(HEADER.pri_fw_major)
            << "." << static_cast<unsigned int>(HEADER.pri_fw_minor)
            << std::endl;
  std::cout << "Secondary Ver: "
            << static_cast<unsigned int>(HEADER.sec_fw_major) << "."
            << static_cast<unsigned int>(HEADER.sec_fw_minor) << std::endl;
  return true;
}

bool ECD15020056::firmwareTransmit(const std::string &filePath) {
  std::vector<uint8_t> data = readBinaryFile(filePath);
  if (data.empty()) {
    return false;
  }

  std::cout << "-- Transmit Header -- " << std::endl;
  if (!firmwareTransmitSection(0, HEADER_LEN / BYTES_PER_LINE, data,
                               HEADER_DELAY, Section::Header)) {
    return false;
  }

  std::cout << "-- Transmit Primary Firmware -- " << std::endl;
  if (!firmwareTransmitSection(HEADER_LEN / BYTES_PER_LINE,
                               HEADER.sec_data_start, data, PRIMARY_DELAY,
                               Section::Primary)) {
    return false;
  }

  std::cout << "-- Transmit Secondary Firmware -- " << std::endl;
  if (!firmwareTransmitSection(HEADER.sec_data_start,
                               data.size() / BYTES_PER_LINE, data,
                               SECONDARY_DELAY, Section::Secondary)) {
    return false;
  }

  return true;
}

bool ECD15020056::firmwareTransmitSection(int startLine, int endLine,
                                          const std::vector<uint8_t> &data,
                                          int delay, Section section) {
  int lineNum;
  int linesUploaded = 0;

  std::cout << std::dec << "Beginning transmit of lines " << startLine << " to "
            << endLine << std::endl;
  for (lineNum = startLine; lineNum < endLine; lineNum++) {

    if (!firmwareTransmitLine(lineNum, data, delay, section)) {
      std::cerr << "Failed to write a line, aborting" << std::endl;
      return false;
    }
    linesUploaded++;
    std::cout << "-- " << std::dec << linesUploaded << " lines uploaded --\r";
  }
  std::cout << std::endl;
  if (startLine < HEADER_LEN / BYTES_PER_LINE) {
    std::this_thread::sleep_for(std::chrono::milliseconds(POST_HEADER_DELAY));
  } else {
    writeNullByte(psuFd, FLASH_REG);
    std::this_thread::sleep_for(std::chrono::milliseconds(FLASH_DELAY));

    if (startLine < HEADER.sec_data_start) {
      return crcCheck(Section::Primary);
    } else {
      return crcCheck(Section::Secondary);
    }
  }
  return true;
}

bool ECD15020056::firmwareTransmitLine(int lineNum,
                                       const std::vector<uint8_t> &data,
                                       int delay, Section section) {
  std::vector<uint8_t> block(BYTES_PER_LINE + 2);
  block[0] = lineNum & 0xFF;
  block[1] = (lineNum >> 8) & 0xFF;
  size_t startWriteFrom = lineNum * BYTES_PER_LINE;
  std::copy(data.begin() + startWriteFrom,
            data.begin() + startWriteFrom + BYTES_PER_LINE, block.begin() + 2);

  writeBlock(psuFd, RAM_REG, block);
  if (lineNum == 3) {
    delay += POST_HEADER_DELAY;
  }
  std::this_thread::sleep_for(std::chrono::milliseconds(delay));
  int bootFlagVal = bootFlagRdwr(BOOT_MODE, Operation::Read);
  if ((bootFlagVal & 0x20)) {
    std::cout << "-- FW transmission error --" << std::endl;
    return false;
  }

  if (section == Section::Secondary) {
    if ((bootFlagVal & 0xF) != 0xD) {
      std::cout << "-- FW transmission error -- " << std::endl;
      return false;
    }
  } else {
    if ((bootFlagVal & 0xF) != 0xC) {
      std::cout << "-- FW transmission error --" << std::endl;
      return false;
    }
  }
  return true;
}

bool ECD15020056::crcCheck(Section section) {
  uint8_t fileCrc[2];
  if (section == Section::Primary) {
    std::copy(HEADER.pri_crc, HEADER.pri_crc + 2, fileCrc);
  } else {
    std::copy(HEADER.sec_crc, HEADER.sec_crc + 2, fileCrc);
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
bool ECD15020056::updatePsu(std::string file) {
  if (ioctl(psuFd, I2C_PEC, 1) < 0) {
    std::cerr << "Could not enable I2C_PEC" << std::endl;
    return false;
  }

  int bootFlagVal = bootFlagRdwr(BOOT_MODE, Operation::Read);

  if (!(bootFlagVal & PSU_BOOT_UNLOCKED_BOOTLOADER_MASK) &&
      !isPsuPowerOk(psuNum)) {
    std::cout << "PSU " << psuNum
              << " power is not ok. Verify that the PSU is conneted to AC "
                 "power supply."
              << std::endl;
    return false;
  }

  unlockUpgrade();
  std::this_thread::sleep_for(std::chrono::milliseconds(UNLOCK_DELAY));
  bootFlagRdwr(BOOT_MODE, Operation::Write);
  std::this_thread::sleep_for(std::chrono::milliseconds(BOOT_FLAG_DELAY));
  if ((bootFlagRdwr(BOOT_MODE, Operation::Read) & 0xF) == 0xD) {
    std::cout << "-- Secondary MCU Selected, Reverting to Primary --"
              << std::endl;
    bootFlagRdwr(NORMAL_MODE, Operation::Write);
    std::this_thread::sleep_for(std::chrono::milliseconds(BOOT_FLAG_DELAY));
    unlockUpgrade();
    std::this_thread::sleep_for(std::chrono::milliseconds(UNLOCK_DELAY));
    bootFlagRdwr(BOOT_MODE, Operation::Write);
    std::this_thread::sleep_for(std::chrono::milliseconds(BOOT_FLAG_DELAY));
  }

  if ((bootFlagRdwr(BOOT_MODE, Operation::Read) & 0xF) != 0xC) {
    std::cout << "-- Set Bootloader Mode Error --" << std::endl;
    return false;
  }

  firmwareTransmit(file);

  bootFlagVal = bootFlagRdwr(NORMAL_MODE, Operation::Write);
  std::this_thread::sleep_for(std::chrono::milliseconds(BOOT_FLAG_DELAY));

  psuSetWp(WRITE_PROTECT_ON_VAL);

  bootFlagVal = bootFlagRdwr(BOOT_MODE, Operation::Read);
  if ((bootFlagVal & 0x7) == 0x4) {
    if (bootFlagVal & 0x80) {
      std::cout << "-- Primary FW Identifier Error --" << std::endl;
      return false;
    } else if (bootFlagVal & 0x40) {
      std::cout << "-- Primary CRC16 Application Checksum Wrong --"
                << std::endl;
      return false;
    }
  } else if ((bootFlagVal & 0x7) == 0x5) {
    if (bootFlagVal & 0x80) {
      std::cout << "-- Secondary FW Identifier Error --" << std::endl;
      return -1;
    } else if (bootFlagVal & 0x40) {
      std::cout << "-- Secondary CRC16 Application Checksum Wrong --"
                << std::endl;
      return false;
    }
  }
  std::cout << "-- Upgrade Done --" << std::endl;
  return true;
}

void ECD25010017::unlockUpgrade() {
  std::vector<uint8_t> data(MFR_MODEL_LEN + 1);
  data[MFR_MODEL_LEN] = HEADER.compatibility;
  for (int i = 0; i < MFR_MODEL_LEN; i++) {
    data[i] = MFR_MODEL_NAME[i];
  }
  psuSetWp(WRITE_PROTECT_OFF_VAL);
  writeBlock(psuFd, UNLOCK_UPGRADE_REG, data);
}

bool ECD25010017::parseImageHeader(std::vector<uint8_t> header) {
  int index = 0;
  for (int i = 0; i < MFR_MODEL_LEN; i++) {
    HEADER.fw_id[i] = header[index++];
  }

  if (std::memcmp(HEADER.fw_id, MFR_MODEL_NAME.c_str(), MFR_MODEL_LEN) != 0) {
    std::cout << "PSU Model does not match with model of file" << std::endl;
    return false;
  }

  HEADER.compatibility = header[index++];
  index += RESERVED_LINE_0;
  HEADER.pri_fw_end_line = header[index++];
  HEADER.pri_fw_end_line |= header[index++] << 8;
  HEADER.pri_crc[0] = header[index++];
  HEADER.pri_crc[1] = header[index++];
  index += RESERVED_LINE_1;
  HEADER.sec_fw_end_line = header[index++];
  HEADER.sec_fw_end_line |= header[index++] << 8;
  HEADER.sec_crc[0] = header[index++];
  HEADER.sec_crc[1] = header[index++];
  index += RESERVED_LINE_2;
  HEADER.pri_reset_flag = (uint16_t)(header[index++] << 8);
  HEADER.pri_reset_flag |= header[index++];
  HEADER.sec_reset_flag = (uint16_t)(header[index++] << 8);
  HEADER.sec_reset_flag |= header[index++];
  HEADER.pri_update_flag = (uint16_t)(header[index++] << 8);
  HEADER.pri_update_flag |= header[index++];
  HEADER.sec_update_flag = (uint16_t)(header[index++] << 8);
  HEADER.sec_update_flag |= header[index++];

  std::cout << "Model: " << HEADER.fw_id << std::endl;
  std::cout << "HW Compatibility: "
            << static_cast<unsigned int>(HEADER.compatibility) << std::endl;
  return true;
}

bool ECD25010017::updatePsu(std::string file) {
  unlockUpgrade();
  std::this_thread::sleep_for(std::chrono::milliseconds(UNLOCK_DELAY));
  bootFlagRdwr(BOOT_MODE, Operation::Write);
  std::this_thread::sleep_for(std::chrono::milliseconds(BOOT_FLAG_DELAY));
  std::vector<uint8_t> data = readBinaryFile(file);

  for (int lineNum = 0; lineNum <= HEADER.sec_fw_end_line / 2; lineNum++) {
    std::vector<uint8_t> block(I2C_SMBUS_BLOCK_MAX);
    size_t startWriteFrom = lineNum * I2C_SMBUS_BLOCK_MAX;
    std::copy(data.begin() + startWriteFrom,
              data.begin() + startWriteFrom + I2C_SMBUS_BLOCK_MAX,
              block.begin());

    writeBlock(psuFd, RAM_REG, block);
    printf(" %d / %u lines written\r", lineNum, HEADER.sec_fw_end_line / 2);
    std::this_thread::sleep_for(std::chrono::milliseconds(LINE_DELAY));
  }
  std::cout << std::endl;
  bootFlagRdwr(NORMAL_MODE, Operation::Write);
  std::this_thread::sleep_for(std::chrono::milliseconds(ENDING_DELAY));
  std::cout << "Upgrade Done" << std::endl;
  return true;
}

} // namespace update
