// (c) Meta Platforms, Inc. and affiliates. Confidential and proprietary.

#pragma once

#include "fboss/lib/bsp/BspPlatformMapping.h"

namespace facebook {
namespace fboss {

class Meru800baBspPlatformMapping : public BspPlatformMapping {
 public:
  Meru800baBspPlatformMapping();
  explicit Meru800baBspPlatformMapping(const std::string& platformMappingStr);
};

} // namespace fboss
} // namespace facebook
