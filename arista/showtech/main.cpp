// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "DarwinShowtech.h"
#include "MeruShowtech.h"
#include "Showtech.h"
#include "ShowtechUtils.h"
#include <algorithm>
#include <cstring>
#include <memory>
#include <iostream>
#include <fstream>

using namespace showtech;

std::unique_ptr<Showtech> get_platform_showtech(bool verbose) {
  std::string platform;
  if (run_cmd("dmidecode -s system-product-name", platform) == 0) {
    strip(platform);
    std::transform(platform.begin(), platform.end(), platform.begin(), ::tolower);
    if (platform == "darwin") {
      return std::make_unique<DarwinShowtech>(verbose);
    } else if (platform == "meru800bia" || platform == "meru800bfa") {
      return std::make_unique<MeruShowtech>(verbose);
    } else {
      std::cout << "Unsupported platform: " << platform << "\n";
      std::exit(1);
    }
  } else {
    std::cout << "Failed to discover platform from dmidecode\n";
    std::exit(1);
  }
}

int main(int argc, const char *argv[]) {
  bool verbose = true;
  std::unique_ptr<Showtech> platformShowtech;

  if (argc > 1) {
    if (!strcmp(argv[1], "-q")) {
      verbose = false;
    }
  }

  platformShowtech = get_platform_showtech(verbose);
  platformShowtech->printShowtech();

  return 0;
}
