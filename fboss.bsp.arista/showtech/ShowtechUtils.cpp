// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "ShowtechUtils.h"
#include <array>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <regex>
#include <string>

namespace showtech {

void printMainHeader(std::string_view headerName) {
  std::string topPadding = std::string(headerName.size() + 12, '#');
  std::cout << topPadding << "\n";
  std::cout << "##### " << headerName << " #####\n";
  std::cout << topPadding << "\n" << std::endl;
}

void printSubHeader(std::string_view headerName) {
  std::cout << "#### " << headerName << " ####" << std::endl;
}

int run_cmd(std::string cmd, std::string &output) {
  std::array<char, 128> buffer;
  std::string result;
  FILE *pipe = popen(cmd.c_str(), "r");

  if (!pipe) {
    return -1;
  }

  while (std::fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
    result += buffer.data();
  }
  output = result;
  int exit_status = pclose(pipe);

  return exit_status;
}

std::string run_cmd_no_check(std::string cmd) {
  std::string output;

  run_cmd(cmd, output);
  return output;
}

std::string run_cmd_with_limit(std::string cmd, int max_lines) {
  std::string count_cmd = cmd + " | wc -l";
  int total_lines = std::stoi(run_cmd_no_check(count_cmd));

  if (total_lines <= max_lines) {
    return run_cmd_no_check(cmd);
  }

  int half_max = max_lines / 2;
  std::string first_part =
      run_cmd_no_check(cmd + " | head -n " + std::to_string(half_max));
  std::string last_part =
      run_cmd_no_check(cmd + " | tail -n " + std::to_string(half_max));

  std::string truncation_message =
      "=== File exceeds " + std::to_string(max_lines) +
      " lines (total: " + std::to_string(total_lines) +
      "). Showing first and last " + std::to_string(half_max) +
      " lines only ===\n\n";

  return truncation_message + first_part +
         "\n\n=== " + std::to_string(total_lines - max_lines) +
         " lines truncated ===\n\n" + last_part;
}

std::string run_cmd_with_timeout(std::string cmd, int timeout_s) {
  std::string output;
  std::string cmd_with_timeout;

  cmd_with_timeout = "timeout " + std::to_string(timeout_s) + " " + cmd;

  int status = run_cmd(cmd_with_timeout, output);
  if (WEXITSTATUS(status) == 124) {
    output += "\nError: " + cmd + " timed out after " +
              std::to_string(timeout_s) + " seconds";
  }

  return output;
}

void strip(std::string &str) {
  const std::string stripChars = " \t\n\r\f\v";
  const size_t last = str.find_last_not_of(stripChars);
  if (std::string::npos == last) {
    str.clear();
    return;
  }
  str.erase(last + 1);
  const size_t first = str.find_first_not_of(stripChars);
  str.erase(0, first);
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

int getI2cBusForScd(std::string pciAddr, int master, int bus) {
  std::string output;
  std::stringstream i2c_bus_regex;
  std::smatch i2c_bus_match;

  if (run_cmd("/usr/sbin/i2cdetect -l", output)) {
    return -1;
  }

  i2c_bus_regex << "i2c-(\\d+).*SCD " << pciAddr << " SMBus master " << master
                << " bus " << bus;
  if (regex_search(output.cbegin(), output.cend(), i2c_bus_match,
                   std::regex(i2c_bus_regex.str()))) {
    if (i2c_bus_match.size() == 2) {
      return std::stoi(i2c_bus_match[1]);
    }
  }

  return -1;
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
  return cmd + "\n" + run_cmd_with_timeout(cmd, 15);
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

std::string I2cGpioDevice::getGpioValue(int lineIndex) {
  std::string cmd =
      "/usr/bin/gpioget " + gpioPath + " " + std::to_string(lineIndex);
  std::string output = run_cmd_no_check(cmd);
  strip(output);
  return output;
}

void I2cGpioDevice::printGpioDump(const std::map<int, std::string> &gpioLines) {
  for (const auto &[lineIndex, label] : gpioLines) {
    std::cout << "line " << std::setw(2) << lineIndex << ": " << label << " -> "
              << getGpioValue(lineIndex) << std::endl;
  }
}
} // namespace showtech
