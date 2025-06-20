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

void Showtech::_printMainHeader(std::string_view headerName) {
  std::string topPadding = std::string(headerName.size() + 12, '#');
  std::cout << topPadding << "\n";
  std::cout << "##### " << headerName << " #####\n";
  std::cout << topPadding << "\n\n";
}

void Showtech::_printSubHeader(std::string_view headerName) {
  std::cout << "#### " << headerName << " ####\n";
}

void Showtech::print_fboss2_show_cmd(std::string cmd) {
  if (!ramdisk_) {
    _printSubHeader("fboss2 show " + cmd);
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

  _printSubHeader(target + " SERIAL NUMBER");
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
  _printMainHeader("SHOWTECH VERSION " + version);
}

void Showtech::printCpuDetails() {
  _printMainHeader("HOST DETAILS");

  _printSubHeader("CPU SYSTEM TIME");
  std::cout << run_cmd_no_check("date") << std::endl;

  _printSubHeader("CPU HOSTNAME");
  std::cout << run_cmd_no_check("hostname") << std::endl;

  _printSubHeader("CPU Linux Kernel Version");
  std::cout << run_cmd_no_check("uname -r") << std::endl;

  _printSubHeader("CPU UPTIME");
  std::cout << run_cmd_no_check("uptime") << std::endl;
}

void Showtech::printFbossDetails() {
  _printMainHeader("FBOSS DETAILS");

  print_fboss2_show_cmd("product");
  print_fboss2_show_cmd("version agent");
  print_fboss2_show_cmd("environment sensor");
  print_fboss2_show_cmd("environment temperature");
  print_fboss2_show_cmd("environment fan");
  print_fboss2_show_cmd("environment power");
}

void Showtech::printLspci() {
  _printMainHeader("LSPCI");

  std::string cmd = "lspci";
  if (verbose_) {
    cmd = cmd + " -vvv";
  }
  std::cout << cmd << std::endl;
  std::cout << run_cmd_no_check(cmd) << std::endl;
}

void Showtech::printI2cDetect() {
  _printMainHeader("I2C DETECT");

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
  _printMainHeader("DEBUG LOGS");

  const std::string alt_platform_manager_log_path =
      "/var/facebook/logs/fboss/platform_manager.log";
  const std::string alt_sensor_service_log_path =
      "/var/facebook/logs/fboss/sensor_service.log";
  const std::string alt_data_corral_log_path =
      "/var/facebook/logs/fboss/data_corral_service.log";
  const std::string alt_fan_service_log_path =
      "/var/facebook/logs/fboss/fan_service.log";

  _printSubHeader("PLATFORM MANAGER LOG");
  if (std::filesystem::exists(alt_platform_manager_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_platform_manager_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u platform_manager")
              << std::endl;
  }

  _printSubHeader("SENSOR SERVICE LOG");
  if (std::filesystem::exists(alt_sensor_service_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_sensor_service_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u sensor_service")
              << std::endl;
  }

  _printSubHeader("FAN SERVICE LOG");
  if (std::filesystem::exists(alt_fan_service_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_fan_service_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u fan_service") << std::endl;
  }

  _printSubHeader("DATA CORRAL LOG");
  if (std::filesystem::exists(alt_data_corral_log_path)) {
    std::cout << run_cmd_with_limit("cat " + alt_data_corral_log_path)
              << std::endl;
  } else {
    std::cout << run_cmd_with_limit("journalctl -u data_corral_service")
              << std::endl;
  }

  _printSubHeader("QSFP LOG");
  std::cout << run_cmd_with_limit("journalctl -u qsfp_service") << std::endl;

  _printSubHeader("SW AGENT LOG");
  std::cout << run_cmd_with_limit("journalctl -u fboss_sw_agent") << std::endl;

  _printSubHeader("HW AGENT LOG");
  std::cout << run_cmd_with_limit("journalctl -u fboss_hw_agent@0")
            << std::endl;

  _printSubHeader("DMESG LOG");
  std::cout << run_cmd_with_limit("dmesg") << std::endl;

  _printSubHeader("BOOT CONSOLE LOG");
  std::cout << run_cmd_with_limit("cat /var/log/boot.log") << std::endl;

  _printSubHeader("LINUX MESSAGES LOG");
  std::cout << run_cmd_with_limit("cat /var/log/messages") << std::endl;

  _printSubHeader("NVME SSD SMART LOG");
  std::cout << run_cmd_no_check("nvme smart-log /dev/nvme0n1") << std::endl;

  _printSubHeader("NVME SSD ERROR LOG");
  std::cout << run_cmd_no_check("nvme error-log /dev/nvme0n1") << std::endl;

  _printSubHeader("NVME SSD ID CTRL LOG");
  std::cout << run_cmd_no_check("nvme id-ctrl /dev/nvme0n1") << std::endl;
}

void Showtech::printL1Info() {
  _printMainHeader("L1 LOGS");

  print_fboss2_show_cmd("port");
  print_fboss2_show_cmd("fabric");
  print_fboss2_show_cmd("lldp");
  print_fboss2_show_cmd("interface counters");
  print_fboss2_show_cmd("interface errors");
  print_fboss2_show_cmd("interface flaps");
  print_fboss2_show_cmd("interface phy");
  print_fboss2_show_cmd("transceiver");

  if (verbose_ && !ramdisk_) {
    _printSubHeader("wedge_qsfp_util");
    std::cout << run_cmd_with_timeout("wedge_qsfp_util", 30) << std::endl;
  }
}

void Showtech::printSensors() {
  _printMainHeader("SENSORS DUMP");
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
