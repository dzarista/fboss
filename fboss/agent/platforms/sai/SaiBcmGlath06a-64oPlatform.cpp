/*
 *  Copyright (c) 2004-present, Facebook, Inc.
 *  All rights reserved.
 *
 *  This source code is licensed under the BSD-style license found in the
 *  LICENSE file in the root directory of this source tree. An additional grant
 *  of patent rights can be found in the PATENTS file in the same directory.
 *
 */

#include "fboss/agent/platforms/sai/SaiBcmGlath06a-64oPlatform.h"

#include "fboss/agent/hw/switch_asics/Tomahawk6Asic.h"
#include "fboss/agent/platforms/common/glath06a-64o/Glath06a-64oPlatformMapping.h"

#include <cstring>
namespace facebook::fboss {

SaiBcmGlath06a_64oPlatform::SaiBcmGlath06a_64oPlatform(
    std::unique_ptr<PlatformProductInfo> productInfo,
    folly::MacAddress localMac,
    const std::string& platformMappingStr)
    : SaiBcmPlatform(
          std::move(productInfo),
          platformMappingStr.empty()
              ? std::make_unique<Glath06a_64oPlatformMapping>()
              : std::make_unique<Glath06a_64oPlatformMapping>(
                    platformMappingStr),
          localMac) {}

void SaiBcmGlath06a_64oPlatform::setupAsic(
    std::optional<int64_t> switchId,
    const cfg::SwitchInfo& switchInfo,
    std::optional<HwAsic::FabricNodeRole> fabricNodeRole) {
  CHECK(!fabricNodeRole.has_value());
  asic_ = std::make_unique<Tomahawk6Asic>(switchId, switchInfo);
}

HwAsic* SaiBcmGlath06a_64oPlatform::getAsic() const {
  return asic_.get();
}

SaiBcmGlath06a_64oPlatform::~SaiBcmGlath06a_64oPlatform() = default;

} // namespace facebook::fboss
