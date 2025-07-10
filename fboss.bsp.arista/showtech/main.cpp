// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "DarwinShowtech.h"
#include "MeruShowtech.h"
#include "Showtech.h"
#include "ShowtechUtils.h"
#include <algorithm>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>

using namespace showtech;

std::unique_ptr<Showtech> get_platform_showtech() {
  std::string platform;
  if (run_cmd("dmidecode -s system-product-name", platform) == 0) {
    strip(platform);
    std::transform(platform.begin(), platform.end(), platform.begin(),
                   ::tolower);
    if (platform == "darwin" || platform == "darwin48v") {
      return std::make_unique<DarwinShowtech>(platform);
    } else if (platform == "meru800bia" || platform == "meru800biab" ||
               platform == "meru800biac") {
      return std::make_unique<Meru800BiaShowtech>();
    } else if (platform == "meru800bfa") {
      return std::make_unique<Meru800BfaShowtech>();
    } else if (platform == "glath05a-64o") {
      return std::make_unique<Glath05a_64oShowtech>();
    }
  }
  return std::make_unique<GenericShowtech>();
}

int main(int argc, const char *argv[]) {
  std::unique_ptr<Showtech> platformShowtech = get_platform_showtech();
  platformShowtech->printShowtech();

  return 0;
}
