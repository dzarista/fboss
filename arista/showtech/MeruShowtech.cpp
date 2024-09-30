// Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "MeruShowtech.h"
#include "PsuShowtech.h"
#include "CfmShowtech.h"
#include <filesystem>
#include <iostream>
#include <memory>
#include <regex>
#include <set>
#include <sstream>
#include <string>
#include <unistd.h>

namespace showtech {

void MeruShowtech::printFpgaVersion(std::string name,
                                    std::string major_rev_path,
                                    std::string minor_rev_path) {
  std::string major_rev;
  std::string minor_rev;

  if (run_cmd("head -n 1 " + major_rev_path, major_rev) == 0 &&
      run_cmd("head -n 1 " + minor_rev_path, minor_rev) == 0 &&
      major_rev != "" && minor_rev != "") {
    strip(major_rev);
    strip(minor_rev);
    std::cout << name << ": "
              << std::stoul(major_rev, nullptr, 16) << "."
              << std::stoul(minor_rev, nullptr, 16) << std::endl;
  } else {
    std::cout << name << ": VERSION_NOT_DETECTED" << std::endl;
  }
}

void MeruShowtech::printAllFpgaVersions() {
  std::string major_rev_path, minor_rev_path;
  std::set<std::filesystem::path> fpga_sorted_by_name, cpld_sorted_by_name;
  std::string fpga_path = "/run/devmap/fpgas/";
  std::string cpld_path = "/run/devmap/cplds/";

  std::cout << "##### FPGA VERSIONS #####\n";

  for (const auto & fpga : std::filesystem::directory_iterator(fpga_path)) {
    fpga_sorted_by_name.insert(fpga.path());
  }
  for (const auto & path : fpga_sorted_by_name) {
    major_rev_path = path.string() + "/fpga_ver";
    minor_rev_path = path.string() + "/fpga_sub_ver";
    printFpgaVersion(path.filename().string(), major_rev_path, minor_rev_path);
  }

  for (const auto & cpld : std::filesystem::directory_iterator(cpld_path)) {
    cpld_sorted_by_name.insert(cpld.path());
  }
  for (const auto & path : cpld_sorted_by_name) {
    if (path.string().find("FAN") != std::string::npos) {
      // Fan CPLDs are a special case because the version files are in hwmon.
      major_rev_path = path.string() + "/hwmon/hwmon*/cpld_ver";
      minor_rev_path = path.string() + "/hwmon/hwmon*/cpld_sub_ver";
    } else {
      major_rev_path = path.string() + "/cpld_ver";
      minor_rev_path = path.string() + "/cpld_sub_ver";
    }
    printFpgaVersion(path.filename().string(), major_rev_path, minor_rev_path);
  }

  std::cout << std::endl;
}

void MeruShowtech::printFanInfo() {
  int i, pwm_pcnt, num_cpld = 0;
  std::set<std::filesystem::path> path_sorted_by_name;
  std::string per_cpld_fan_num, global_fan_num, present, pwm, rpm;
  std::string sensor_path = "/run/devmap/sensors/";

  std::cout << "##### FANS #####\n";

  // This is dependent on the numbering of the FAN_CPLDs in the filenames.
  for (const auto & sensor : std::filesystem::directory_iterator(sensor_path)) {
    path_sorted_by_name.insert(sensor.path());
  }

  for (auto & path : path_sorted_by_name) {
    if (path.string().find("FAN_CPLD") != std::string::npos) {
      for (i = 1; i <= numFansPerCpld; ++i) {
        per_cpld_fan_num = std::to_string(i);
        global_fan_num = std::to_string(i + (num_cpld * numFansPerCpld));
        std::cout << "FAN " << global_fan_num << ": ";
        present = run_cmd_no_check("head  -n 1 " + path.string() + "/fan" +
                                   per_cpld_fan_num + "_present");
        strip(present);
        std::cout << "Present: " + present;

        if (present == "1") {
          pwm = run_cmd_no_check("head -n 1 " + path.string() +
                                 "/pwm" + per_cpld_fan_num);
          strip(pwm);
          rpm = run_cmd_no_check("head -n 1 " + path.string() +
                                 "/fan" + per_cpld_fan_num + "_input");
          strip(rpm);
          if (pwm != "" && rpm != "") {
            pwm_pcnt = 100 * std::stoi(pwm) / 255;
            strip(rpm);
            std::cout << ", RPM: " << rpm << " (" << pwm_pcnt << "%)\n";
          } else {
            std::cout << ", RPM: " << " SPEED UNKNOWN\n";
          }
        } else {
          std::cout << "\n";
        }
      }
      num_cpld++;
    }
  }
  std::cout << std::endl;
}

void MeruShowtech::printI2cInfo() {
  std::string i2c_dev_str;
  std::filesystem::path symlink;
  std::smatch i2c_dev_match;
  std::regex i2c_dev_regex("(\\d+)-([0-9a-f]+)");
  int i2c_bus, i2c_addr;

  std::cout << "##########################\n";
  std::cout << "##### I2C DEBUG INFO #####\n";
  std::cout << "##########################\n\n";

  std::string cpldPath = "/run/devmap/cplds/";
  for (const auto & entry : std::filesystem::directory_iterator(cpldPath)) {
    if (std::filesystem::is_symlink(entry.path())) {
      symlink = std::filesystem::read_symlink(entry.path());
      i2c_dev_str = symlink.filename().string();
      if (regex_search(i2c_dev_str.cbegin(), i2c_dev_str.cend(), i2c_dev_match,
                       i2c_dev_regex)) {
        if (i2c_dev_match.size() == 3) {
          i2c_bus = std::stoi(i2c_dev_match[1]);
          i2c_addr = std::stoi(i2c_dev_match[2], 0, 16);
          std::cout << "##### " << entry.path().filename().string()
                    << " I2CDUMP #####\n" << i2c_dump(i2c_bus, i2c_addr)
                    << std::endl;
        }
      }
    }
  }
}

void MeruShowtech::printPsuShowtechInfo() {
  std::cout << "##########################\n";
  std::cout << "##### PSU DEBUG INFO #####\n";
  std::cout << "##########################\n\n";
  printPsuInfo();
}

void MeruShowtech::printCfmShowtechInfo() {
   std::cout << "####################\n";
   std::cout << "##### CFM INFO #####\n";
   std::cout << "####################\n\n";
   printCfmInfo();
}

void MeruShowtech::printPlatformInfo() {
  printWeutil("SCM");
  printWeutil("SMB");
  printAllFpgaVersions();
  printFanInfo();
  printPsuShowtechInfo();
  printCfmShowtechInfo();
  if (verbose_) {
    printI2cInfo();
  }
}

} // namespace showtech
