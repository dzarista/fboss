/*
 *  Copyright (c) 2004-present, Facebook, Inc.
 *  All rights reserved.
 *
 *  This source code is licensed under the BSD-style license found in the
 *  LICENSE file in the root directory of this source tree. An additional grant
 *  of patent rights can be found in the PATENTS file in the same directory.
 *
 */
#pragma once

#include "fboss/agent/platforms/common/PlatformMapping.h"

namespace facebook::fboss {

class Meru800baPlatformMapping : public PlatformMapping {
 public:
  Meru800baPlatformMapping();
  explicit Meru800baPlatformMapping(const std::string& platformMappingStr);

 private:
  // Forbidden copy constructor and assignment operator
  Meru800baPlatformMapping(Meru800baPlatformMapping const&) = delete;
  Meru800baPlatformMapping& operator=(Meru800baPlatformMapping const&) = delete;
};
} // namespace facebook::fboss
