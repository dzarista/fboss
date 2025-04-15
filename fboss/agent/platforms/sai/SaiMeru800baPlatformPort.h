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

 #include "fboss/agent/platforms/sai/SaiBcmPlatformPort.h"
 
 namespace facebook::fboss {
 
 class SaiMeru800baPlatformPort : public SaiBcmPlatformPort {
  public:
   SaiMeru800baPlatformPort(PortID id, SaiPlatform* platform)
       : SaiBcmPlatformPort(id, platform) {}
   void linkStatusChanged(bool up, bool adminUp) override;
   void externalState(PortLedExternalState lfs) override;
   uint32_t getCurrentLedState() const override;
   void portChanged(
       std::shared_ptr<Port> /*newPort*/,
       std::shared_ptr<Port> /*oldPort*/) override {}
 
  private:
   uint32_t currentLedState_{0};
 };
 
 } // namespace facebook::fboss
