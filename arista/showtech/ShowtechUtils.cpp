// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "ShowtechUtils.h"
#include <filesystem>
#include <iostream>
#include <regex>
#include <string>

namespace showtech {

int run_cmd(std::string cmd, std::string &output) {
  std::array<char, 128> buffer;
  std::string result;
  std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"),
                                                pclose);

  if (!pipe) {
    return -1;
  }

  while (std::fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
    result += buffer.data();
  }
  output = result;

  return 0;
}

std::string run_cmd_no_check(std::string cmd) {
  std::string output;

  run_cmd(cmd, output);
  return output;
}

void print_fboss2_show_cmd(std::string cmd) {
  std::cout << "#### fboss2 show " << cmd << " ####\n";
  std::cout << run_cmd_no_check("LANG=en_US.UTF-8 fboss2 show " + cmd) << std::endl;
}

void strip(std::string &str) {
  str.erase(remove_if(str.begin(), str.end(), ::isspace), str.end());
}

int get_max_i2c_bus() {
  std::string output;

  if (run_cmd("/usr/sbin/i2cdetect -l | awk '{print $1}' | "
              "sed -e 's/i2c-//' | sort -n | tail -n 1",
              output)) {
    return 0;
  }

  strip(output);
  return std::stoi(output);
}

std::string i2c_dump(int bus, int addr) {
  std::string cmd = "i2cdump -f -y " + std::to_string(bus) + " " + std::to_string(addr) + " b";
  return cmd + "\n" + run_cmd_no_check(cmd);
}

std::string Device::readSysfsAttr(std::string attr) {
  return run_cmd_no_check("head -n 1 " + sysfsPath + attr);
}

void Device::printSysfsAttr(std::string attr, std::string label) {
  std::string value = readSysfsAttr(attr);
  std::cout << label << ": ";
  if (value != "") {
    std::cout << value;
  } else {
    std::cout << std::endl;
  }
}

std::string I2cDevice::getI2cBusForScd(std::string pciAddr, int master,
                                       int bus) {
  std::string output;
  std::stringstream i2c_bus_regex;
  std::smatch i2c_bus_match;

  if (run_cmd("/usr/sbin/i2cdetect -l", output)) {
    return "";
  }

  i2c_bus_regex << "i2c-(\\d+).*SCD " << pciAddr << " SMBus master " << master
                << " bus " << bus;
  if (regex_search(output.cbegin(), output.cend(), i2c_bus_match,
                   std::regex(i2c_bus_regex.str()))) {
    if (i2c_bus_match.size() == 2) {
      return i2c_bus_match[1];
    }
  }

  return "";
}

std::string I2cDevice::i2cDump() {
  std::string cmd = "i2cdump -f -y " + i2cBus + " " + "0x" + addr + " b";
  return cmd + "\n" + run_cmd_no_check(cmd);
}

std::string I2cHwmonDevice::getHwmonPath() {
  std::string cmd;
  std::string output;

  cmd = "find " + sysfsPath + "hwmon/ -mindepth 1 -type d -name hwmon*";
  if (run_cmd(cmd, output)) {
    return "";
  }

  strip(output);
  return output + "/";
}

std::string I2cGpioDevice::getGpioPath() {
  std::string output;

  if (run_cmd("find " + sysfsPath + " -type d -name gpiochip*", output)) {
    return "";
  }

  strip(output);
  return "/dev/" + output.substr(output.find_last_of("/\\") + 1);
}

void I2cGpioDevice::printGpioValue(int num, std::string label) {
  std::string cmd = "/usr/bin/gpioget " + gpioPath + " " + std::to_string(num);
  std::string output = run_cmd_no_check(cmd);
  strip(output);
  std::cout << label << ": " << output << std::endl;
}

} // namespace showtech
