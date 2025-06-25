// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "Showtech.h"
#include "ShowtechUtils.h"
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace showtech {

void Showtech::printVersion() {
  std::cout << "################################\n";
  std::cout << "##### SHOWTECH VERSION " << version << " #####\n";
  std::cout << "################################\n\n";
}

void Showtech::printCpuDetails() {
  std::cout << "##### CPU SYSTEM TIME #####\n" << run_cmd_no_check("date");
  std::cout << "\n##### CPU HOSTNAME #####\n" << run_cmd_no_check("hostname");
  std::cout << "\n##### CPU Linux Kernel Version #####\n"
            << run_cmd_no_check("uname -r");
  std::cout << "\n##### CPU UPTIME #####\n"
            << run_cmd_no_check("uptime") << std::endl;
}

void Showtech::printFbossDetails() {
  print_fboss2_show_cmd("product");
  print_fboss2_show_cmd("version agent");
  print_fboss2_show_cmd("environment sensor");
  print_fboss2_show_cmd("environment temperature");
  print_fboss2_show_cmd("environment fan");
  print_fboss2_show_cmd("environment power");
}

void Showtech::printWeutil(std::string target) {
  std::string cmd = "weutil --eeprom " + target;
  std::filesystem::path ossConfigPath{
      "/opt/fboss/share/platform_configs/weutil.json"};

  if (std::filesystem::exists(ossConfigPath)) {
    // OSS doesn't support running weutil without the -config_file arg.
    cmd = cmd + " -config_file " + ossConfigPath.string();
  }
  std::cout << "##### " + target + " SERIAL NUMBER #####\n";
  std::cout << run_cmd_no_check(cmd) << std::endl;
}

void Showtech::printFpgaVersion(std::string name, std::string sysfsPath,
                                std::string combinedRevPath) {
  std::string combinedRev;
  if (run_cmd("head -n 1 " + sysfsPath + combinedRevPath, combinedRev) == 0) {
    strip(combinedRev);
    std::cout << name << ": " << combinedRev << std::endl;
  } else {
    std::cout << name << ": VERSION_NOT_DETECTED" << std::endl;
  }
}

void Showtech::printFpgaVersion(std::string name, std::string sysfsPath,
                                std::string majorRevPath,
                                std::string minorRevPath) {
  std::string majorRev;
  std::string minorRev;
  if (run_cmd("head -n 1 " + sysfsPath + majorRevPath, majorRev) == 0 &&
      run_cmd("head -n 1 " + sysfsPath + minorRevPath, minorRev) == 0) {
    strip(majorRev);
    strip(minorRev);
    std::cout << name << ": " << std::stoul(majorRev, nullptr, 16) << "."
              << std::stoul(minorRev, nullptr, 16) << std::endl;
  } else {
    std::cout << name << ": VERSION_NOT_DETECTED" << std::endl;
  }
}

void Showtech::printLspci() {
  std::string cmd;

  std::cout << "################################\n";
  std::cout << "############# LSPCI ############\n";
  std::cout << "################################\n\n";

  cmd = "lspci";
  if (verbose_) {
    cmd = cmd + " -vvv";
  }
  std::cout << cmd << std::endl << run_cmd_no_check(cmd) << std::endl;
}

void Showtech::printI2cDetect() {
  std::string cmd;
  std::set<int> bus_to_ignore = i2cBusIgnore();
  int bus;

  std::cout << "################################\n";
  std::cout << "########## I2C DETECT ##########\n";
  std::cout << "################################\n\n";

  cmd = "i2cdetect -l";
  std::cout << cmd << std::endl << run_cmd_no_check(cmd) << std::endl;

  for (bus = 0; bus <= get_max_i2c_bus(); ++bus) {
    if (bus_to_ignore.find(bus) == bus_to_ignore.end()) {
      cmd = "i2cdetect -y " + std::to_string(bus);
      std::cout << cmd << std::endl
                << run_cmd_with_timeout(cmd, 30) << std::endl;
    }
  }
}

void Showtech::printLogs() {

  const std::string alt_platform_manager_log_path =
      "/var/facebook/logs/fboss/platform_manager.log";
  const std::string alt_sensor_service_log_path =
      "/var/facebook/logs/fboss/sensor_service.log";
  const std::string alt_data_corral_log_path =
      "/var/facebook/logs/fboss/data_corral_service.log";
  const std::string alt_fan_service_log_path =
      "/var/facebook/logs/fboss/fan_service.log";
  std::cout << "################################\n";
  std::cout << "########## DEBUG LOGS ##########\n";
  std::cout << "################################\n\n";

  std::cout << "#### PLATFORM MANAGER LOG ####\n";
  if (std::filesystem::exists(alt_platform_manager_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_platform_manager_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u platform_manager")
              << std::endl;
  }

  std::cout << "#### SENSOR SERVICE LOG ####\n";
  if (std::filesystem::exists(alt_sensor_service_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_sensor_service_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u sensor_service")
              << std::endl;
  }

  std::cout << "#### FAN SERVICE LOG ####\n";
  if (std::filesystem::exists(alt_fan_service_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_fan_service_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u fan_service") << std::endl;
  }

  std::cout << "#### DATA CORRAL LOG ####\n";
  if (std::filesystem::exists(alt_data_corral_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_data_corral_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u data_corral_service")
              << std::endl;
  }

  std::cout << "#### QSFP LOG ####\n";
  std::cout << run_cmd_with_limit("journalctl -u qsfp_service") << std::endl;

  std::cout << "#### SW AGENT LOG ####\n";
  std::cout << run_cmd_with_limit("journalctl -u fboss_sw_agent") << std::endl;

  std::cout << "#### HW AGENT LOG ####\n";
  std::cout << run_cmd_with_limit("journalctl -u fboss_hw_agent@0")
            << std::endl;

  std::cout << "#### DMESG LOG ####\n";
  std::cout << run_cmd_with_limit("dmesg") << std::endl;

  std::cout << "#### BOOT CONSOLE LOG ####\n";
  std::cout << run_cmd_with_limit("cat /var/log/boot.log") << std::endl;

  std::cout << "#### LINUX MESSAGES LOG ####\n";
  std::cout << run_cmd_with_limit("cat /var/log/messages") << std::endl;

  std::cout << "#### NVME SSD SMART LOG ####\n";
  std::cout << run_cmd_no_check("nvme smart-log /dev/nvme0n1") << std::endl;

  std::cout << "#### NVME SSD ERROR LOG ####\n";
  std::cout << run_cmd_no_check("nvme error-log /dev/nvme0n1") << std::endl;

  std::cout << "#### NVME SSD ID CTRL LOG ####\n";
  std::cout << run_cmd_no_check("nvme id-ctrl /dev/nvme0n1") << std::endl;
}

void Showtech::printL1Info() {
  std::cout << "################################\n";
  std::cout << "########### L1 LOGS ############\n";
  std::cout << "################################\n\n";

  print_fboss2_show_cmd("port");
  print_fboss2_show_cmd("fabric");
  print_fboss2_show_cmd("lldp");
  print_fboss2_show_cmd("interface counters");
  print_fboss2_show_cmd("interface errors");
  print_fboss2_show_cmd("interface flaps");
  print_fboss2_show_cmd("interface phy");
  print_fboss2_show_cmd("transceiver");

  if (verbose_ && !ramdisk_) {
    std::cout << "#### wedge_qsfp_util ####\n";
    std::cout << run_cmd_with_timeout("wedge_qsfp_util", 30) << std::endl;
  }
}

void Showtech::printSensors() {
  std::cout << "################################\n";
  std::cout << "######### SENSORS DUMP #########\n";
  std::cout << "################################\n\n";
  std::cout << run_cmd_with_timeout("sensors", 30) << std::endl;
}
void Showtech::printShowtech() {
  printVersion();
  printCpuDetails();
  printFbossDetails();
  printPlatformInfo();
  printLspci();
  printL1Info();
  printSensors();
  if (verbose_) {
    printI2cDetect();
    printLogs();
  }
}

} // namespace showtech
