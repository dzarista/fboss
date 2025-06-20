// Copyright (c) 2023 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "MeruShowtech.h"
#include "CfmShowtech.h"
#include "PsuShowtech.h"
#include "ShowtechUtils.h"
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <memory>
#include <regex>
#include <set>
#include <sstream>
#include <string>
#include <unistd.h>

namespace showtech {

Meru800BiaShowtech::Meru800BiaShowtech(bool verbose) : MeruShowtech(verbose) {
  cpuCpld = std::make_unique<PciScdDevice>("0000:07:00.0",
                                           "fpgas/MERU_SCM_CPLD_INFO_ROM");
  switchcardScds.push_back(std::make_unique<PciScdDevice>(
      "0000:01:00.0", "MERU800BIA_SMB_FPGA_INFO_ROM"));
  switchcardCpld =
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 0, "23", "scd-vcpld");
  powerCtrlers.emplace_back(std::make_unique<I2cDevice>(switchcardScds[0]->addr,
                                                        0, 0, "45", "isl68137"),
                            1);
  powerCtrlers.emplace_back(std::make_unique<I2cDevice>(switchcardScds[0]->addr,
                                                        0, 0, "54", "isl68137"),
                            3);
  powerCtrlers.emplace_back(std::make_unique<I2cDevice>(switchcardScds[0]->addr,
                                                        0, 0, "55", "isl68137"),
                            1);
  fanCplds.emplace_back(std::make_unique<I2cHwmonDevice>(cpuCpld->addr, 1, 3,
                                                         "60", "dsf-fan-cpld"));
}

Meru800BfaShowtech::Meru800BfaShowtech(bool verbose) : MeruShowtech(verbose) {
  cpuCpld = std::make_unique<PciScdDevice>("0000:07:00.0",
                                           "fpgas/MERU_SCM_CPLD_INFO_ROM");
  switchcardScds.emplace_back(std::make_unique<PciScdDevice>(
      "0000:02:00.0", "MERU800BIA_SMB_FPGA0_INFO_ROM"));
  switchcardScds.emplace_back(std::make_unique<PciScdDevice>(
      "0000:01:00.0", "MERU800BIA_SMB_FPGA1_INFO_ROM"));
  switchcardScds.emplace_back(std::make_unique<PciScdDevice>(
      "0000:03:00.0", "MERU800BIA_SMB_FPGA2_INFO_ROM"));
  switchcardScds.emplace_back(std::make_unique<PciScdDevice>(
      "0000:04:00.0", "MERU800BIA_SMB_FPGA3_INFO_ROM"));
  switchcardCpld =
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 0, "23", "decker-cpld");
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "50", "bp4a_isl68137"),
      3);
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "51", "bp4a_isl68137"),
      3);
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "52", "bp4a_isl68137"),
      3);
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "53", "bp4a_isl68137"),
      3);
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "5a", "isl68137"), 1);
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "5b", "isl68137"), 1);
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "5c", "isl68137"), 1);
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "5d", "isl68137"), 1);
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "60", "isl68137"), 1);
  powerCtrlers.emplace_back(
      std::make_unique<I2cDevice>(cpuCpld->addr, 1, 1, "61", "isl68137"), 1);
  fanCplds.emplace_back(std::make_unique<I2cHwmonDevice>(cpuCpld->addr, 1, 3,
                                                         "60", "dsf-fan-cpld"));
  fanCplds.emplace_back(std::make_unique<I2cHwmonDevice>(cpuCpld->addr, 1, 3,
                                                         "61", "dsf-fan-cpld"));
  fanCplds.emplace_back(std::make_unique<I2cHwmonDevice>(cpuCpld->addr, 1, 3,
                                                         "62", "dsf-fan-cpld"));
}

