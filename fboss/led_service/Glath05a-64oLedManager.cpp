// (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

#include "fboss/led_service/Glath05a-64oLedManager.h"
#include "fboss/agent/platforms/common/glath05a-64o/Glath05a-64oPlatformMapping.h"
#include "fboss/lib/bsp/BspGenericSystemContainer.h"
#include "fboss/lib/bsp/glath05a-64o/Glath05a-64oBspPlatformMapping.h"

namespace facebook::fboss {

/*
 * Glath05a-64oLedManager ctor()
 *
 * Glath05a-64oLedManager constructor will create the LedManager object for
 * Glath05a-64o platform
 */
Glath05a-64oLedManager::Glath05a-64oLedManager() : BspLedManager() {
  init<Glath05a-64oBspPlatformMapping, Glath05a-64oPlatformMapping>();
  XLOG(INFO) << "Created Glath05a-64o BSP LED Manager";
}

} // namespace facebook::fboss
