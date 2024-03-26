// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "Showtech.h"
#include "ShowtechUtils.h"
#include <filesystem>
#include <iostream>
#include <string>
#include <sstream>
#include <vector>

namespace showtech {

void Showtech::printVersion() {
  std::cout << "################################\n";
  std::cout << "##### SHOWTECH VERSION " << getVersion() << " #####\n";
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

void Showtech::printWeutil(std::string target) {
  std::string cmd = "weutil --eeprom " + target;
  std::filesystem::path ossConfigPath{"/opt/fboss/share/platform_configs/weutil.json"};

  if (std::filesystem::exists(ossConfigPath)) {
    // OSS doesn't support running weutil without the -config_file arg.
    cmd = cmd + " -config_file " + ossConfigPath.string();
  }
  std::cout << "##### " + target + " SERIAL NUMBER #####\n";
  std::cout << run_cmd_no_check(cmd) << std::endl;
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
      std::cout << cmd << std::endl << run_cmd_no_check(cmd) << std::endl;
    }
  }
}

void Showtech::printLogs() {
  std::cout << "################################\n";
  std::cout << "########## DEBUG LOGS ##########\n";
  std::cout << "################################\n\n";

  std::cout << "#### SENSORS LOG ####\n";
  std::cout << run_cmd_no_check("journalctl -u sensor_service") << std::endl;

  std::cout << "#### FAN LOG ####\n";
  std::cout << run_cmd_no_check("journalctl -u fan_service") << std::endl;

  std::cout << "#### DMESG LOG ####\n";
  std::cout << run_cmd_no_check("dmesg") << std::endl;

  std::cout << "#### BOOT CONSOLE LOG ####\n";
  std::cout << run_cmd_no_check("cat /var/log/boot.log") << std::endl;

  std::cout << "#### LINUX MESSAGES LOG ####\n";
  std::cout << run_cmd_no_check("cat /var/log/messages") << std::endl;
}

void Showtech::printL1Info() {
  // Get a list of ports in order to run commands that require interface to included. If the
  // command fails then ports vector remains empty.
  auto ports = std::vector<std::string>{};
  std::string portListStr;
  auto portsOk = run_cmd(
    "LANG=en_US.UTF-8 fboss2 show interface counters | awk '{print $1}' | tail -n +3",
    portListStr);
  if (portsOk == 0) {
    auto ss = std::stringstream{portListStr};
    for (std::string port; std::getline(ss, port, '\n');) {
      if (port.find("eth") != std::string::npos || port.find("fab") != std::string::npos){
        ports.push_back(port);
      }
    }
  }

  std::cout << "################################\n";
  std::cout << "########### L1 LOGS ############\n";
  std::cout << "################################\n\n";

  std::cout << "#### fboss2 show port ####\n";
  std::cout << run_cmd_no_check("LANG=en_US.UTF-8 fboss2 show port") << std::endl;
  std::cout << "#### fboss2 show fabric ####\n";
  std::cout << run_cmd_no_check("LANG=en_US.UTF-8 fboss2 show fabric") << std::endl;
  std::cout << "#### fboss2 show lldp ####\n";
  std::cout << run_cmd_no_check("LANG=en_US.UTF-8 fboss2 show lldp") << std::endl;

  std::cout << "#### fboss2 show interface counters ####\n";
  std::cout << run_cmd_no_check("LANG=en_US.UTF-8 fboss2 show interface counters") << std::endl;
  std::cout << "#### fboss2 show interface errors ####\n";
  std::cout << run_cmd_no_check("LANG=en_US.UTF-8 fboss2 show interface errors") << std::endl;
  std::cout << "#### fboss2 show interface flaps ####\n";
  std::cout << run_cmd_no_check("LANG=en_US.UTF-8 fboss2 show interface flaps") << std::endl;

  if (verbose_) {
    std::cout << "#### fboss2 show interface phy ####\n";
    for (std::string port: ports) {
      std::cout << run_cmd_no_check("LANG=en_US.UTF-8 fboss2 show interface " + port + " phy")
                << std::endl;
    }
  }
  std::cout << "#### fboss2 show transceiver ####\n";
  std::cout << run_cmd_no_check("LANG=en_US.UTF-8 fboss2 show transceiver") << std::endl;
  if (verbose_) {
    std::cout << "#### wedge_qsfp_util ####\n";
    std::cout << run_cmd_no_check("wedge_qsfp_util") << std::endl;
  }
}

void Showtech::printShowtech() {
  printVersion();
  printCpuDetails();
  printPlatformInfo();
  printL1Info();
  if (verbose_) {
    printI2cDetect();
    printLogs();
  }
}

} // namespace showtech
