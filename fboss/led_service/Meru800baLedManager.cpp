// (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

#include "fboss/led_service/Meru800baLedManager.h"
#include "fboss/agent/platforms/common/meru800ba/Meru800baPlatformMapping.h"
#include "fboss/lib/bsp/BspGenericSystemContainer.h"
#include "fboss/lib/bsp/meru800ba/Meru800baBspPlatformMapping.h"

namespace facebook::fboss {

/*
 * Meru800baLedManager ctor()
 *
 * Meru800baLedManager constructor will create the LedManager object for
 * Meru800ba platform
 */
Meru800baLedManager::Meru800baLedManager() : BspLedManager() {
  init<Meru800baBspPlatformMapping, Meru800baPlatformMapping>();
  XLOG(INFO) << "Created Meru800ba BSP LED Manager";
}

} // namespace facebook::fboss
