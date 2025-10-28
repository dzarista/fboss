// (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

#pragma once

#include "fboss/lib/bsp/BspPlatformMapping.h"

namespace facebook {
namespace fboss {

class Glath06a_64oBspPlatformMapping : public BspPlatformMapping {
 public:
  Glath06a_64oBspPlatformMapping();
  explicit Glath06a_64oBspPlatformMapping(
      const std::string& platformMappingStr);
};

} // namespace fboss
} // namespace facebook
