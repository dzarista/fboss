// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "PsuUpdate.h"
#include <csignal>
#include <errno.h>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <sys/file.h>
#include <syslog.h>

using namespace update;

void printUsage() {
  int psuCount = getPsuCount();

  std::stringstream ss;
  ss << "Usage: psu-upgrade <";
  for (int i = 1; i <= psuCount; i++) {
    ss << "psu" << i;
    if (i < psuCount) {
      ss << "|";
    }
  }
  ss << "> --update <file_path> --vendor <Delta|Arista>";

  std::cout << ss.str() << std::endl;
}

int main(int argc, const char *argv[]) {
  int psuCount = getPsuCount();
  int psuNum = 0;
  if (argc < 5) {
    printUsage();
    return -1;
  }

  std::string psuArg = argv[1];

  for (int i = 1; i <= psuCount; i++) {
    if (psuArg == "psu" + std::to_string(i)) {
      psuNum = i;
      break;
    }
  }
  if (psuNum == 0) {
    printUsage();
    return -1;
  }

  std::string updateFilePath = "";
  std::string vendorName = "";

  for (int i = 2; i < argc; i++) {
    std::string arg = argv[i];
    if (arg == "--update" && i + 1 < argc) {
      updateFilePath = argv[++i];
    } else if (arg == "--vendor" && i + 1 < argc) {
      vendorName = argv[++i];
    }
  }

  if (updateFilePath.empty() && vendorName.empty()) {
    printUsage();
    return -1;
  }

  int pidFile = open("/var/run/psu-upgrade.pid", O_RDWR | O_CREAT, 0666);
  if (flock(pidFile, LOCK_EX | LOCK_NB) && (errno == EWOULDBLOCK)) {
    std::cout << "Another psu-upgrade instance is running..." << std::endl;
    exit(EXIT_FAILURE);
  }

  if (!isPsuPresent(psuNum)) {
    std::cout << "PSU" << psuNum << " not present" << std::endl;
    return -1;
  }

  int backupPsus = 0;
  for (int i = 1; i <= psuCount; i++) {
    if (i != psuNum && isPsuPowerOk(i)) {
      backupPsus++;
    }
  }

  if (backupPsus == 0) {
    std::cout << "Another PSU must be functional to perform update"
              << std::endl;
    return -1;
  }

  return updatePsu(psuNum, updateFilePath, vendorName);
}