std::set<int> Meru800BfaShowtech::i2cBusIgnore() {
  std::set<int> busesToCheck = {
      1,
      getI2cBusForScd(cpuCpld->addr, 0, 0),
      getI2cBusForScd(cpuCpld->addr, 0, 2),
      getI2cBusForScd(cpuCpld->addr, 0, 3),
      getI2cBusForScd(cpuCpld->addr, 0, 4),
      getI2cBusForScd(cpuCpld->addr, 1, 0),
      getI2cBusForScd(cpuCpld->addr, 1, 1),
      getI2cBusForScd(cpuCpld->addr, 1, 2),
      getI2cBusForScd(cpuCpld->addr, 1, 3),
      getI2cBusForScd(switchcardScds[0]->addr, 4, 0),
      getI2cBusForScd(switchcardScds[0]->addr, 4, 1),
      getI2cBusForScd(switchcardScds[1]->addr, 4, 0),
      getI2cBusForScd(switchcardScds[1]->addr, 4, 1),
      getI2cBusForScd(switchcardScds[2]->addr, 4, 0),
      getI2cBusForScd(switchcardScds[2]->addr, 4, 1),
      getI2cBusForScd(switchcardScds[2]->addr, 4, 3),
      getI2cBusForScd(switchcardScds[3]->addr, 4, 0),
      getI2cBusForScd(switchcardScds[3]->addr, 4, 1),
  };

  std::set<int> busesToIgnore;
  int maxI2cBus = get_max_i2c_bus();
  for (int i = 0; i <= maxI2cBus; i++) {
    if (busesToCheck.find(i) == busesToCheck.end()) {
      busesToIgnore.insert(i);
    }
  }

  return busesToIgnore;
}

Glath05a_64oShowtech::Glath05a_64oShowtech(bool verbose)
    : MeruShowtech(verbose) {
  cpuCpld = std::make_unique<PciScdDevice>("0000:07:00.0",
                                           "fpgas/MERU_SCM_CPLD_INFO_ROM");
  switchcardScds.emplace_back(
      std::make_unique<PciScdDevice>("0000:01:00.0", "GLATH05A_64O_INFO_ROM"));
  switchcardCpld = std::make_unique<I2cDevice>(cpuCpld->addr, 1, 0, "23",
                                               "glath05a-64o-cpld");
  powerCtrlers.emplace_back(std::make_unique<I2cDevice>(switchcardScds[0]->addr,
                                                        1, 0, "45", "isl68137"),
                            1);
  powerCtrlers.emplace_back(std::make_unique<I2cDevice>(switchcardScds[0]->addr,
                                                        1, 1, "46", "isl68137"),
                            2);
  powerCtrlers.emplace_back(std::make_unique<I2cDevice>(switchcardScds[0]->addr,
                                                        1, 2, "47", "isl68137"),
                            2);
  powerCtrlers.emplace_back(std::make_unique<I2cDevice>(switchcardScds[0]->addr,
                                                        1, 3, "4d", "isl68137"),
                            1);
  powerCtrlers.emplace_back(std::make_unique<I2cDevice>(switchcardScds[0]->addr,
                                                        1, 4, "4c", "isl68137"),
                            1);
  fanCplds.emplace_back(std::make_unique<I2cHwmonDevice>(
      cpuCpld->addr, 1, 3, "60", "glath05a-64o-fan-cpld"));
}

void MeruShowtech::printWeutilInfo() {
  std::cout << "#########################\n";
  std::cout << "##### WEUTIL INFO #####\n";
  std::cout << "#########################\n\n";

  printWeutil("SCM");
  printWeutil("SMB");
}

