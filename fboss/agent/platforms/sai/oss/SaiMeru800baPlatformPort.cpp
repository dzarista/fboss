/*
 *  Copyright (c) 2004-present, Facebook, Inc.
 *  All rights reserved.
 *
 *  This source code is licensed under the BSD-style license found in the
 *  LICENSE file in the root directory of this source tree. An additional grant
 *  of patent rights can be found in the PATENTS file in the same directory.
 *
 */
 #include "fboss/agent/platforms/sai/SaiMeru800baPlatformPort.h"

 namespace facebook::fboss {
 
 void SaiMeru800baPlatformPort::linkStatusChanged(
     bool /* up */,
     bool /* adminUp */) {}
 
 void SaiMeru800baPlatformPort::externalState(PortLedExternalState /* lfs */) {}
 
 uint32_t SaiMeru800baPlatformPort::getCurrentLedState() const {
   return static_cast<uint32_t>(currentLedState_);
 }
 
 } // namespace facebook::fboss
 