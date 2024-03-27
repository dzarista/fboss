// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "DarwinShowtech.h"
#include "MeruShowtech.h"
#include "Showtech.h"
#include <algorithm>
#include <cstring>
#include <memory>
#include <iostream>
#include <fstream>
#include "json.hpp"

using json = nlohmann::json;

using namespace showtech;

std::string get_platform_from_fruid() {
  std::ifstream fruid_file("/var/facebook/fboss/fruid.json");
  json fruid = json::parse(fruid_file);
  return fruid["Information"]["Product Name"];
}

std::unique_ptr<Showtech> get_platform_showtech(bool verbose) {
  std::string platform = get_platform_from_fruid();
  std::transform(platform.begin(), platform.end(), platform.begin(), ::tolower);
  if (platform == "darwin") {
    return std::make_unique<DarwinShowtech>(verbose);
  } else if (platform == "meru800bia" || platform == "meru800bfa") {
    return std::make_unique<MeruShowtech>(verbose);
  } else {
    std::cout << "Failed to discover platform from fruid.json\n";
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
