// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef UPDATE_PSUUTIL_H
#define UPDATE_PSUUTIL_H

#include <filesystem>

namespace update {
#define NULL_VALUE 0
#define NORMAL_MODE 0x00
#define BOOT_MODE 0x01
#define DELTA_BOOT_FLAG 0xF1
#define ARISTA_BOOT_FLAG 0xD6
#define DATA_TO_RAM 0xF2
#define DATA_TO_FLASH 0xF3
#define DELTA_MFR_MODEL_REG_ADDR 0x9A
#define ARISTA_MFR_MODEL_REG_ADDR 0xCA
#define DELTA_MODEL "ECD15020056"
#define ARISTA_MODEL "ECD25010017"
#define DELTA_HDR_LENGTH 64
#define UPDATE_SKIP 10
#define DELTA_ID_LEN 11
#define DELTA_RESERVED_LINE_0 2
#define DELTA_RESERVED_LINE_1 12
#define ARISTA_ID_LEN 11
#define ARISTA_RESERVED_LINE_0 4
#define ARISTA_RESERVED_LINE_1 12
#define DELTA_PSU_BOOT_UNLOCKED_BOOTLOADER_MASK 0xC
#define DELTA_UNLOCK_UPGRADE 0xF0
#define ARISTA_UNLOCK_UPGRADE 0xD5
#define ARISTA_DATA_REG 0xD7
#define ARISTA_UPGRADE_STATUS 0xD8
#define ENABLE_ALL_CMDS 0x00
#define DELTA_OPERATION_PAGE_ONLY 0x40
#define ARISTA_OPERATION_PAGE_ONLY 0x80
#define WRITE_PROTECT 0x10
#define DELTA_UNLOCK_DELAY 5
#define ARISTA_UNLOCK_DELAY 1000
#define HEADER_DELAY 25
#define PRIMARY_DELAY 25
#define SECONDARY_DELAY 5
#define DELTA_BOOT_FLAG_DELAY 3000
#define ARISTA_BOOT_FLAG_DELAY 1000
#define ARISTA_ENDING_DELAY 20000
#define ARISTA_LINE_DELAY 100
#define POST_HEADER_DELAY 5000
#define FLASH_DELAY 1000
#define I2C_SMBUS_BLOCK_MAX = 32
#define BYTES_PER_LINE 16
#define DELTA_NUM_HEADER_LINES 4
#define CRC_CHECK 0xF4

enum class Operation { Read, Write };

enum class Section { Header, Primary, Secondary };

const std::filesystem::path vprPsuInfoIn =
    "/run/devmap/fpgas/MERU800BIA_SMB_FPGA";
const std::filesystem::path wlrPsuInfoIn =
    "/run/devmap/fpgas/MERU800BFA_SMB_FPGA0";

class Delta {};
struct deltaHdrType {
  uint8_t compatibility;
  uint16_t sec_data_start;
  uint8_t pri_fw_major;
  uint8_t pri_fw_minor;
  uint8_t pri_crc[2];
  uint8_t sec_fw_major;
  uint8_t sec_fw_minor;
  uint8_t sec_crc[2];
  uint8_t fw_id[DELTA_ID_LEN + 1];
};

struct aristaHdrType {
  uint8_t compatibility;
  uint16_t pri_fw_end_line;
  uint8_t pri_crc[2];
  uint16_t sec_fw_end_line;
  uint8_t sec_crc[2];
  uint16_t pri_reset_flag;
  uint16_t sec_reset_flag;
  uint16_t pri_update_flag;
  uint16_t sec_update_flag;
  uint8_t fw_id[12];
};

int getPsuCount();
bool isPsuPresent(int psuNum);
bool isPsuPowerOk(int psuNum);
bool updatePsu(int psuNum, std::string file, std::string vendor);
} // namespace update
#endif // UPDATE_PSUUTIL_H
