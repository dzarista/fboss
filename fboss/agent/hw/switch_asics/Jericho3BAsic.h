// Copyright 2004-present Facebook. All Rights Reserved.

#pragma once

#include "fboss/agent/hw/switch_asics/Jericho3Asic.h"

namespace facebook::fboss {

class Jericho3BAsic : public Jericho3Asic {
 public:
  Jericho3BAsic(
      cfg::SwitchType type,
      std::optional<int64_t> id,
      int16_t index,
      std::optional<cfg::Range64> systemPortRange,
      const folly::MacAddress& mac,
      std::optional<cfg::SdkVersion> sdkVersion = std::nullopt)
      : Jericho3Asic(type, id, index, systemPortRange, mac, sdkVersion) {}

  cfg::AsicType getAsicType() const override {
    return cfg::AsicType::ASIC_TYPE_JERICHO3B;
  }
};

} // namespace facebook::fboss
