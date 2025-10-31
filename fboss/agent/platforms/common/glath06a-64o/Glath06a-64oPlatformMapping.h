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

class Glath06a_64oPlatformMapping : public PlatformMapping {
 public:
  Glath06a_64oPlatformMapping();
  explicit Glath06a_64oPlatformMapping(const std::string& platformMappingStr);

 private:
  // Forbidden copy constructor and assignment operator
  Glath06a_64oPlatformMapping(Glath06a_64oPlatformMapping const&) = delete;
  Glath06a_64oPlatformMapping& operator=(Glath06a_64oPlatformMapping const&) =
      delete;
};
} // namespace facebook::fboss
