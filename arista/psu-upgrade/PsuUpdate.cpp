// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "PsuUpdate.h"
#include "DeviceHandler.h"
#include "PsuModels.h"
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
#include <memory>
#include <sys/ioctl.h>
#include <syslog.h>
#include <thread>
#include <unistd.h>
#include <vector>

namespace update {

static int globalFd = -1;

void exitHandler(int signum) {
  std::cout << std::endl << "PSU update abort!" << std::endl;
  syslog(LOG_WARNING, "PSU update abort!");
  close(globalFd);
  std::filesystem::remove("/var/run/psu-upgrade.pid");
  exit(signum);
}

bool prepUpdatePsu(int psuNum, std::string file) {
  std::signal(SIGHUP, exitHandler);
  std::signal(SIGINT, exitHandler);
  std::signal(SIGTERM, exitHandler);
  std::signal(SIGQUIT, exitHandler);
  std::unique_ptr<Generic> PsuModel;

  std::string psuI2cBus = getPsuI2cBus(psuNum);
  globalFd = openI2cBus(psuI2cBus);

  if (globalFd < 0) {
    std::cerr << "Failed to open i2c" << std::endl;
    close(globalFd);
    std::filesystem::remove("/var/run/psu-upgrade.pid");
    return false;
  }

  std::string i2cDevice = "/dev/i2c-" + psuI2cBus;
  std::vector<uint8_t> mfrModel(I2C_SMBUS_BLOCK_MAX);
  bool validPsuModel = false;

  if (readBlock(globalFd, NEW_PSU_MODEL_REG_ADDR, mfrModel)) {
    if (std::string(mfrModel.begin(),
                    mfrModel.begin() + strlen("ECD25010017")) ==
        "ECD25010017") {
      PsuModel = std::make_unique<ECD25010017>();
      validPsuModel = true;
    }
  } else if (readBlock(globalFd, OLD_PSU_MODEL_REG_ADDR, mfrModel)) {
    if (std::string(mfrModel.begin(),
                    mfrModel.begin() + strlen("ECD15020056")) ==
        "ECD15020056") {
      PsuModel = std::make_unique<ECD15020056>();
      validPsuModel = true;
    }
  } else {
    std::cout << "Could not find the PSU Model from register" << std::endl;
    return false;
  }

  if (!validPsuModel) {
    std::cout << "psu-upgrade utility does not currently support this PSU Model"
              << std::endl;
    return false;
  }

  PsuModel->psuNum = psuNum;
  PsuModel->psuFd = globalFd;
  std::vector<uint8_t> headerBinary = readBinaryFile(file);
  if (headerBinary.empty()) {
    return false;
  }

  if (!PsuModel->parseImageHeader(headerBinary)) {
    return false;
  }

  std::cout << "Upgrading PSU Model " << PsuModel->MFR_MODEL_NAME << std::endl;
  PsuModel->updatePsu(file);
  return true;
}

} // namespace update
