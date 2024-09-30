// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "CfmShowtech.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <numeric>
#include <vector>

namespace showtech {

double forecast( double x, const std::array< double, ARRAY_SIZE > & known_x, const std::array< double, ARRAY_SIZE > & known_y ) {
    double sum_x = 0.0, sum_y = 0.0, sum_x_squared = 0.0, sum_xy = 0.0;
    for ( std::size_t i = 0; i < ARRAY_SIZE; ++i ) {
        sum_x += known_x[i];
        sum_y += known_y[i];
        sum_x_squared += known_x[i] * known_x[i];
        sum_xy += known_x[i] * known_y[i];
    }
    double slope = ( ARRAY_SIZE * sum_xy - sum_x * sum_y ) / ( ARRAY_SIZE * sum_x_squared - sum_x * sum_x );
    double intercept = ( sum_y - slope * sum_x ) / ARRAY_SIZE;
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
  for (const auto &entry : std::filesystem::directory_iterator(sensorPath)) {
    std::string fileName = entry.path().filename().string();
    if (fileName.find("PSU") == 0) {
      psuCount++;
    }
  }
  return psuCount;
}

int getFanCount() {
  int fanCount = 0;
  for (const auto &entry : std::filesystem::directory_iterator(sensorPath)) {
    std::string fileName = entry.path().filename().string();
    if (fileName.find("FAN_CPLD") == 0) {
      fanCount++;
    }
  }
  return fanCount;
}

int getFanId() {
  if (getFanCount() == 1) {
    return readIntFromFile(sensorPath + "/FAN_CPLD/fan1_id");
  } else {
    return readIntFromFile(sensorPath + "/FAN_CPLD0/fan1_id");
  }
}

int getFanPwm(const std::string &filePath) {
  return readIntFromFile(filePath + "/pwm1");
}

int getPsuRpm( int psuNum ) {
   return readIntFromFile( sensorPath + "/PSU" + std::to_string( psuNum ) + "_PMBUS/fan1_input" ) +
      readIntFromFile( sensorPath + "/PSU" + std::to_string( psuNum ) + "_PMBUS/fan2_input" );
}

double getPsuPwm( int rpm ) {
   // SanyoDenki
  if ( getFanId() == 0 ) {
     if ( getFanCount() == 1 ) {
        return forecast( rpm, VIPER_SD_PSU_RPM_LINE, PWM_LINE );
     }
     else {
        return forecast( rpm, WHISTLER_SD_PSU_RPM_LINE, PWM_LINE );
     }
  }

  //  Delta
  else if ( getFanId() == 1 ) {
     if ( getFanCount() == 1 ) {
        return forecast( rpm, VIPER_DELTA_PSU_RPM_LINE, PWM_LINE );
     }
     else {
        return forecast( rpm, WHISTLER_DELTA_PSU_RPM_LINE, PWM_LINE );
     }
  }
  return -1;
}

double calcPsuCfm() {
   if ( getFanId() == 0 ) {
      if ( getFanCount() == 1 ) {
         int psuRpm = getPsuRpm( 1 );
         double psuPwm = getPsuPwm( psuRpm );
         double psuCfm = forecast( psuPwm, PWM_LINE, VIPER_PSU_CFM_LINE );
         return psuCfm;
      }
      else {
         double totalPsuRpm = 0;
         for ( int i = 1; i <= getPsuCount(); i++ ) {
            totalPsuRpm += getPsuRpm( 1 );
         }
         double averagePsuRpm = totalPsuRpm / getPsuCount() ;
         double psuPwm = getPsuPwm( averagePsuRpm );
         double psuCfm = forecast( psuPwm, PWM_LINE, WHISTLER_SD_PSU_CFM_LINE );
         return psuCfm;
      }
   }
   return 0;
}

double calcFanCfm() {
   if ( getFanId() == 0 ) {
      if ( getFanCount() == 1 ) {
         double fanPwmPercent = ( static_cast< double >( getFanPwm( sensorPath + "/FAN_CPLD" ) ) / MAX_PWM ) * 100.0;
         double fanCfm = forecast( fanPwmPercent, PWM_LINE, VIPER_SD_FAN_LINE );
         return fanCfm;
      }
      else {
         double fanPwmPercent1to4 = ( static_cast< double >( getFanPwm( sensorPath + "/FAN_CPLD0" ) ) / MAX_PWM ) * 100.0;
         double fanCfm1to4 = forecast( fanPwmPercent1to4, PWM_LINE, WHISTLER_SD_FAN_LINE_1TO4 );

         double fanPwmPercent5to12 = ( static_cast< double >( getFanPwm( sensorPath + "/FAN_CPLD1" ) ) / MAX_PWM ) * 100.0;
         double fanCfm5to12 = forecast( fanPwmPercent5to12, PWM_LINE, WHISTLER_SD_FAN_LINE_5TO12 );

         return fanCfm1to4 + fanCfm5to12;
      }
   }
  return 0;
}

void printCfmInfo() {
  double totalCfm = calcFanCfm() + calcPsuCfm();
  std::cout << "FAN CFM: " << calcFanCfm() << std::endl;
  std::cout << "PSU CFM: " << calcPsuCfm() << std::endl;
  std::cout << "TOTAL CFM: " << totalCfm << std::endl;
}

} // namespace showtech