void MeruShowtech::printAllFpgaVersions() {
  std::string major_rev_path, minor_rev_path, combined_path;
  std::set<std::filesystem::path> fpga_sorted_by_name, cpld_sorted_by_name;
  std::string fpga_path = "/run/devmap/fpgas/";
  std::string cpld_path = "/run/devmap/cplds/";

  std::cout << "#########################\n";
  std::cout << "##### FPGA VERSIONS #####\n";
  std::cout << "#########################\n\n";

  if (std::filesystem::exists(fpga_path)) {
    for (const auto &fpga : std::filesystem::directory_iterator(fpga_path)) {
      if (fpga.is_directory() &&
          fpga.path().filename().string().find("INFO_ROM") != std::string::npos)
        fpga_sorted_by_name.insert(fpga.path());
    }
  } else {
    std::cout << fpga_path << " does not exist" << std::endl;
  }
  for (const auto &path : fpga_sorted_by_name) {
    combined_path = "/fw_ver";
    printFpgaVersion(path.filename().string(), path.string(), combined_path);
  }

  if (std::filesystem::exists(cpld_path)) {
    for (const auto &cpld : std::filesystem::directory_iterator(cpld_path)) {
      cpld_sorted_by_name.insert(cpld.path());
    }
  } else {
    std::cout << cpld_path << " does not exist" << std::endl;
  }
  for (const auto &path : cpld_sorted_by_name) {
    if (path.string().find("FAN") != std::string::npos) {
      // Fan CPLDs are a special case because the version files are in hwmon.
      major_rev_path = "/hwmon/hwmon*/cpld_ver";
      minor_rev_path = "/hwmon/hwmon*/cpld_sub_ver";
    } else {
      major_rev_path = "/cpld_ver";
      minor_rev_path = "/cpld_sub_ver";
    }
    printFpgaVersion(path.filename().string(), path.string(), major_rev_path,
                     minor_rev_path);
  }

  std::cout << std::endl;
}

void MeruShowtech::printFanInfo() {
  int i, pwm_pcnt, num_cpld = 0;
  std::set<std::filesystem::path> path_sorted_by_name;
  std::string per_cpld_fan_num, global_fan_num, present, pwm, rpm;
  std::string sensor_path = "/run/devmap/sensors/";

  std::cout << "##########################\n";
  std::cout << "##### FAN DEBUG INFO #####\n";
  std::cout << "##########################\n\n";

  if (std::filesystem::exists(sensor_path)) {
    // This is dependent on the numbering of the FAN_CPLDs in the filenames.
    for (const auto &sensor :
         std::filesystem::directory_iterator(sensor_path)) {
      path_sorted_by_name.insert(sensor.path());
    }
  } else {
    std::cout << sensor_path << " does not exist" << std::endl;
  }

  for (auto &path : path_sorted_by_name) {
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
          pwm = run_cmd_no_check("head -n 1 " + path.string() + "/pwm" +
                                 per_cpld_fan_num);
          strip(pwm);
          rpm = run_cmd_no_check("head -n 1 " + path.string() + "/fan" +
                                 per_cpld_fan_num + "_input");
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
  std::cout << "##########################\n";
  std::cout << "##### I2C DEBUG INFO #####\n";
  std::cout << "##########################\n\n";

  std::cout << "#### SWITCHCARD CPLD I2C DUMP ####" << std::endl;
  std::cout << switchcardCpld->i2cDump() << std::endl;

  std::cout << "#### POWER CONTROLLER I2C DUMPS ####" << std::endl;
  for (const auto &pwrCtrler : powerCtrlers) {
    /* Force writes on claimed device potentially dangerous - disable for now

   for ( int page = 0; page < pwrCtrler.second; page++ ) {
     std::cout << "PAGE " << std::to_string(page) << std::endl;
     run_cmd_with_timeout("i2cset -f -y " + (pwrCtrler.first)->i2cBus + " 0x" +
                              (pwrCtrler.first)->addr + " 0x0 " +
                              std::to_string(page),
                          5);
    */
    std::cout << (pwrCtrler.first)->i2cDump() << std::endl;
  }

  std::cout << "#### FAN I2C DUMPS ####" << std::endl;
  for (const auto &fanCpld : fanCplds) {
    std::cout << fanCpld->i2cDump() << std::endl;
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
  printWeutilInfo();
  printAllFpgaVersions();
  printFanInfo();
  printPsuShowtechInfo();
  if (!ramdisk_) {
    printCfmShowtechInfo();
  }
  if (verbose_) {
    printI2cInfo();
  }
}

} // namespace showtech
