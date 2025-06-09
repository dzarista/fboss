// (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

#include "fboss/lib/bsp/glath05a-64o/Glath05a-64oBspPlatformMapping.h"
#include <thrift/lib/cpp2/protocol/Serializer.h>
#include "fboss/lib/bsp/BspPlatformMapping.h"
#include "fboss/lib/bsp/gen-cpp2/bsp_platform_mapping_types.h"

using namespace facebook::fboss;

namespace {

// This is generated from the csv under fboss/lib/bsp/bspmapping/input
constexpr auto kJsonBspPlatformMappingStr = R"(
{
  "pimMapping": {
    "1": {
      "pimID": 1,
      "tcvrMapping": {
        "1": {
          "tcvrId": 1,
          "accessControl": {
            "controllerId": "1",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_1/xcvr1_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_1/xcvr1_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "1",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_1"
          },
          "tcvrLaneToLedId": {
            "1": 2,
            "2": 2,
            "3": 2,
            "4": 2
          }
        },
        "2": {
          "tcvrId": 2,
          "accessControl": {
            "controllerId": "2",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_2/xcvr2_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_2/xcvr2_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "2",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_2"
          },
          "tcvrLaneToLedId": {
            "1": 4,
            "2": 4,
            "3": 4,
            "4": 4
          }
        },
        "3": {
          "tcvrId": 3,
          "accessControl": {
            "controllerId": "3",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_3/xcvr3_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_3/xcvr3_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "3",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_3"
          },
          "tcvrLaneToLedId": {
            "1": 6,
            "2": 6,
            "3": 6,
            "4": 6
          }
        },
        "4": {
          "tcvrId": 4,
          "accessControl": {
            "controllerId": "4",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_4/xcvr4_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_4/xcvr4_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "4",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_4"
          },
          "tcvrLaneToLedId": {
            "1": 8,
            "2": 8,
            "3": 8,
            "4": 8
          }
        },
        "5": {
          "tcvrId": 5,
          "accessControl": {
            "controllerId": "5",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_5/xcvr5_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_5/xcvr5_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "5",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_5"
          },
          "tcvrLaneToLedId": {
            "1": 10,
            "2": 10,
            "3": 10,
            "4": 10
          }
        },
        "6": {
          "tcvrId": 6,
          "accessControl": {
            "controllerId": "6",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_6/xcvr6_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_6/xcvr6_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "6",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_6"
          },
          "tcvrLaneToLedId": {
            "1": 12,
            "2": 12,
            "3": 12,
            "4": 12
          }
        },
        "7": {
          "tcvrId": 7,
          "accessControl": {
            "controllerId": "7",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_7/xcvr7_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_7/xcvr7_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "7",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_7"
          },
          "tcvrLaneToLedId": {
            "1": 14,
            "2": 14,
            "3": 14,
            "4": 14
          }
        },
        "8": {
          "tcvrId": 8,
          "accessControl": {
            "controllerId": "8",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_8/xcvr8_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_8/xcvr8_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "8",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_8"
          },
          "tcvrLaneToLedId": {
            "1": 16,
            "2": 16,
            "3": 16,
            "4": 16
          }
        },
        "9": {
          "tcvrId": 9,
          "accessControl": {
            "controllerId": "9",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_9/xcvr9_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_9/xcvr9_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "9",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_9"
          },
          "tcvrLaneToLedId": {
            "1": 18,
            "2": 18,
            "3": 18,
            "4": 18
          }
        },
        "10": {
          "tcvrId": 10,
          "accessControl": {
            "controllerId": "10",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_10/xcvr10_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_10/xcvr10_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "10",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_10"
          },
          "tcvrLaneToLedId": {
            "1": 20,
            "2": 20,
            "3": 20,
            "4": 20
          }
        },
        "11": {
          "tcvrId": 11,
          "accessControl": {
            "controllerId": "11",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_11/xcvr11_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_11/xcvr11_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "11",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_11"
          },
          "tcvrLaneToLedId": {
            "1": 22,
            "2": 22,
            "3": 22,
            "4": 22
          }
        },
        "12": {
          "tcvrId": 12,
          "accessControl": {
            "controllerId": "12",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_12/xcvr12_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_12/xcvr12_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "12",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_12"
          },
          "tcvrLaneToLedId": {
            "1": 24,
            "2": 24,
            "3": 24,
            "4": 24
          }
        },
        "13": {
          "tcvrId": 13,
          "accessControl": {
            "controllerId": "13",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_13/xcvr13_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_13/xcvr13_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "13",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_13"
          },
          "tcvrLaneToLedId": {
            "1": 26,
            "2": 26,
            "3": 26,
            "4": 26
          }
        },
        "14": {
          "tcvrId": 14,
          "accessControl": {
            "controllerId": "14",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_14/xcvr14_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_14/xcvr14_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "14",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_14"
          },
          "tcvrLaneToLedId": {
            "1": 28,
            "2": 28,
            "3": 28,
            "4": 28
          }
        },
        "15": {
          "tcvrId": 15,
          "accessControl": {
            "controllerId": "15",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_15/xcvr15_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_15/xcvr15_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "15",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_15"
          },
          "tcvrLaneToLedId": {
            "1": 30,
            "2": 30,
            "3": 30,
            "4": 30
          }
        },
        "16": {
          "tcvrId": 16,
          "accessControl": {
            "controllerId": "16",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_16/xcvr16_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_16/xcvr16_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "16",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_16"
          },
          "tcvrLaneToLedId": {
            "1": 32,
            "2": 32,
            "3": 32,
            "4": 32
          }
        },
        "17": {
          "tcvrId": 17,
          "accessControl": {
            "controllerId": "17",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_17/xcvr17_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_17/xcvr17_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "17",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_17"
          },
          "tcvrLaneToLedId": {
            "1": 34,
            "2": 34,
            "3": 34,
            "4": 34
          }
        },
        "18": {
          "tcvrId": 18,
          "accessControl": {
            "controllerId": "18",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_18/xcvr18_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_18/xcvr18_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "18",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_18"
          },
          "tcvrLaneToLedId": {
            "1": 36,
            "2": 36,
            "3": 36,
            "4": 36
          }
        },
        "19": {
          "tcvrId": 19,
          "accessControl": {
            "controllerId": "19",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_19/xcvr19_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_19/xcvr19_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "19",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_19"
          },
          "tcvrLaneToLedId": {
            "1": 38,
            "2": 38,
            "3": 38,
            "4": 38
          }
        },
        "20": {
          "tcvrId": 20,
          "accessControl": {
            "controllerId": "20",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_20/xcvr20_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_20/xcvr20_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "20",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_20"
          },
          "tcvrLaneToLedId": {
            "1": 40,
            "2": 40,
            "3": 40,
            "4": 40
          }
        },
        "21": {
          "tcvrId": 21,
          "accessControl": {
            "controllerId": "21",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_21/xcvr21_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_21/xcvr21_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "21",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_21"
          },
          "tcvrLaneToLedId": {
            "1": 42,
            "2": 42,
            "3": 42,
            "4": 42
          }
        },
        "22": {
          "tcvrId": 22,
          "accessControl": {
            "controllerId": "22",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_22/xcvr22_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_22/xcvr22_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "22",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_22"
          },
          "tcvrLaneToLedId": {
            "1": 44,
            "2": 44,
            "3": 44,
            "4": 44
          }
        },
        "23": {
          "tcvrId": 23,
          "accessControl": {
            "controllerId": "23",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_23/xcvr23_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_23/xcvr23_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "23",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_23"
          },
          "tcvrLaneToLedId": {
            "1": 46,
            "2": 46,
            "3": 46,
            "4": 46
          }
        },
        "24": {
          "tcvrId": 24,
          "accessControl": {
            "controllerId": "24",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_24/xcvr24_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_24/xcvr24_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "24",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_24"
          },
          "tcvrLaneToLedId": {
            "1": 48,
            "2": 48,
            "3": 48,
            "4": 48
          }
        },
        "25": {
          "tcvrId": 25,
          "accessControl": {
            "controllerId": "25",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_25/xcvr25_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_25/xcvr25_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "25",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_25"
          },
          "tcvrLaneToLedId": {
            "1": 50,
            "2": 50,
            "3": 50,
            "4": 50
          }
        },
        "26": {
          "tcvrId": 26,
          "accessControl": {
            "controllerId": "26",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_26/xcvr26_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_26/xcvr26_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "26",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_26"
          },
          "tcvrLaneToLedId": {
            "1": 52,
            "2": 52,
            "3": 52,
            "4": 52
          }
        },
        "27": {
          "tcvrId": 27,
          "accessControl": {
            "controllerId": "27",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_27/xcvr27_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_27/xcvr27_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "27",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_27"
          },
          "tcvrLaneToLedId": {
            "1": 54,
            "2": 54,
            "3": 54,
            "4": 54
          }
        },
        "28": {
          "tcvrId": 28,
          "accessControl": {
            "controllerId": "28",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_28/xcvr28_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_28/xcvr28_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "28",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_28"
          },
          "tcvrLaneToLedId": {
            "1": 56,
            "2": 56,
            "3": 56,
            "4": 56
          }
        },
        "29": {
          "tcvrId": 29,
          "accessControl": {
            "controllerId": "29",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_29/xcvr29_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_29/xcvr29_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "29",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_29"
          },
          "tcvrLaneToLedId": {
            "1": 58,
            "2": 58,
            "3": 58,
            "4": 58
          }
        },
        "30": {
          "tcvrId": 30,
          "accessControl": {
            "controllerId": "30",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_30/xcvr30_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_30/xcvr30_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "30",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_30"
          },
          "tcvrLaneToLedId": {
            "1": 60,
            "2": 60,
            "3": 60,
            "4": 60
          }
        },
        "31": {
          "tcvrId": 31,
          "accessControl": {
            "controllerId": "31",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_31/xcvr31_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_31/xcvr31_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "31",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_31"
          },
          "tcvrLaneToLedId": {
            "1": 62,
            "2": 62,
            "3": 62,
            "4": 62
          }
        },
        "32": {
          "tcvrId": 32,
          "accessControl": {
            "controllerId": "32",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_32/xcvr32_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_32/xcvr32_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "32",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_32"
          },
          "tcvrLaneToLedId": {
            "1": 64,
            "2": 64,
            "3": 64,
            "4": 64
          }
        },
        "33": {
          "tcvrId": 33,
          "accessControl": {
            "controllerId": "33",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_33/xcvr33_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_33/xcvr33_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "33",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_33"
          },
          "tcvrLaneToLedId": {
            "1": 66,
            "2": 66,
            "3": 66,
            "4": 66
          }
        },
        "34": {
          "tcvrId": 34,
          "accessControl": {
            "controllerId": "34",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_34/xcvr34_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_34/xcvr34_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "34",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_34"
          },
          "tcvrLaneToLedId": {
            "1": 68,
            "2": 68,
            "3": 68,
            "4": 68
          }
        },
        "35": {
          "tcvrId": 35,
          "accessControl": {
            "controllerId": "35",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_35/xcvr35_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_35/xcvr35_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "35",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_35"
          },
          "tcvrLaneToLedId": {
            "1": 70,
            "2": 70,
            "3": 70,
            "4": 70
          }
        },
        "36": {
          "tcvrId": 36,
          "accessControl": {
            "controllerId": "36",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_36/xcvr36_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_36/xcvr36_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "36",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_36"
          },
          "tcvrLaneToLedId": {
            "1": 72,
            "2": 72,
            "3": 72,
            "4": 72
          }
        },
        "37": {
          "tcvrId": 37,
          "accessControl": {
            "controllerId": "37",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_37/xcvr37_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_37/xcvr37_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "37",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_37"
          },
          "tcvrLaneToLedId": {
            "1": 74,
            "2": 74,
            "3": 74,
            "4": 74
          }
        },
        "38": {
          "tcvrId": 38,
          "accessControl": {
            "controllerId": "38",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_38/xcvr38_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_38/xcvr38_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "38",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_38"
          },
          "tcvrLaneToLedId": {
            "1": 76,
            "2": 76,
            "3": 76,
            "4": 76
          }
        },
        "39": {
          "tcvrId": 39,
          "accessControl": {
            "controllerId": "39",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_39/xcvr39_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_39/xcvr39_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "39",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_39"
          },
          "tcvrLaneToLedId": {
            "1": 78,
            "2": 78,
            "3": 78,
            "4": 78
          }
        },
        "40": {
          "tcvrId": 40,
          "accessControl": {
            "controllerId": "40",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_40/xcvr40_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_40/xcvr40_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "40",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_40"
          },
          "tcvrLaneToLedId": {
            "1": 80,
            "2": 80,
            "3": 80,
            "4": 80
          }
        },
        "41": {
          "tcvrId": 41,
          "accessControl": {
            "controllerId": "41",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_41/xcvr41_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_41/xcvr41_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "41",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_41"
          },
          "tcvrLaneToLedId": {
            "1": 82,
            "2": 82,
            "3": 82,
            "4": 82
          }
        },
        "42": {
          "tcvrId": 42,
          "accessControl": {
            "controllerId": "42",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_42/xcvr42_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_42/xcvr42_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "42",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_42"
          },
          "tcvrLaneToLedId": {
            "1": 84,
            "2": 84,
            "3": 84,
            "4": 84
          }
        },
        "43": {
          "tcvrId": 43,
          "accessControl": {
            "controllerId": "43",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_43/xcvr43_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_43/xcvr43_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "43",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_43"
          },
          "tcvrLaneToLedId": {
            "1": 86,
            "2": 86,
            "3": 86,
            "4": 86
          }
        },
        "44": {
          "tcvrId": 44,
          "accessControl": {
            "controllerId": "44",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_44/xcvr44_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_44/xcvr44_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "44",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_44"
          },
          "tcvrLaneToLedId": {
            "1": 88,
            "2": 88,
            "3": 88,
            "4": 88
          }
        },
        "45": {
          "tcvrId": 45,
          "accessControl": {
            "controllerId": "45",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_45/xcvr45_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_45/xcvr45_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "45",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_45"
          },
          "tcvrLaneToLedId": {
            "1": 90,
            "2": 90,
            "3": 90,
            "4": 90
          }
        },
        "46": {
          "tcvrId": 46,
          "accessControl": {
            "controllerId": "46",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_46/xcvr46_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_46/xcvr46_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "46",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_46"
          },
          "tcvrLaneToLedId": {
            "1": 92,
            "2": 92,
            "3": 92,
            "4": 92
          }
        },
        "47": {
          "tcvrId": 47,
          "accessControl": {
            "controllerId": "47",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_47/xcvr47_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_47/xcvr47_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "47",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_47"
          },
          "tcvrLaneToLedId": {
            "1": 94,
            "2": 94,
            "3": 94,
            "4": 94
          }
        },
        "48": {
          "tcvrId": 48,
          "accessControl": {
            "controllerId": "48",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_48/xcvr48_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_48/xcvr48_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "48",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_48"
          },
          "tcvrLaneToLedId": {
            "1": 96,
            "2": 96,
            "3": 96,
            "4": 96
          }
        },
        "49": {
          "tcvrId": 49,
          "accessControl": {
            "controllerId": "49",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_49/xcvr49_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_49/xcvr49_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "49",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_49"
          },
          "tcvrLaneToLedId": {
            "1": 98,
            "2": 98,
            "3": 98,
            "4": 98
          }
        },
        "50": {
          "tcvrId": 50,
          "accessControl": {
            "controllerId": "50",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_50/xcvr50_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_50/xcvr50_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "50",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_50"
          },
          "tcvrLaneToLedId": {
            "1": 100,
            "2": 100,
            "3": 100,
            "4": 100
          }
        },
        "51": {
          "tcvrId": 51,
          "accessControl": {
            "controllerId": "51",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_51/xcvr51_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_51/xcvr51_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "51",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_51"
          },
          "tcvrLaneToLedId": {
            "1": 102,
            "2": 102,
            "3": 102,
            "4": 102
          }
        },
        "52": {
          "tcvrId": 52,
          "accessControl": {
            "controllerId": "52",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_52/xcvr52_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_52/xcvr52_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "52",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_52"
          },
          "tcvrLaneToLedId": {
            "1": 104,
            "2": 104,
            "3": 104,
            "4": 104
          }
        },
        "53": {
          "tcvrId": 53,
          "accessControl": {
            "controllerId": "53",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_53/xcvr53_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_53/xcvr53_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "53",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_53"
          },
          "tcvrLaneToLedId": {
            "1": 106,
            "2": 106,
            "3": 106,
            "4": 106
          }
        },
        "54": {
          "tcvrId": 54,
          "accessControl": {
            "controllerId": "54",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_54/xcvr54_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_54/xcvr54_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "54",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_54"
          },
          "tcvrLaneToLedId": {
            "1": 108,
            "2": 108,
            "3": 108,
            "4": 108
          }
        },
        "55": {
          "tcvrId": 55,
          "accessControl": {
            "controllerId": "55",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_55/xcvr55_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_55/xcvr55_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "55",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_55"
          },
          "tcvrLaneToLedId": {
            "1": 110,
            "2": 110,
            "3": 110,
            "4": 110
          }
        },
        "56": {
          "tcvrId": 56,
          "accessControl": {
            "controllerId": "56",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_56/xcvr56_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_56/xcvr56_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "56",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_56"
          },
          "tcvrLaneToLedId": {
            "1": 112,
            "2": 112,
            "3": 112,
            "4": 112
          }
        },
        "57": {
          "tcvrId": 57,
          "accessControl": {
            "controllerId": "57",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_57/xcvr57_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_57/xcvr57_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "57",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_57"
          },
          "tcvrLaneToLedId": {
            "1": 114,
            "2": 114,
            "3": 114,
            "4": 114
          }
        },
        "58": {
          "tcvrId": 58,
          "accessControl": {
            "controllerId": "58",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_58/xcvr58_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_58/xcvr58_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "58",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_58"
          },
          "tcvrLaneToLedId": {
            "1": 116,
            "2": 116,
            "3": 116,
            "4": 116
          }
        },
        "59": {
          "tcvrId": 59,
          "accessControl": {
            "controllerId": "59",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_59/xcvr59_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_59/xcvr59_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "59",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_59"
          },
          "tcvrLaneToLedId": {
            "1": 118,
            "2": 118,
            "3": 118,
            "4": 118
          }
        },
        "60": {
          "tcvrId": 60,
          "accessControl": {
            "controllerId": "60",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_60/xcvr60_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_60/xcvr60_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "60",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_60"
          },
          "tcvrLaneToLedId": {
            "1": 120,
            "2": 120,
            "3": 120,
            "4": 120
          }
        },
        "61": {
          "tcvrId": 61,
          "accessControl": {
            "controllerId": "61",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_61/xcvr61_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_61/xcvr61_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "61",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_61"
          },
          "tcvrLaneToLedId": {
            "1": 122,
            "2": 122,
            "3": 122,
            "4": 122
          }
        },
        "62": {
          "tcvrId": 62,
          "accessControl": {
            "controllerId": "62",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_62/xcvr62_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_62/xcvr62_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "62",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_62"
          },
          "tcvrLaneToLedId": {
            "1": 124,
            "2": 124,
            "3": 124,
            "4": 124
          }
        },
        "63": {
          "tcvrId": 63,
          "accessControl": {
            "controllerId": "63",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_63/xcvr63_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_63/xcvr63_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "63",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_63"
          },
          "tcvrLaneToLedId": {
            "1": 126,
            "2": 126,
            "3": 126,
            "4": 126
          }
        },
        "64": {
          "tcvrId": 64,
          "accessControl": {
            "controllerId": "64",
            "type": 1,
            "reset": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_64/xcvr64_reset",
              "mask": 1,
              "gpioOffset": 0,
              "resetHoldHi": 0
            },
            "presence": {
              "sysfsPath": "/run/devmap/xcvrs/xcvr_ctrl_64/xcvr64_present",
              "mask": 1,
              "gpioOffset": 0,
              "presentHoldHi": 0
            },
            "gpioChip": ""
          },
          "io": {
            "controllerId": "64",
            "type": 1,
            "devicePath": "/run/devmap/xcvrs/xcvr_io_64"
          },
          "tcvrLaneToLedId": {
            "1": 128,
            "2": 128,
            "3": 128,
            "4": 128
          }
        }
      },
      "phyMapping": {},
      "phyIOControllers": {},
      "ledMapping": {
        "1": {
          "id": 1,
          "bluePath": "/sys/class/leds/port1_led1:blue:status",
          "yellowPath": "/sys/class/leds/port1_led1:yellow:status\r",
          "transceiverId": 1
        },
        "2": {
          "id": 2,
          "bluePath": "/sys/class/leds/port1_led2:blue:status",
          "yellowPath": "/sys/class/leds/port1_led2:yellow:status\r",
          "transceiverId": 1
        },
        "3": {
          "id": 3,
          "bluePath": "/sys/class/leds/port2_led1:blue:status",
          "yellowPath": "/sys/class/leds/port2_led1:yellow:status\r",
          "transceiverId": 2
        },
        "4": {
          "id": 4,
          "bluePath": "/sys/class/leds/port2_led2:blue:status",
          "yellowPath": "/sys/class/leds/port2_led2:yellow:status\r",
          "transceiverId": 2
        },
        "5": {
          "id": 5,
          "bluePath": "/sys/class/leds/port3_led1:blue:status",
          "yellowPath": "/sys/class/leds/port3_led1:yellow:status\r",
          "transceiverId": 3
        },
        "6": {
          "id": 6,
          "bluePath": "/sys/class/leds/port3_led2:blue:status",
          "yellowPath": "/sys/class/leds/port3_led2:yellow:status\r",
          "transceiverId": 3
        },
        "7": {
          "id": 7,
          "bluePath": "/sys/class/leds/port4_led1:blue:status",
          "yellowPath": "/sys/class/leds/port4_led1:yellow:status\r",
          "transceiverId": 4
        },
        "8": {
          "id": 8,
          "bluePath": "/sys/class/leds/port4_led2:blue:status",
          "yellowPath": "/sys/class/leds/port4_led2:yellow:status\r",
          "transceiverId": 4
        },
        "9": {
          "id": 9,
          "bluePath": "/sys/class/leds/port5_led1:blue:status",
          "yellowPath": "/sys/class/leds/port5_led1:yellow:status\r",
          "transceiverId": 5
        },
        "10": {
          "id": 10,
          "bluePath": "/sys/class/leds/port5_led2:blue:status",
          "yellowPath": "/sys/class/leds/port5_led2:yellow:status\r",
          "transceiverId": 5
        },
        "11": {
          "id": 11,
          "bluePath": "/sys/class/leds/port6_led1:blue:status",
          "yellowPath": "/sys/class/leds/port6_led1:yellow:status\r",
          "transceiverId": 6
        },
        "12": {
          "id": 12,
          "bluePath": "/sys/class/leds/port6_led2:blue:status",
          "yellowPath": "/sys/class/leds/port6_led2:yellow:status\r",
          "transceiverId": 6
        },
        "13": {
          "id": 13,
          "bluePath": "/sys/class/leds/port7_led1:blue:status",
          "yellowPath": "/sys/class/leds/port7_led1:yellow:status\r",
          "transceiverId": 7
        },
        "14": {
          "id": 14,
          "bluePath": "/sys/class/leds/port7_led2:blue:status",
          "yellowPath": "/sys/class/leds/port7_led2:yellow:status\r",
          "transceiverId": 7
        },
        "15": {
          "id": 15,
          "bluePath": "/sys/class/leds/port8_led1:blue:status",
          "yellowPath": "/sys/class/leds/port8_led1:yellow:status\r",
          "transceiverId": 8
        },
        "16": {
          "id": 16,
          "bluePath": "/sys/class/leds/port8_led2:blue:status",
          "yellowPath": "/sys/class/leds/port8_led2:yellow:status\r",
          "transceiverId": 8
        },
        "17": {
          "id": 17,
          "bluePath": "/sys/class/leds/port9_led1:blue:status",
          "yellowPath": "/sys/class/leds/port9_led1:yellow:status\r",
          "transceiverId": 9
        },
        "18": {
          "id": 18,
          "bluePath": "/sys/class/leds/port9_led2:blue:status",
          "yellowPath": "/sys/class/leds/port9_led2:yellow:status\r",
          "transceiverId": 9
        },
        "19": {
          "id": 19,
          "bluePath": "/sys/class/leds/port10_led1:blue:status",
          "yellowPath": "/sys/class/leds/port10_led1:yellow:status\r",
          "transceiverId": 10
        },
        "20": {
          "id": 20,
          "bluePath": "/sys/class/leds/port10_led2:blue:status",
          "yellowPath": "/sys/class/leds/port10_led2:yellow:status\r",
          "transceiverId": 10
        },
        "21": {
          "id": 21,
          "bluePath": "/sys/class/leds/port11_led1:blue:status",
          "yellowPath": "/sys/class/leds/port11_led1:yellow:status\r",
          "transceiverId": 11
        },
        "22": {
          "id": 22,
          "bluePath": "/sys/class/leds/port11_led2:blue:status",
          "yellowPath": "/sys/class/leds/port11_led2:yellow:status\r",
          "transceiverId": 11
        },
        "23": {
          "id": 23,
          "bluePath": "/sys/class/leds/port12_led1:blue:status",
          "yellowPath": "/sys/class/leds/port12_led1:yellow:status\r",
          "transceiverId": 12
        },
        "24": {
          "id": 24,
          "bluePath": "/sys/class/leds/port12_led2:blue:status",
          "yellowPath": "/sys/class/leds/port12_led2:yellow:status\r",
          "transceiverId": 12
        },
        "25": {
          "id": 25,
          "bluePath": "/sys/class/leds/port13_led1:blue:status",
          "yellowPath": "/sys/class/leds/port13_led1:yellow:status\r",
          "transceiverId": 13
        },
        "26": {
          "id": 26,
          "bluePath": "/sys/class/leds/port13_led2:blue:status",
          "yellowPath": "/sys/class/leds/port13_led2:yellow:status\r",
          "transceiverId": 13
        },
        "27": {
          "id": 27,
          "bluePath": "/sys/class/leds/port14_led1:blue:status",
          "yellowPath": "/sys/class/leds/port14_led1:yellow:status\r",
          "transceiverId": 14
        },
        "28": {
          "id": 28,
          "bluePath": "/sys/class/leds/port14_led2:blue:status",
          "yellowPath": "/sys/class/leds/port14_led2:yellow:status\r",
          "transceiverId": 14
        },
        "29": {
          "id": 29,
          "bluePath": "/sys/class/leds/port15_led1:blue:status",
          "yellowPath": "/sys/class/leds/port15_led1:yellow:status\r",
          "transceiverId": 15
        },
        "30": {
          "id": 30,
          "bluePath": "/sys/class/leds/port15_led2:blue:status",
          "yellowPath": "/sys/class/leds/port15_led2:yellow:status\r",
          "transceiverId": 15
        },
        "31": {
          "id": 31,
          "bluePath": "/sys/class/leds/port16_led1:blue:status",
          "yellowPath": "/sys/class/leds/port16_led1:yellow:status\r",
          "transceiverId": 16
        },
        "32": {
          "id": 32,
          "bluePath": "/sys/class/leds/port16_led2:blue:status",
          "yellowPath": "/sys/class/leds/port16_led2:yellow:status\r",
          "transceiverId": 16
        },
        "33": {
          "id": 33,
          "bluePath": "/sys/class/leds/port17_led1:blue:status",
          "yellowPath": "/sys/class/leds/port17_led1:yellow:status\r",
          "transceiverId": 17
        },
        "34": {
          "id": 34,
          "bluePath": "/sys/class/leds/port17_led2:blue:status",
          "yellowPath": "/sys/class/leds/port17_led2:yellow:status\r",
          "transceiverId": 17
        },
        "35": {
          "id": 35,
          "bluePath": "/sys/class/leds/port18_led1:blue:status",
          "yellowPath": "/sys/class/leds/port18_led1:yellow:status\r",
          "transceiverId": 18
        },
        "36": {
          "id": 36,
          "bluePath": "/sys/class/leds/port18_led2:blue:status",
          "yellowPath": "/sys/class/leds/port18_led2:yellow:status\r",
          "transceiverId": 18
        },
        "37": {
          "id": 37,
          "bluePath": "/sys/class/leds/port19_led1:blue:status",
          "yellowPath": "/sys/class/leds/port19_led1:yellow:status\r",
          "transceiverId": 19
        },
        "38": {
          "id": 38,
          "bluePath": "/sys/class/leds/port19_led2:blue:status",
          "yellowPath": "/sys/class/leds/port19_led2:yellow:status\r",
          "transceiverId": 19
        },
        "39": {
          "id": 39,
          "bluePath": "/sys/class/leds/port20_led1:blue:status",
          "yellowPath": "/sys/class/leds/port20_led1:yellow:status\r",
          "transceiverId": 20
        },
        "40": {
          "id": 40,
          "bluePath": "/sys/class/leds/port20_led2:blue:status",
          "yellowPath": "/sys/class/leds/port20_led2:yellow:status\r",
          "transceiverId": 20
        },
        "41": {
          "id": 41,
          "bluePath": "/sys/class/leds/port21_led1:blue:status",
          "yellowPath": "/sys/class/leds/port21_led1:yellow:status\r",
          "transceiverId": 21
        },
        "42": {
          "id": 42,
          "bluePath": "/sys/class/leds/port21_led2:blue:status",
          "yellowPath": "/sys/class/leds/port21_led2:yellow:status\r",
          "transceiverId": 21
        },
        "43": {
          "id": 43,
          "bluePath": "/sys/class/leds/port22_led1:blue:status",
          "yellowPath": "/sys/class/leds/port22_led1:yellow:status\r",
          "transceiverId": 22
        },
        "44": {
          "id": 44,
          "bluePath": "/sys/class/leds/port22_led2:blue:status",
          "yellowPath": "/sys/class/leds/port22_led2:yellow:status\r",
          "transceiverId": 22
        },
        "45": {
          "id": 45,
          "bluePath": "/sys/class/leds/port23_led1:blue:status",
          "yellowPath": "/sys/class/leds/port23_led1:yellow:status\r",
          "transceiverId": 23
        },
        "46": {
          "id": 46,
          "bluePath": "/sys/class/leds/port23_led2:blue:status",
          "yellowPath": "/sys/class/leds/port23_led2:yellow:status\r",
          "transceiverId": 23
        },
        "47": {
          "id": 47,
          "bluePath": "/sys/class/leds/port24_led1:blue:status",
          "yellowPath": "/sys/class/leds/port24_led1:yellow:status\r",
          "transceiverId": 24
        },
        "48": {
          "id": 48,
          "bluePath": "/sys/class/leds/port24_led2:blue:status",
          "yellowPath": "/sys/class/leds/port24_led2:yellow:status\r",
          "transceiverId": 24
        },
        "49": {
          "id": 49,
          "bluePath": "/sys/class/leds/port25_led1:blue:status",
          "yellowPath": "/sys/class/leds/port25_led1:yellow:status\r",
          "transceiverId": 25
        },
        "50": {
          "id": 50,
          "bluePath": "/sys/class/leds/port25_led2:blue:status",
          "yellowPath": "/sys/class/leds/port25_led2:yellow:status\r",
          "transceiverId": 25
        },
        "51": {
          "id": 51,
          "bluePath": "/sys/class/leds/port26_led1:blue:status",
          "yellowPath": "/sys/class/leds/port26_led1:yellow:status\r",
          "transceiverId": 26
        },
        "52": {
          "id": 52,
          "bluePath": "/sys/class/leds/port26_led2:blue:status",
          "yellowPath": "/sys/class/leds/port26_led2:yellow:status\r",
          "transceiverId": 26
        },
        "53": {
          "id": 53,
          "bluePath": "/sys/class/leds/port27_led1:blue:status",
          "yellowPath": "/sys/class/leds/port27_led1:yellow:status\r",
          "transceiverId": 27
        },
        "54": {
          "id": 54,
          "bluePath": "/sys/class/leds/port27_led2:blue:status",
          "yellowPath": "/sys/class/leds/port27_led2:yellow:status\r",
          "transceiverId": 27
        },
        "55": {
          "id": 55,
          "bluePath": "/sys/class/leds/port28_led1:blue:status",
          "yellowPath": "/sys/class/leds/port28_led1:yellow:status\r",
          "transceiverId": 28
        },
        "56": {
          "id": 56,
          "bluePath": "/sys/class/leds/port28_led2:blue:status",
          "yellowPath": "/sys/class/leds/port28_led2:yellow:status\r",
          "transceiverId": 28
        },
        "57": {
          "id": 57,
          "bluePath": "/sys/class/leds/port29_led1:blue:status",
          "yellowPath": "/sys/class/leds/port29_led1:yellow:status\r",
          "transceiverId": 29
        },
        "58": {
          "id": 58,
          "bluePath": "/sys/class/leds/port29_led2:blue:status",
          "yellowPath": "/sys/class/leds/port29_led2:yellow:status\r",
          "transceiverId": 29
        },
        "59": {
          "id": 59,
          "bluePath": "/sys/class/leds/port30_led1:blue:status",
          "yellowPath": "/sys/class/leds/port30_led1:yellow:status\r",
          "transceiverId": 30
        },
        "60": {
          "id": 60,
          "bluePath": "/sys/class/leds/port30_led2:blue:status",
          "yellowPath": "/sys/class/leds/port30_led2:yellow:status\r",
          "transceiverId": 30
        },
        "61": {
          "id": 61,
          "bluePath": "/sys/class/leds/port31_led1:blue:status",
          "yellowPath": "/sys/class/leds/port31_led1:yellow:status\r",
          "transceiverId": 31
        },
        "62": {
          "id": 62,
          "bluePath": "/sys/class/leds/port31_led2:blue:status",
          "yellowPath": "/sys/class/leds/port31_led2:yellow:status\r",
          "transceiverId": 31
        },
        "63": {
          "id": 63,
          "bluePath": "/sys/class/leds/port32_led1:blue:status",
          "yellowPath": "/sys/class/leds/port32_led1:yellow:status\r",
          "transceiverId": 32
        },
        "64": {
          "id": 64,
          "bluePath": "/sys/class/leds/port32_led2:blue:status",
          "yellowPath": "/sys/class/leds/port32_led2:yellow:status\r",
          "transceiverId": 32
        },
        "65": {
          "id": 65,
          "bluePath": "/sys/class/leds/port33_led1:blue:status",
          "yellowPath": "/sys/class/leds/port33_led1:yellow:status\r",
          "transceiverId": 33
        },
        "66": {
          "id": 66,
          "bluePath": "/sys/class/leds/port33_led2:blue:status",
          "yellowPath": "/sys/class/leds/port33_led2:yellow:status\r",
          "transceiverId": 33
        },
        "67": {
          "id": 67,
          "bluePath": "/sys/class/leds/port34_led1:blue:status",
          "yellowPath": "/sys/class/leds/port34_led1:yellow:status\r",
          "transceiverId": 34
        },
        "68": {
          "id": 68,
          "bluePath": "/sys/class/leds/port34_led2:blue:status",
          "yellowPath": "/sys/class/leds/port34_led2:yellow:status\r",
          "transceiverId": 34
        },
        "69": {
          "id": 69,
          "bluePath": "/sys/class/leds/port35_led1:blue:status",
          "yellowPath": "/sys/class/leds/port35_led1:yellow:status\r",
          "transceiverId": 35
        },
        "70": {
          "id": 70,
          "bluePath": "/sys/class/leds/port35_led2:blue:status",
          "yellowPath": "/sys/class/leds/port35_led2:yellow:status\r",
          "transceiverId": 35
        },
        "71": {
          "id": 71,
          "bluePath": "/sys/class/leds/port36_led1:blue:status",
          "yellowPath": "/sys/class/leds/port36_led1:yellow:status\r",
          "transceiverId": 36
        },
        "72": {
          "id": 72,
          "bluePath": "/sys/class/leds/port36_led2:blue:status",
          "yellowPath": "/sys/class/leds/port36_led2:yellow:status\r",
          "transceiverId": 36
        },
        "73": {
          "id": 73,
          "bluePath": "/sys/class/leds/port37_led1:blue:status",
          "yellowPath": "/sys/class/leds/port37_led1:yellow:status\r",
          "transceiverId": 37
        },
        "74": {
          "id": 74,
          "bluePath": "/sys/class/leds/port37_led2:blue:status",
          "yellowPath": "/sys/class/leds/port37_led2:yellow:status\r",
          "transceiverId": 37
        },
        "75": {
          "id": 75,
          "bluePath": "/sys/class/leds/port38_led1:blue:status",
          "yellowPath": "/sys/class/leds/port38_led1:yellow:status\r",
          "transceiverId": 38
        },
        "76": {
          "id": 76,
          "bluePath": "/sys/class/leds/port38_led2:blue:status",
          "yellowPath": "/sys/class/leds/port38_led2:yellow:status\r",
          "transceiverId": 38
        },
        "77": {
          "id": 77,
          "bluePath": "/sys/class/leds/port39_led1:blue:status",
          "yellowPath": "/sys/class/leds/port39_led1:yellow:status\r",
          "transceiverId": 39
        },
        "78": {
          "id": 78,
          "bluePath": "/sys/class/leds/port39_led2:blue:status",
          "yellowPath": "/sys/class/leds/port39_led2:yellow:status\r",
          "transceiverId": 39
        },
        "79": {
          "id": 79,
          "bluePath": "/sys/class/leds/port40_led1:blue:status",
          "yellowPath": "/sys/class/leds/port40_led1:yellow:status\r",
          "transceiverId": 40
        },
        "80": {
          "id": 80,
          "bluePath": "/sys/class/leds/port40_led2:blue:status",
          "yellowPath": "/sys/class/leds/port40_led2:yellow:status\r",
          "transceiverId": 40
        },
        "81": {
          "id": 81,
          "bluePath": "/sys/class/leds/port41_led1:blue:status",
          "yellowPath": "/sys/class/leds/port41_led1:yellow:status\r",
          "transceiverId": 41
        },
        "82": {
          "id": 82,
          "bluePath": "/sys/class/leds/port41_led2:blue:status",
          "yellowPath": "/sys/class/leds/port41_led2:yellow:status\r",
          "transceiverId": 41
        },
        "83": {
          "id": 83,
          "bluePath": "/sys/class/leds/port42_led1:blue:status",
          "yellowPath": "/sys/class/leds/port42_led1:yellow:status\r",
          "transceiverId": 42
        },
        "84": {
          "id": 84,
          "bluePath": "/sys/class/leds/port42_led2:blue:status",
          "yellowPath": "/sys/class/leds/port42_led2:yellow:status\r",
          "transceiverId": 42
        },
        "85": {
          "id": 85,
          "bluePath": "/sys/class/leds/port43_led1:blue:status",
          "yellowPath": "/sys/class/leds/port43_led1:yellow:status\r",
          "transceiverId": 43
        },
        "86": {
          "id": 86,
          "bluePath": "/sys/class/leds/port43_led2:blue:status",
          "yellowPath": "/sys/class/leds/port43_led2:yellow:status\r",
          "transceiverId": 43
        },
        "87": {
          "id": 87,
          "bluePath": "/sys/class/leds/port44_led1:blue:status",
          "yellowPath": "/sys/class/leds/port44_led1:yellow:status\r",
          "transceiverId": 44
        },
        "88": {
          "id": 88,
          "bluePath": "/sys/class/leds/port44_led2:blue:status",
          "yellowPath": "/sys/class/leds/port44_led2:yellow:status\r",
          "transceiverId": 44
        },
        "89": {
          "id": 89,
          "bluePath": "/sys/class/leds/port45_led1:blue:status",
          "yellowPath": "/sys/class/leds/port45_led1:yellow:status\r",
          "transceiverId": 45
        },
        "90": {
          "id": 90,
          "bluePath": "/sys/class/leds/port45_led2:blue:status",
          "yellowPath": "/sys/class/leds/port45_led2:yellow:status\r",
          "transceiverId": 45
        },
        "91": {
          "id": 91,
          "bluePath": "/sys/class/leds/port46_led1:blue:status",
          "yellowPath": "/sys/class/leds/port46_led1:yellow:status\r",
          "transceiverId": 46
        },
        "92": {
          "id": 92,
          "bluePath": "/sys/class/leds/port46_led2:blue:status",
          "yellowPath": "/sys/class/leds/port46_led2:yellow:status\r",
          "transceiverId": 46
        },
        "93": {
          "id": 93,
          "bluePath": "/sys/class/leds/port47_led1:blue:status",
          "yellowPath": "/sys/class/leds/port47_led1:yellow:status\r",
          "transceiverId": 47
        },
        "94": {
          "id": 94,
          "bluePath": "/sys/class/leds/port47_led2:blue:status",
          "yellowPath": "/sys/class/leds/port47_led2:yellow:status\r",
          "transceiverId": 47
        },
        "95": {
          "id": 95,
          "bluePath": "/sys/class/leds/port48_led1:blue:status",
          "yellowPath": "/sys/class/leds/port48_led1:yellow:status\r",
          "transceiverId": 48
        },
        "96": {
          "id": 96,
          "bluePath": "/sys/class/leds/port48_led2:blue:status",
          "yellowPath": "/sys/class/leds/port48_led2:yellow:status\r",
          "transceiverId": 48
        },
        "97": {
          "id": 97,
          "bluePath": "/sys/class/leds/port49_led1:blue:status",
          "yellowPath": "/sys/class/leds/port49_led1:yellow:status\r",
          "transceiverId": 49
        },
        "98": {
          "id": 98,
          "bluePath": "/sys/class/leds/port49_led2:blue:status",
          "yellowPath": "/sys/class/leds/port49_led2:yellow:status\r",
          "transceiverId": 49
        },
        "99": {
          "id": 99,
          "bluePath": "/sys/class/leds/port50_led1:blue:status",
          "yellowPath": "/sys/class/leds/port50_led1:yellow:status\r",
          "transceiverId": 50
        },
        "100": {
          "id": 100,
          "bluePath": "/sys/class/leds/port50_led2:blue:status",
          "yellowPath": "/sys/class/leds/port50_led2:yellow:status\r",
          "transceiverId": 50
        },
        "101": {
          "id": 101,
          "bluePath": "/sys/class/leds/port51_led1:blue:status",
          "yellowPath": "/sys/class/leds/port51_led1:yellow:status\r",
          "transceiverId": 51
        },
        "102": {
          "id": 102,
          "bluePath": "/sys/class/leds/port51_led2:blue:status",
          "yellowPath": "/sys/class/leds/port51_led2:yellow:status\r",
          "transceiverId": 51
        },
        "103": {
          "id": 103,
          "bluePath": "/sys/class/leds/port52_led1:blue:status",
          "yellowPath": "/sys/class/leds/port52_led1:yellow:status\r",
          "transceiverId": 52
        },
        "104": {
          "id": 104,
          "bluePath": "/sys/class/leds/port52_led2:blue:status",
          "yellowPath": "/sys/class/leds/port52_led2:yellow:status\r",
          "transceiverId": 52
        },
        "105": {
          "id": 105,
          "bluePath": "/sys/class/leds/port53_led1:blue:status",
          "yellowPath": "/sys/class/leds/port53_led1:yellow:status\r",
          "transceiverId": 53
        },
        "106": {
          "id": 106,
          "bluePath": "/sys/class/leds/port53_led2:blue:status",
          "yellowPath": "/sys/class/leds/port53_led2:yellow:status\r",
          "transceiverId": 53
        },
        "107": {
          "id": 107,
          "bluePath": "/sys/class/leds/port54_led1:blue:status",
          "yellowPath": "/sys/class/leds/port54_led1:yellow:status\r",
          "transceiverId": 54
        },
        "108": {
          "id": 108,
          "bluePath": "/sys/class/leds/port54_led2:blue:status",
          "yellowPath": "/sys/class/leds/port54_led2:yellow:status\r",
          "transceiverId": 54
        },
        "109": {
          "id": 109,
          "bluePath": "/sys/class/leds/port55_led1:blue:status",
          "yellowPath": "/sys/class/leds/port55_led1:yellow:status\r",
          "transceiverId": 55
        },
        "110": {
          "id": 110,
          "bluePath": "/sys/class/leds/port55_led2:blue:status",
          "yellowPath": "/sys/class/leds/port55_led2:yellow:status\r",
          "transceiverId": 55
        },
        "111": {
          "id": 111,
          "bluePath": "/sys/class/leds/port56_led1:blue:status",
          "yellowPath": "/sys/class/leds/port56_led1:yellow:status\r",
          "transceiverId": 56
        },
        "112": {
          "id": 112,
          "bluePath": "/sys/class/leds/port56_led2:blue:status",
          "yellowPath": "/sys/class/leds/port56_led2:yellow:status\r",
          "transceiverId": 56
        },
        "113": {
          "id": 113,
          "bluePath": "/sys/class/leds/port57_led1:blue:status",
          "yellowPath": "/sys/class/leds/port57_led1:yellow:status\r",
          "transceiverId": 57
        },
        "114": {
          "id": 114,
          "bluePath": "/sys/class/leds/port57_led2:blue:status",
          "yellowPath": "/sys/class/leds/port57_led2:yellow:status\r",
          "transceiverId": 57
        },
        "115": {
          "id": 115,
          "bluePath": "/sys/class/leds/port58_led1:blue:status",
          "yellowPath": "/sys/class/leds/port58_led1:yellow:status\r",
          "transceiverId": 58
        },
        "116": {
          "id": 116,
          "bluePath": "/sys/class/leds/port58_led2:blue:status",
          "yellowPath": "/sys/class/leds/port58_led2:yellow:status\r",
          "transceiverId": 58
        },
        "117": {
          "id": 117,
          "bluePath": "/sys/class/leds/port59_led1:blue:status",
          "yellowPath": "/sys/class/leds/port59_led1:yellow:status\r",
          "transceiverId": 59
        },
        "118": {
          "id": 118,
          "bluePath": "/sys/class/leds/port59_led2:blue:status",
          "yellowPath": "/sys/class/leds/port59_led2:yellow:status\r",
          "transceiverId": 59
        },
        "119": {
          "id": 119,
          "bluePath": "/sys/class/leds/port60_led1:blue:status",
          "yellowPath": "/sys/class/leds/port60_led1:yellow:status\r",
          "transceiverId": 60
        },
        "120": {
          "id": 120,
          "bluePath": "/sys/class/leds/port60_led2:blue:status",
          "yellowPath": "/sys/class/leds/port60_led2:yellow:status\r",
          "transceiverId": 60
        },
        "121": {
          "id": 121,
          "bluePath": "/sys/class/leds/port61_led1:blue:status",
          "yellowPath": "/sys/class/leds/port61_led1:yellow:status\r",
          "transceiverId": 61
        },
        "122": {
          "id": 122,
          "bluePath": "/sys/class/leds/port61_led2:blue:status",
          "yellowPath": "/sys/class/leds/port61_led2:yellow:status\r",
          "transceiverId": 61
        },
        "123": {
          "id": 123,
          "bluePath": "/sys/class/leds/port62_led1:blue:status",
          "yellowPath": "/sys/class/leds/port62_led1:yellow:status\r",
          "transceiverId": 62
        },
        "124": {
          "id": 124,
          "bluePath": "/sys/class/leds/port62_led2:blue:status",
          "yellowPath": "/sys/class/leds/port62_led2:yellow:status\r",
          "transceiverId": 62
        },
        "125": {
          "id": 125,
          "bluePath": "/sys/class/leds/port63_led1:blue:status",
          "yellowPath": "/sys/class/leds/port63_led1:yellow:status\r",
          "transceiverId": 63
        },
        "126": {
          "id": 126,
          "bluePath": "/sys/class/leds/port63_led2:blue:status",
          "yellowPath": "/sys/class/leds/port63_led2:yellow:status\r",
          "transceiverId": 63
        },
        "127": {
          "id": 127,
          "bluePath": "/sys/class/leds/port64_led1:blue:status",
          "yellowPath": "/sys/class/leds/port64_led1:yellow:status\r",
          "transceiverId": 64
        },
        "128": {
          "id": 128,
          "bluePath": "/sys/class/leds/port64_led2:blue:status",
          "yellowPath": "/sys/class/leds/port64_led2:yellow:status",
          "transceiverId": 64
        }
      }
    }
  }
}
)";

static BspPlatformMappingThrift buildGlath05a_64oPlatformMapping(
    const std::string& platformMappingStr) {
  return apache::thrift::SimpleJSONSerializer::deserialize<
      BspPlatformMappingThrift>(platformMappingStr);
}

} // namespace

namespace facebook {
namespace fboss {

Glath05a_64oBspPlatformMapping::Glath05a_64oBspPlatformMapping()
    : BspPlatformMapping(
          buildGlath05a_64oPlatformMapping(kJsonBspPlatformMappingStr)) {}

Glath05a_64oBspPlatformMapping::Glath05a_64oBspPlatformMapping(
    const std::string& platformMappingStr)
    : BspPlatformMapping(buildGlath05a_64oPlatformMapping(platformMappingStr)) {}

} // namespace fboss
} // namespace facebook
