// Copyright (c) 2024 Arista Networks, Inc.  All rights reserved.
// Arista Networks, Inc. Confidential and Proprietary.

#ifndef SHOWTECH_CFMSHOWTECH_H
#define SHOWTECH_CFMSHOWTECH_H

#include <array>
#include <set>
#include <string>

namespace showtech {

const int MAX_PWM = 255;
const size_t ARRAY_SIZE = 11;

const std::set<int> SANYO_DENKI_FAN_IDS = {0, 10};
const std::set<int> DELTA_FAN_IDS = {1, 9, 11};

const int VIPER_FAN_COUNT = 1;
const int WHISTLER_FAN_COUNT = 3;

const std::string SENSOR_PATH = "/run/devmap/sensors";

const std::array<double, ARRAY_SIZE> PWM_LINE = {100, 90, 80, 70, 60, 50,
                                                 40,  30, 20, 10, 0};
const std::array<double, ARRAY_SIZE> VIPER_SD_FAN_LINE = {
    353.22, 329.06, 304.72, 271.82, 243, 211.46,
    178.04, 147.72, 117.4,  77,     57.6};
const std::array<double, ARRAY_SIZE> VIPER_PSU_CFM_LINE = {
    19.39, 18.97, 16.14, 14.09, 12, 9.77, 7.48, 5.64, 4.8, 3.5, 2.2};
const std::array<double, ARRAY_SIZE> VIPER_SD_PSU_RPM_LINE = {
    23500, 23150, 20700, 18100, 15550, 12970, 10352, 7768, 6750, 6750, 6750};
const std::array<double, ARRAY_SIZE> VIPER_DELTA_PSU_RPM_LINE = {
    23584, 23248, 20688, 18176, 15520, 12976, 10367, 7740, 6916, 6916, 6916};
const std::array<double, ARRAY_SIZE> VIPER_DELTA_FAN_LINE = {
    377.82, 355.36, 323.22, 290.72, 255.6, 221.66,
    189.34, 151.62, 117.1,  87.2,   42.8};
const std::array<double, ARRAY_SIZE> WHISTLER_SD_FAN_LINE_1TO4 = {
    313.3, 293.9, 264.7, 241.2, 212.8, 183.2, 155.6, 131.2, 101.3, 76.4, 76.4};
const std::array<double, ARRAY_SIZE> WHISTLER_SD_FAN_LINE_5TO12 = {
    502.5, 469.7, 425.8, 382.2,  337.7, 292.6,
    249.2, 207.5, 161.3, 120.31, 120.31};
const std::array<double, ARRAY_SIZE> WHISTLER_SD_PSU_CFM_LINE = {
    71.8, 67.2, 61.6, 56, 50.3, 45.6, 39.9, 35.3, 29.5, 29.5, 29.5};
const std::array<double, ARRAY_SIZE> WHISTLER_SD_PSU_RPM_LINE = {
    23500, 23300, 20800, 18100, 15550, 12910, 10360, 7750, 6200, 6200, 6200};
const std::array<double, ARRAY_SIZE> WHISTLER_DELTA_FAN_LINE_1TO4 = {
    330.1, 315.2, 279.9, 253.7, 224.5, 192.7, 165.3, 137.9, 106.8, 76.4, 76.1};
const std::array<double, ARRAY_SIZE> WHISTLER_DELTA_FAN_LINE_5TO12 = {
    529.5, 503.7, 450.2, 401.9, 356.3, 307.7,
    264.8, 218.1, 170.1, 120.4, 119.8};
const std::array<double, ARRAY_SIZE> WHISTLER_DELTA_PSU_CFM_LINE = {
    75.7, 72.1, 65.1, 58.9, 53.1, 48.0, 42.4, 37.1, 31.1, 29.5, 29.4};
const std::array<double, ARRAY_SIZE> WHISTLER_DELTA_PSU_RPM_LINE = {
    23552, 23104, 20680, 18152, 15600, 12936, 10376, 7764, 6360, 6360, 6360};

void printCfmInfo();
} // namespace showtech
#endif // SHOWTECH_CFMSHOWTECH_H
