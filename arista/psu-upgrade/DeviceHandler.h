// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef PSU_UPGRADE_DEVICEHANDLER_H
#define PSU_UPGRADE_DEVICEHANDLER_H

#include <filesystem>
#include <string>
#include <vector>

namespace update {
#define I2C_SMBUS_BLOCK_MAX 32
#define BYTES_PER_LINE 16
#define NEW_PSU_MODEL_REG_ADDR 0xCA
#define OLD_PSU_MODEL_REG_ADDR 0x9A

static const int chipAddr = 0x58;
const std::filesystem::path vprPsuInfoIn =
    "/run/devmap/fpgas/MERU800BIA_SMB_FPGA";
const std::filesystem::path wlrPsuInfoIn =
    "/run/devmap/fpgas/MERU800BFA_SMB_FPGA0";

bool writeNullByte(int, uint8_t);
bool writeByte(int, uint8_t, uint8_t);
bool writeBlock(int, uint8_t, std::vector<uint8_t> &);
int readByte(int, uint8_t);
int readWord(int, uint8_t);
bool readBlock(int, uint8_t, std::vector<uint8_t> &);
std::vector<uint8_t> readBinaryFile(const std::string &);
int getPsuCount();
bool isFileContents1(const std::filesystem::path &);
bool isPsuPresent(int);
bool isPsuPowerOk(int);
std::string getPsuI2cBus(int);
int openI2cBus(std::string);

} // namespace update
#endif // PSU_UPGRADE_DEVICEHANDLER_H
