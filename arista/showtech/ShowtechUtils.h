// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef SHOWTECH_UTILS_H
#define SHOWTECH_UTILS_H

#include <string>

namespace showtech {
int run_cmd(std::string cmd, std::string &output);
std::string run_cmd_no_check(std::string cmd);
void print_fboss2_show_cmd(std::string cmd);
void strip(std::string &str);
int get_max_i2c_bus();
std::string i2c_dump(int bus, int addr);

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
  PciScdDevice(std::string pciAddr) {
    addr = pciAddr;
    sysfsPath = "/sys/bus/pci/drivers/scd/" + pciAddr + "/";
  }
  std::string addr;
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
  void printGpioValue(int num, std::string label);

private:
  std::string getGpioPath();
};
} // namespace showtech

#endif // SHOWTECH_UTILS_H
