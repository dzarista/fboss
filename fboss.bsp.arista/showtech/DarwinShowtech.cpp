// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "DarwinShowtech.h"
#include "PsuShowtech.h"
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <unistd.h>

namespace showtech {

void DarwinShowtech::printSwitchcardPowergood() {
  printMainHeader("SWITCHCARD POWERGOOD STATUS");

  switchcardCpld->printSysfsAttr("switch_card_pwr_status", "POWERGOOD");
  std::cout << std::endl;
}

void DarwinShowtech::printWeutilInfo() {
  printMainHeader("WEUTIL INFO");

  printWeutil("chassis");
  if (product == "darwin") {
    printWeutil("pem");
  }
  printWeutil("fanspinner");
  printWeutil("rackmon");
}

void DarwinShowtech::printAllFpgaVersions() {
  printMainHeader("FPGA VERSIONS");

  printFpgaVersion("CPU_CPLD", cpuCpld->infoRomPath, "fw_ver");
  printFpgaVersion("SWITCHCARD_CPLD", switchcardCpld->sysfsPath, "cpld_ver",
                   "cpld_sub_ver");
  printFpgaVersion("SWITCHCARD_SCD", switchcardScd->infoRomPath, "fw_ver");
  printFpgaVersion("SAT_CPLD0", switchcardScd->sysfsPath, "sat0_cpld_ver",
                   "sat0_cpld_sub_ver");
  printFpgaVersion("SAT_CPLD1", switchcardScd->sysfsPath, "sat1_cpld_ver",
                   "sat1_cpld_sub_ver");
  printFpgaVersion("FAN_CPLD", fanCpld->sysfsPath, "cpld_ver", "cpld_sub_ver");
  std::cout << std::endl;
}

void DarwinShowtech::printPemInfo() {
  printMainHeader("PEM DEBUG INFO");

  switchcardScd->printSysfsAttr("pem_present", "PRESENT");
  switchcardScd->printSysfsAttr("pem_input_ok", "INPUT_OK");
  switchcardScd->printSysfsAttr("pem_status", "STATUS");
  std::cout << std::endl
            << run_cmd_no_check("/usr/bin/pem-util --get_pem_info")
            << std::endl;
}

void DarwinShowtech::printFanspinnerInfo() {
  printMainHeader("FANSPINNER DEBUG INFO");

  printSubHeader("SLG4F4527 INFO");
  fanspinner->printSysfsAttr("pwm", "PWM");
  fanspinner->printSysfsAttr("fan1_input", "RPM");
  fanspinner->printSysfsAttr("idprom_wp", "IDPROM_WP");
  fanspinner->printSysfsAttr("rm_idprom_wp", "RACKMON_IDPROM_WP");
  fanspinner->printSysfsAttr("led_green", "LED_GREEN");
  fanspinner->printSysfsAttr("led_red", "LED_RED");

  printSubHeader("PCA9539 GPIO INFO");
  if (pca9539->gpioPath == "") {
    std::cout << "PCA9539 GPIO Expander NOT DETECTED" << std::endl;
  } else {
    pca9539->printGpioValue(0, "RJ1_BKP_RED");
    pca9539->printGpioValue(1, "RJ2_BKP_RED");
    pca9539->printGpioValue(2, "RJ3_BKP_RED");
    pca9539->printGpioValue(3, "GPIO_FTDI_RST");
    pca9539->printGpioValue(4, "RJ1_PWR_OK");
    pca9539->printGpioValue(5, "RJ2_PWR_OK");
    pca9539->printGpioValue(6, "RJ3_PWR_OK");
    pca9539->printGpioValue(9, "BMC_MOD_ID0");
    pca9539->printGpioValue(10, "BMC_MOD_ID1");
    pca9539->printGpioValue(11, "BMC_MOD_ID2");
    pca9539->printGpioValue(12, "BMC_ALIVE");
    pca9539->printGpioValue(13, "BMC_PGOOD_CONN");
    pca9539->printGpioValue(14, "IOEXP_BMC_RESET");
    pca9539->printGpioValue(15, "BMC_PRSNT_L");
  }
  std::cout << std::endl;
}

void DarwinShowtech::printFanInfo() {
  printMainHeader("FAN DEBUG INFO");
  unsigned int i, j;
  int pwm_pcnt;
  int fan_delay = 0.5;
  std::string rawPwm;
  std::string rpm;

  printSubHeader("FAN PRESENCE");
  for (i = 1; i <= 5; ++i) {
    fanCpld->printSysfsAttr("fan" + std::to_string(i) + "_present",
                            "FAN " + std::to_string(i));
  }
  switchcardScd->printSysfsAttr("rackmon_present", "FANSPINNER FAN");

  printSubHeader("FAN SPEED LOGS");
  for (i = 0; i < 2; ++i) {
    for (j = 1; j <= 5; ++j) {
      rawPwm = fanCpld->readSysfsAttr("pwm" + std::to_string(j));
      rpm = fanCpld->readSysfsAttr("fan" + std::to_string(j) + "_input");
      if (rawPwm != "" && rpm != "") {
        pwm_pcnt = 100 * std::stoi(rawPwm) / 255;
        strip(rpm);
        std::cout << "FAN " << j << " RPM: " << rpm << " (" << pwm_pcnt
                  << "%)\n";
      } else {
        std::cout << "FAN " << j << " SPEED UNKNOWN\n";
      }
    }

    rawPwm = fanspinner->readSysfsAttr("pwm");
    rpm = fanspinner->readSysfsAttr("fan1_input");
    if (rawPwm != "" && rpm != "") {
      pwm_pcnt = 100 * std::stoi(rawPwm) / 255;
      strip(rpm);
      std::cout << "FANSPINNER FAN RPM: " << rpm << " (" << pwm_pcnt << "%)\n";
    } else {
      std::cout << "FANSPINNER FAN SPEED UNKNOWN\n";
    }

    if (!i) {
      std::cout << "\nSleeping " << fan_delay << " seconds...\n\n";
      sleep(fan_delay);
    }
  }
  std::cout << std::endl;
}

void DarwinShowtech::printRackmonInfo() {
  printMainHeader("RACKMON DEBUG INFO");

  std::cout << run_cmd_no_check("/usr/bin/rackmonctl status");
  std::cout << run_cmd_no_check("/usr/bin/rackmonctl info");
  std::cout << run_cmd_no_check("/usr/bin/rackmonctl data");

  std::cout << "\n\n";
}

void DarwinShowtech::printI2cInfo() {
  printMainHeader("I2C DEBUG INFO");

  printSubHeader("SWITCHCARD CPLD I2CDUMP");
  std::cout << switchcardCpld->i2cDump() << std::endl;

  printSubHeader("FAN CPLD I2CDUMP");
  std::cout << fanCpld->i2cDump() << std::endl;
}

void DarwinShowtech::printPsuShowtechInfo() {
  printMainHeader("PSU DEBUG INFO");
  printPsuInfo();
}

void DarwinShowtech::printPlatformInfo() {
  cpuCpld = std::make_unique<PciScdDevice>("0000:ff:0b.3",
                                           "cplds/ROOK_CPU_CPLD_INFO_ROM");
  switchcardScd =
      std::make_unique<PciScdDevice>("0000:07:00.0", "fpgas/SCD_FPGA_INFO_ROM");
  switchcardCpld =
      std::make_unique<I2cDevice>(cpuCpld->addr, 2, 0, "23", "blackhawk-cpld");
  fanCpld = std::make_unique<I2cHwmonDevice>(cpuCpld->addr, 3, 0, "60",
                                             "rook-fan-cpld");
  fanspinner = std::make_unique<I2cHwmonDevice>(switchcardScd->addr, 1, 4, "08",
                                                "aslg4f4527");
  pca9539 = std::make_unique<I2cGpioDevice>(switchcardScd->addr, 1, 4, "74",
                                            "pca953x");

  printSwitchcardPowergood();
  printWeutilInfo();
  printAllFpgaVersions();
  printPemInfo();
  printFanspinnerInfo();
  printFanInfo();
  if (product == "darwin48v") {
    printPsuShowtechInfo();
  }
  printRackmonInfo();
  printI2cInfo();
}

} // namespace showtech
