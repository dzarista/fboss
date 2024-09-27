// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#include "CfmShowtech.h"
#include <filesystem>
#include <iostream>
#include <fstream>
#include <vector>
#include <numeric>

namespace cfm {

double forecast( double x, const std::vector< double > & x_values,
                 const std::vector< double > & y_values ) {
    size_t n = x_values.size();

    double sum_x = std::accumulate( x_values.begin(), x_values.end(), 0.0 );
    double sum_y = std::accumulate( y_values.begin(), y_values.end(), 0.0 );
    double sum_x2 = std::accumulate(
          x_values.begin(), x_values.end(), 0.0,
          []( double acc, double xi ) { return acc + xi * xi; } );
    double sum_xy = std::inner_product(
          x_values.begin(), x_values.end(), y_values.begin(), 0.0 );

    double m = ( n * sum_xy - sum_x * sum_y ) / ( n * sum_x2 - sum_x * sum_x );
    double b = ( sum_y - m * sum_x ) / n;

    return m * x + b;
}

int readIntFromFile( const std::string & filePath ) {
    std::ifstream file( filePath );

    if ( !file.is_open() ) {
        std::cerr << "Error: Could not open file " << filePath << std::endl;
        return -1;
    }

    int number;
    file >> number;
    return number;
}

int getPsuCount() {
   int psuCount = 0;
   for ( const auto &entry : std::filesystem::directory_iterator( sensorPath ) ) {
      std::string fileName = entry.path().filename().string();
      if ( fileName.find( "PSU" ) == 0 ) {
         psuCount++;
      }
   }
   return psuCount;
}

int getFanCount() {
   int fanCount = 0;
   for ( const auto &entry : std::filesystem::directory_iterator( sensorPath ) ) {
      std::string fileName = entry.path().filename().string();
      if ( fileName.find( "FAN_CPLD" ) == 0 ) {
         fanCount++;
      }
   }
   return fanCount;
}


int getFanId() {
   if ( getFanCount() == 1 ) {
      return readIntFromFile( sensorPath + "/FAN_CPLD/fan1_id" );
   }
   else {
      return readIntFromFile( sensorPath + "/FAN_CPLD0/fan1_id" );
   }
}

int getFanPwm() {
   return 0;
}

int getPsuPwm() {
   return 0;
}

double calcPsuCfm() {
   return 0;
}

double calcFanCfm() {
   if ( getFanCount() == 1 ) {
      double fanPwmPercent = ( static_cast< double >( getFanPwm() ) / MAX_PWM ) * 100.0;
   }
   return 0;
}

void printCfmInfo() {
   double totalCfm = calcFanCfm() + calcPsuCfm();
   std::cout << "TOTAL CFM: " << totalCfm <<  std::endl;
}

} //namespace cfm

