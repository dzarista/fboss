// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef SHOWTECH_UTILS_H
#define SHOWTECH_UTILS_H

#include <map>
#include <string>
#include <vector>

namespace showtech {
int run_cmd(std::string cmd, std::string &output);
std::string run_cmd_no_check(std::string cmd);
std::string run_cmd_with_limit(std::string cmd, int max_lines = 5000);
std::string run_cmd_with_timeout(std::string cmd, int timeout_s = 30);
void strip(std::string &str);
int get_max_i2c_bus();
std::string i2c_dump(int bus, int addr, char type = 'b');
int getI2cBusForScd(std::string pciAddr, int master, int bus);
void printMainHeader(std::string_view headerName);
void printSubHeader(std::string_view headerName);

class Device {
public:
  Device() {}
  Device(std::string path) { sysfsPath = path; }
  ~Device() = default;
  std::string sysfsPath;
  std::string readSysfsAttr(std::string attr);
  void printSysfsAttr(std::string attr, std::string label);
};

class PciScdDevice : public Device {
public:
  PciScdDevice(std::string pciAddr, std::string infoRomDir) {
    addr = pciAddr;
    sysfsPath = "/sys/bus/pci/drivers/scd/" + pciAddr + "/";
    infoRomPath = "/run/devmap/" + infoRomDir + "/";
  }
  std::string addr;
  std::string infoRomPath;
};

class I2cDevice : public Device {
public:
  I2cDevice(std::string scdPciAddr, int scdI2cMaster, int scdI2cBus,
            std::string deviceAddr, std::string driver) {
    addr = deviceAddr;
    i2cBus = getI2cBusForScd(scdPciAddr, scdI2cMaster, scdI2cBus);
    sysfsPath =
        "/sys/bus/i2c/drivers/" + driver + "/" + i2cBus + "-00" + addr + "/";
  }
  std::string addr;
  std::string i2cBus;
  std::string i2cDump();

private:
  std::string getI2cBusForScd(std::string pciAddr, int master, int bus);
};

class I2cHwmonDevice : public I2cDevice {
public:
  I2cHwmonDevice(std::string scdPciAddr, int scdI2cMaster, int scdI2cBus,
                 std::string deviceAddr, std::string driver)
      : I2cDevice(scdPciAddr, scdI2cMaster, scdI2cBus, deviceAddr, driver) {
    sysfsPath = getHwmonPath();
  }

private:
  std::string getHwmonPath();
};

class I2cGpioDevice : public I2cDevice {
public:
  I2cGpioDevice(std::string scdPciAddr, int scdI2cMaster, int scdI2cBus,
                std::string deviceAddr, std::string driver)
      : I2cDevice(scdPciAddr, scdI2cMaster, scdI2cBus, deviceAddr, driver) {
    gpioPath = getGpioPath();
  }
  std::string gpioPath;
  std::string getGpioInfo(int num, std::string label);
  std::string getGpioValue(int num, std::string label);
  void printGpioDump(const std::map<int, std::string> &gpioNames);

private:
  std::string getGpioPath();
};
} // namespace showtech

#endif // SHOWTECH_UTILS_H
