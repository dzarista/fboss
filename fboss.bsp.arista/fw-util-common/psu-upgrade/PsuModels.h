// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef UPGRADE_PSUMODELS_H
#define UPGRADE_PSUMODELS_H

#include <cstdint>
#include <string>
#include <vector>

namespace update {

enum class Operation { Read, Write };

enum class Section { Header, Primary, Secondary };

class Generic {
public:
  Generic(std::string MFR_MODEL_NAME, uint8_t BOOT_FLAG,
          uint8_t MFR_MODEL_REG_ADDR, uint8_t MFR_MODEL_LEN,
          uint8_t WRITE_PROTECT_ON_VAL, uint16_t BOOT_FLAG_DELAY,
          uint8_t UNLOCK_UPGRADE_REG, uint16_t UNLOCK_DELAY, uint8_t RAM_REG,
          uint8_t RESERVED_LINE_0, uint8_t RESERVED_LINE_1)
      : MFR_MODEL_NAME(MFR_MODEL_NAME), NORMAL_MODE(0x00), BOOT_MODE(0x01),
        BOOT_FLAG(BOOT_FLAG), MFR_MODEL_REG_ADDR(MFR_MODEL_REG_ADDR),
        MFR_MODEL_LEN(MFR_MODEL_LEN), WRITE_PROTECT_REG(0x10),
        WRITE_PROTECT_ON_VAL(WRITE_PROTECT_ON_VAL), WRITE_PROTECT_OFF_VAL(0x00),
        BOOT_FLAG_DELAY(BOOT_FLAG_DELAY),
        UNLOCK_UPGRADE_REG(UNLOCK_UPGRADE_REG), UNLOCK_DELAY(UNLOCK_DELAY),
        RAM_REG(RAM_REG), RESERVED_LINE_0(RESERVED_LINE_0),
        RESERVED_LINE_1(RESERVED_LINE_1) {}
  bool prepUpdatePsu(int, std::string, std::string);
  int bootFlagRdwr(uint8_t, Operation);
  void psuSetWp(uint8_t);
  virtual void unlockUpgrade() = 0;
  virtual bool parseImageHeader(std::vector<uint8_t>) = 0;
  virtual bool updatePsu(std::string) = 0;

  int psuNum;
  int psuFd;
  const std::string MFR_MODEL_NAME;
  const uint8_t NORMAL_MODE;
  const uint8_t BOOT_MODE;
  const uint8_t BOOT_FLAG;
  const uint8_t MFR_MODEL_REG_ADDR;
  const uint8_t MFR_MODEL_LEN;
  const uint8_t WRITE_PROTECT_REG;
  const uint8_t WRITE_PROTECT_ON_VAL;
  const uint8_t WRITE_PROTECT_OFF_VAL;
  const uint16_t BOOT_FLAG_DELAY;
  const uint8_t UNLOCK_UPGRADE_REG;
  const uint16_t UNLOCK_DELAY;
  const uint8_t RAM_REG;
  const uint8_t RESERVED_LINE_0;
  const uint8_t RESERVED_LINE_1;
};

class ECD15020056 : public Generic {
public:
  ECD15020056()
      : Generic("ECD15020056", 0xF1, 0x9A, 11, 0x40, 3000, 0xF0, 5, 0xF2, 2,
                12),
        HEADER_LEN(64), HEADER_DELAY(25), PRIMARY_DELAY(25), SECONDARY_DELAY(5),
        POST_HEADER_DELAY(5000), FLASH_DELAY(1000), FLASH_REG(0xF3),
        CRC_CHECK(0xF4), PSU_BOOT_UNLOCKED_BOOTLOADER_MASK(0xC) {}
  void unlockUpgrade() override;
  bool parseImageHeader(std::vector<uint8_t>) override;
  bool updatePsu(std::string) override;
  bool firmwareTransmit(const std::string &);
  bool firmwareTransmitSection(int, int, const std::vector<uint8_t> &, int,
                               Section);
  bool firmwareTransmitLine(int, const std::vector<uint8_t> &, int, Section);
  bool crcCheck(Section);

  const uint8_t HEADER_LEN;
  const uint8_t HEADER_DELAY;
  const uint8_t PRIMARY_DELAY;
  const uint8_t SECONDARY_DELAY;
  const uint16_t POST_HEADER_DELAY;
  const uint16_t FLASH_DELAY;
  const uint8_t FLASH_REG;
  const uint8_t CRC_CHECK;
  const uint8_t PSU_BOOT_UNLOCKED_BOOTLOADER_MASK;
  struct HEADER_FIELDS {
    uint8_t compatibility;
    uint16_t sec_data_start;
    uint8_t pri_fw_major;
    uint8_t pri_fw_minor;
    uint8_t pri_crc[2];
    uint8_t sec_fw_major;
    uint8_t sec_fw_minor;
    uint8_t sec_crc[2];
    uint8_t fw_id[12];
  };
  HEADER_FIELDS HEADER;
};

class ECD25010017 : public Generic {
public:
  ECD25010017()
      : Generic("ECD25010017", 0xD6, 0XCA, 11, 0x80, 1000, 0xD5, 1000, 0xD7, 4,
                12),
        UPGRADE_STATUS(0xD8), RESERVED_LINE_2(12), LINE_DELAY(100),
        ENDING_DELAY(2000){};
  void unlockUpgrade() override;
  bool parseImageHeader(std::vector<uint8_t>) override;
  bool updatePsu(std::string) override;

  const uint8_t UPGRADE_STATUS;
  const uint8_t RESERVED_LINE_2;
  const uint8_t LINE_DELAY;
  const uint16_t ENDING_DELAY;
  struct HEADER_FIELDS {
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
  HEADER_FIELDS HEADER;
};

} // namespace update
#endif // UPGRADE_PSUMODELS_H
