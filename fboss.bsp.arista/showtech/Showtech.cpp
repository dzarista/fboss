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

void Showtech::print_fboss2_show_cmd(std::string cmd) {
  if (!ramdisk_) {
    printSubHeader("fboss2 show " + cmd);
    std::cout << run_cmd_no_check("fboss2 show " + cmd) << std::endl;
  }
}

void Showtech::printWeutil(std::string target) {
  std::string cmd = "weutil --eeprom " + target;
  std::filesystem::path ossConfigPath{
      "/opt/fboss/share/platform_configs/weutil.json"};

  if (std::filesystem::exists(ossConfigPath)) {
    // OSS doesn't support running weutil without the -config_file arg.
    cmd = cmd + " -config_file " + ossConfigPath.string();
  }

  printSubHeader(target + " SERIAL NUMBER");
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

void Showtech::printVersion() {
  printMainHeader("SHOWTECH VERSION " + version);
}

void Showtech::printCpuDetails() {
  printMainHeader("HOST DETAILS");

  printSubHeader("CPU SYSTEM TIME");
  std::cout << run_cmd_no_check("date") << std::endl;

  printSubHeader("CPU HOSTNAME");
  std::cout << run_cmd_no_check("hostname") << std::endl;

  printSubHeader("CPU Linux Kernel Version");
  std::cout << run_cmd_no_check("uname -r") << std::endl;

  printSubHeader("CPU UPTIME");
  std::cout << run_cmd_no_check("uptime") << std::endl;
}

void Showtech::printFbossDetails() {
  printMainHeader("FBOSS DETAILS");

  print_fboss2_show_cmd("product");
  print_fboss2_show_cmd("version agent");
  print_fboss2_show_cmd("environment sensor");
  print_fboss2_show_cmd("environment temperature");
  print_fboss2_show_cmd("environment fan");
  print_fboss2_show_cmd("environment power");
}

void Showtech::printLspci() {
  printMainHeader("LSPCI");

  std::string cmd = "lspci -vvv";
  std::cout << cmd << std::endl;
  std::cout << run_cmd_no_check(cmd) << std::endl;
}

void Showtech::printI2cDetect() {
  printMainHeader("I2C DETECT");

  std::string cmd = "i2cdetect -l";
  std::cout << cmd << std::endl;
  std::cout << run_cmd_no_check(cmd) << std::endl;

  std::set<int> bus_to_ignore = i2cBusIgnore();
  for (int bus = 0; bus <= get_max_i2c_bus(); ++bus) {
    if (bus_to_ignore.find(bus) == bus_to_ignore.end()) {
      cmd = "i2cdetect -y " + std::to_string(bus);
      std::cout << cmd << std::endl
                << run_cmd_with_timeout(cmd, 30) << std::endl;
    }
  }
}

void Showtech::printLogs() {
  printMainHeader("DEBUG LOGS");

  const std::string alt_platform_manager_log_path =
      "/var/facebook/logs/fboss/platform_manager.log";
  const std::string alt_sensor_service_log_path =
      "/var/facebook/logs/fboss/sensor_service.log";
  const std::string alt_data_corral_log_path =
      "/var/facebook/logs/fboss/data_corral_service.log";
  const std::string alt_fan_service_log_path =
      "/var/facebook/logs/fboss/fan_service.log";

  printSubHeader("PLATFORM MANAGER LOG");
  if (std::filesystem::exists(alt_platform_manager_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_platform_manager_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u platform_manager")
              << std::endl;
  }

  printSubHeader("SENSOR SERVICE LOG");
  if (std::filesystem::exists(alt_sensor_service_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_sensor_service_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u sensor_service")
              << std::endl;
  }

  printSubHeader("FAN SERVICE LOG");
  if (std::filesystem::exists(alt_fan_service_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_fan_service_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u fan_service") << std::endl;
  }

  printSubHeader("DATA CORRAL LOG");
  if (std::filesystem::exists(alt_data_corral_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_data_corral_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u data_corral_service")
              << std::endl;
  }

  printSubHeader("QSFP LOG");
  std::cout << run_cmd_with_limit("journalctl -u qsfp_service") << std::endl;

  printSubHeader("SW AGENT LOG");
  std::cout << run_cmd_with_limit("journalctl -u fboss_sw_agent") << std::endl;

  printSubHeader("HW AGENT LOG");
  std::cout << run_cmd_with_limit("journalctl -u fboss_hw_agent@0")
            << std::endl;

  printSubHeader("DMESG LOG");
  std::cout << run_cmd_with_limit("dmesg") << std::endl;

  printSubHeader("BOOT CONSOLE LOG");
  std::cout << run_cmd_with_limit("cat /var/log/boot.log") << std::endl;

  printSubHeader("LINUX MESSAGES LOG");
  std::cout << run_cmd_with_limit("cat /var/log/messages") << std::endl;
}

void Showtech::printL1Info() {
  printMainHeader("L1 LOGS");

  print_fboss2_show_cmd("port");
  print_fboss2_show_cmd("fabric");
  print_fboss2_show_cmd("lldp");
  print_fboss2_show_cmd("interface counters");
  print_fboss2_show_cmd("interface errors");
  print_fboss2_show_cmd("interface flaps");
  print_fboss2_show_cmd("interface phy");
  print_fboss2_show_cmd("transceiver");

  if (!ramdisk_) {
    printSubHeader("wedge_qsfp_util");
    std::cout << run_cmd_with_timeout("wedge_qsfp_util", 30) << std::endl;
  }
}

void Showtech::printSensors() {
  printMainHeader("SENSORS DUMP");
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
  printI2cDetect();
  printLogs();
}

} // namespace showtech
