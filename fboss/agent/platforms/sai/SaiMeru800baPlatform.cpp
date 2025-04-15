/*
 *  Copyright (c) 2004-present, Facebook, Inc.
 *  All rights reserved.
 *
 *  This source code is licensed under the BSD-style license found in the
 *  LICENSE file in the root directory of this source tree. An additional grant
 *  of patent rights can be found in the PATENTS file in the same directory.
 *
 */

#include "fboss/agent/platforms/sai/SaiMeru800baPlatform.h"

#include "fboss/agent/hw/switch_asics/Tomahawk5Asic.h"
#include "fboss/agent/platforms/common/meru800ba/Meru800baPlatformMapping.h"

#include <cstdio>
#include <cstring>
namespace facebook::fboss {

SaiMeru800baPlatform::SaiMeru800baPlatform(
    std::unique_ptr<PlatformProductInfo> productInfo,
    folly::MacAddress localMac,
    const std::string& platformMappingStr)
    : SaiBcmPlatform(
          std::move(productInfo),
          platformMappingStr.empty()
              ? std::make_unique<Meru800baPlatformMapping>()
              : std::make_unique<Meru800baPlatformMapping>(platformMappingStr),
          localMac) {}

void SaiMeru800baPlatform::setupAsic(
    std::optional<int64_t> switchId,
    const cfg::SwitchInfo& switchInfo,
    std::optional<HwAsic::FabricNodeRole> fabricNodeRole) {
  CHECK(!fabricNodeRole.has_value());
  asic_ = std::make_unique<Tomahawk5Asic>(switchId, switchInfo);
}

HwAsic* SaiMeru800baPlatform::getAsic() const {
  return asic_.get();
}

SaiMeru800baPlatform::~SaiMeru800baPlatform() = default;

} // namespace facebook::fboss
