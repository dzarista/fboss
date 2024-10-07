// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "CfmShowtech.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <numeric>

namespace showtech {

double forecast(double x, const std::array<double, ARRAY_SIZE> &known_x,
                const std::array<double, ARRAY_SIZE> &known_y) {
  double sum_x = 0.0, sum_y = 0.0, sum_x_squared = 0.0, sum_xy = 0.0;
  for (std::size_t i = 0; i < ARRAY_SIZE; ++i) {
    sum_x += known_x[i];
    sum_y += known_y[i];
    sum_x_squared += known_x[i] * known_x[i];
    sum_xy += known_x[i] * known_y[i];
  }
  double slope = (ARRAY_SIZE * sum_xy - sum_x * sum_y) /
                 (ARRAY_SIZE * sum_x_squared - sum_x * sum_x);
  double intercept = (sum_y - slope * sum_x) / ARRAY_SIZE;
  return slope * x + intercept;
}

int readIntFromFile(const std::string &filePath) {
  std::ifstream file(filePath);

  if (!file.is_open()) {
    std::cerr << "Error: Could not open file " << filePath << std::endl;
    return -1;
  }

  int number;
  file >> number;
  return number;
}

int getPsuCount() {
  int psuCount = 0;
  for (const auto &entry : std::filesystem::directory_iterator(SENSOR_PATH)) {
    std::string fileName = entry.path().filename().string();
    if (fileName.find("PSU") == 0) {
      psuCount++;
    }
  }
  return psuCount;
}

bool isPsuPowerOn(int psuNum) {
  return (readIntFromFile(SENSOR_PATH + "/PSU" + std::to_string(psuNum) +
                          "_PMBUS/power1_input") != 0);
}

std::string getProductName() {
  if (std::system("dmidecode -s system-product-name | grep -i meru800bia > "
                  "/dev/null 2>&1") == 0) {
    return "meru800bia";
  } else if (std::system("dmidecode -s system-product-name | grep -i "
                         "meru800bfa > /dev/null 2>&1") == 0) {
    return "meru800bfa";
  }

  return "Invalid product";
}

int getFanId() {
  if (getProductName() == "meru800bia") {
    return readIntFromFile(SENSOR_PATH + "/FAN_CPLD/fan1_id");
  } else if (getProductName() == "meru800bfa") {
    return readIntFromFile(SENSOR_PATH + "/FAN_CPLD0/fan1_id");
  } else
    return -1;
}

int getFanPwm(const std::string &filePath) {
  return readIntFromFile(filePath + "/pwm1");
}

int getPsuRpm(int psuNum) {
  return readIntFromFile(SENSOR_PATH + "/PSU" + std::to_string(psuNum) +
                         "_PMBUS/fan1_input") +
         readIntFromFile(SENSOR_PATH + "/PSU" + std::to_string(psuNum) +
                         "_PMBUS/fan2_input");
}

double getPsuPwm(int rpm) {
  if (SANYO_DENKI_FAN_IDS.count(getFanId())) {
    if (getProductName() == "meru800bia") {
      return forecast(rpm, VIPER_SD_PSU_RPM_LINE, PWM_LINE);
    } else if (getProductName() == "meru800bfa") {
      return forecast(rpm, WHISTLER_SD_PSU_RPM_LINE, PWM_LINE);
    } else
      return -1;
  }

  else if (DELTA_FAN_IDS.count(getFanId())) {
    if (getProductName() == "meru800bia") {
      return forecast(rpm, VIPER_DELTA_PSU_RPM_LINE, PWM_LINE);
    } else if (getProductName() == "meru800bfa") {
      return forecast(rpm, WHISTLER_DELTA_PSU_RPM_LINE, PWM_LINE);
    } else
      return -1;
  }

  else
    return -1;
}

double calcPsuCfm() {
  int poweredPsus = 0;
  double totalPsuRpm = 0;
  for (int psuNum = 1; psuNum <= getPsuCount(); psuNum++) {
    if (isPsuPowerOn(psuNum)) {
      totalPsuRpm += getPsuRpm(psuNum);
      poweredPsus++;
    }
  }
  double averagePsuRpm = totalPsuRpm / poweredPsus;
  double psuPwm = getPsuPwm(averagePsuRpm);

  if (SANYO_DENKI_FAN_IDS.count(getFanId())) {
    if (getProductName() == "meru800bia") {
      double psuCfm = forecast(psuPwm, PWM_LINE, VIPER_PSU_CFM_LINE);
      return psuCfm;
    } else if (getProductName() == "meru800bfa") {
      double psuCfm = forecast(psuPwm, PWM_LINE, WHISTLER_SD_PSU_CFM_LINE);
      return psuCfm;
    } else
      return -1;
  }

  else if (DELTA_FAN_IDS.count(getFanId())) {
    if (getProductName() == "meru800bia") {
      double psuCfm = forecast(psuPwm, PWM_LINE, VIPER_PSU_CFM_LINE);
      return psuCfm;
    } else if (getProductName() == "meru800bfa") {
      double psuCfm = forecast(psuPwm, PWM_LINE, WHISTLER_DELTA_PSU_CFM_LINE);
      return psuCfm;
    } else
      return -1;
  }
  return -1;
}
double calcFanCfm() {
  if (getProductName() == "meru800bia") {
    double fanPwmPercent =
        (static_cast<double>(getFanPwm(SENSOR_PATH + "/FAN_CPLD")) / MAX_PWM) *
        100.0;
    if (SANYO_DENKI_FAN_IDS.count(getFanId())) {
      double fanCfm = forecast(fanPwmPercent, PWM_LINE, VIPER_SD_FAN_LINE);
      return fanCfm;
    } else if (DELTA_FAN_IDS.count(getFanId())) {
      double fanCfm = forecast(fanPwmPercent, PWM_LINE, VIPER_DELTA_FAN_LINE);
      return fanCfm;
    } else
      return -1;
  }

  else if (getProductName() == "meru800bfa") {
    double fanPwmPercent1to4 =
        (static_cast<double>(getFanPwm(SENSOR_PATH + "/FAN_CPLD0")) / MAX_PWM) *
        100.0;
    double fanPwmPercent5to12 =
        (static_cast<double>(getFanPwm(SENSOR_PATH + "/FAN_CPLD1")) / MAX_PWM) *
        100.0;

    if (SANYO_DENKI_FAN_IDS.count(getFanId())) {
      double fanCfm1to4 =
          forecast(fanPwmPercent1to4, PWM_LINE, WHISTLER_SD_FAN_LINE_1TO4);
      double fanCfm5to12 =
          forecast(fanPwmPercent5to12, PWM_LINE, WHISTLER_SD_FAN_LINE_5TO12);
      return fanCfm1to4 + fanCfm5to12;
    } else if (DELTA_FAN_IDS.count(getFanId())) {
      double fanCfm1to4 =
          forecast(fanPwmPercent1to4, PWM_LINE, WHISTLER_DELTA_FAN_LINE_1TO4);
      double fanCfm5to12 =
          forecast(fanPwmPercent5to12, PWM_LINE, WHISTLER_DELTA_FAN_LINE_5TO12);
      return fanCfm1to4 + fanCfm5to12;
    } else
      return -1;
  }

  return -1;
}

void printCfmInfo() {
  if (calcFanCfm() == -1 || calcPsuCfm() == -1) {
    std::cout << "ERROR CALCULATING CFM. FAN OR PSU TYPE LIKELY NOT SUPPORTED"
              << std::endl;
  } else {
    double totalCfm = calcFanCfm() + calcPsuCfm();
    std::cout << "TOTAL CFM: " << totalCfm << std::endl;
  }
}

} // namespace showtech
