// Copyright (c) 2022 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "DarwinShowtech.h"
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <unistd.h>

namespace showtech {

void DarwinShowtech::printSwitchcardPowergood() {
  std::cout << "##### SWITCHCARD POWERGOOD STATUS #####\n";

  switchcardCpld->printSysfsAttr("switch_card_pwr_status", "POWERGOOD");
  std::cout << std::endl;
}

void DarwinShowtech::printFpgaVersion(std::string target,
                                      std::string sysfsPath) {
  std::string majorRevFile;
  std::string minorRevFile;
  std::string majorRev;
  std::string minorRev;

  if (target == "CPU_CPLD" || target == "SWITCHCARD_SCD") {
    majorRevFile = "fpga_ver";
    minorRevFile = "fpga_sub_ver";
  } else if (target == "SWITCHCARD_CPLD" || target == "FAN_CPLD") {
    majorRevFile = "cpld_ver";
    minorRevFile = "cpld_sub_ver";
  } else if (target == "SAT_CPLD0") {
    majorRevFile = "sat0_cpld_ver";
    minorRevFile = "sat0_cpld_sub_ver";
  } else {
    majorRevFile = "sat1_cpld_ver";
    minorRevFile = "sat1_cpld_sub_ver";
  }

  if (run_cmd("head -n 1 " + sysfsPath + majorRevFile, majorRev) == 0 &&
      run_cmd("head -n 1 " + sysfsPath + minorRevFile, minorRev) == 0 &&
      majorRev != "" && minorRev != "") {
    strip(majorRev);
    strip(minorRev);
    std::cout << target << ": " << std::stoul(majorRev, nullptr, 16) << "."
              << std::stoul(minorRev, nullptr, 16) << std::endl;
  } else {
    std::cout << target << ": VERSION_NOT_DETECTED" << std::endl;
  }
}

void DarwinShowtech::printAllFpgaVersions() {
  std::cout << "##### FPGA VERSIONS #####\n";

  printFpgaVersion("CPU_CPLD", cpuCpld->sysfsPath);
  printFpgaVersion("SWITCHCARD_CPLD", switchcardCpld->sysfsPath);
  printFpgaVersion("SWITCHCARD_SCD", switchcardScd->sysfsPath);
  printFpgaVersion("SAT_CPLD0", switchcardScd->sysfsPath);
  printFpgaVersion("SAT_CPLD1", switchcardScd->sysfsPath);
  printFpgaVersion("FAN_CPLD", fanCpld->sysfsPath);
  std::cout << std::endl;
}

void DarwinShowtech::printPemInfo() {
  std::cout << "################################\n";
  std::cout << "######## PEM DEBUG INFO ########\n";
  std::cout << "################################\n\n";

  switchcardScd->printSysfsAttr("pem_present", "PRESENT");
  switchcardScd->printSysfsAttr("pem_input_ok", "INPUT_OK");
  switchcardScd->printSysfsAttr("pem_status", "STATUS");
  std::cout << std::endl
            << run_cmd_no_check("/usr/bin/pem-util --get_pem_info")
            << std::endl;
}

void DarwinShowtech::printFanspinnerInfo() {
  std::string output;

  std::cout << "#######################################\n";
  std::cout << "######## FANSPINNER DEBUG INFO ########\n";
  std::cout << "#######################################\n\n";

  std::cout << "######## SLG4F4527 INFO ########\n";
  fanspinner->printSysfsAttr("pwm", "PWM");
  fanspinner->printSysfsAttr("fan1_input", "RPM");
  fanspinner->printSysfsAttr("idprom_wp", "IDPROM_WP");
  fanspinner->printSysfsAttr("rm_idprom_wp", "RACKMON_IDPROM_WP");
  fanspinner->printSysfsAttr("led_green", "LED_GREEN");
  fanspinner->printSysfsAttr("led_red", "LED_RED");

  std::cout << "\n######## PCA9539 GPIO INFO ########\n";
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
  unsigned int i, j;
  int pwm_pcnt;
  int fan_delay = 0.5;
  std::string rawPwm;
  std::string rpm;

  std::cout << "################################\n";
  std::cout << "######## FAN DEBUG INFO ########\n";
  std::cout << "################################\n\n";

  std::cout << "##### FAN PRESENCE #####\n";
  for (i = 1; i <= 5; ++i) {
    fanCpld->printSysfsAttr("fan" + std::to_string(i) + "_present",
                            "FAN " + std::to_string(i));
  }
  switchcardScd->printSysfsAttr("rackmon_present", "FANSPINNER FAN");

  std::cout << "\n##### FAN SPEED LOGS #####\n";
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
      pwm_pcnt = 100 * (255 - std::stoi(rawPwm)) / 255;
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
  std::cout << "################################\n";
  std::cout << "###### RACKMON DEBUG INFO ######\n";
  std::cout << "################################\n\n";

  std::cout << run_cmd_no_check("/usr/bin/rackmonctl status");
  if (verbose_) {
    std::cout << run_cmd_no_check("/usr/bin/rackmonctl info");
    std::cout << run_cmd_no_check("/usr/bin/rackmonctl data");
  }
  std::cout << "\n\n";
}

void DarwinShowtech::printI2cInfo() {
  std::cout << "##########################\n";
  std::cout << "##### I2C DEBUG INFO #####\n";
  std::cout << "##########################\n\n";

  std::cout << "##### SWITCHCARD CPLD I2CDUMP #####\n";
  std::cout << switchcardCpld->i2cDump() << std::endl;
  std::cout << "##### FAN CPLD I2CDUMP #####\n";
  std::cout << fanCpld->i2cDump() << std::endl;
}

void DarwinShowtech::printPlatformInfo() {
  cpuCpld = std::make_unique<PciScdDevice>("0000:ff:0b.3");
  switchcardScd = std::make_unique<PciScdDevice>("0000:07:00.0");
  switchcardCpld =
      std::make_unique<I2cDevice>(cpuCpld->addr, 2, 0, "23", "blackhawk-cpld");
  fanCpld = std::make_unique<I2cHwmonDevice>(cpuCpld->addr, 3, 0, "60",
                                             "rook-fan-cpld");
  fanspinner = std::make_unique<I2cHwmonDevice>(switchcardScd->addr, 1, 4, "08",
                                                "aslg4f4527");
  pca9539 = std::make_unique<I2cGpioDevice>(switchcardScd->addr, 1, 4, "74",
                                            "pca953x");

  printSwitchcardPowergood();

  // TODO: enable weutil support
  // printWeutil("chassis");
  // printWeutil("pem");
  // printWeutil("fanspinner");
  // printWeutil("rackmon");

  printAllFpgaVersions();
  printPemInfo();
  printFanspinnerInfo();
  printFanInfo();
  printRackmonInfo();

  if (verbose_) {
    printI2cInfo();
  }
}

} // namespace showtech
