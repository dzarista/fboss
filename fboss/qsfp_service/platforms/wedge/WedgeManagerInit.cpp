/*
 *  Copyright (c) 2004-present, Facebook, Inc.
 *  All rights reserved.
 *
 *  This source code is licensed under the BSD-style license found in the
 *  LICENSE file in the root directory of this source tree. An additional grant
 *  of patent rights can be found in the PATENTS file in the same directory.
 *
 */
#include "fboss/qsfp_service/platforms/wedge/WedgeManagerInit.h"

<<<<<<< srv-fboss-arista-robot.upstream_copy_06-25-2025
#include "fboss/agent/platforms/common/PlatformMappingUtils.h"
=======
#include "fboss/agent/platforms/common/janga800bic/Janga800bicPlatformMapping.h"
#include "fboss/agent/platforms/common/meru400bfu/Meru400bfuPlatformMapping.h"
#include "fboss/agent/platforms/common/meru400bia/Meru400biaPlatformMapping.h"
#include "fboss/agent/platforms/common/meru400biu/Meru400biuPlatformMapping.h"
#include "fboss/agent/platforms/common/meru800bfa/Meru800bfaPlatformMapping.h"
#include "fboss/agent/platforms/common/meru800bia/Meru800biaPlatformMapping.h"
#include "fboss/agent/platforms/common/minipack3n/Minipack3NPlatformMapping.h"
#include "fboss/agent/platforms/common/montblanc/MontblancPlatformMapping.h"
#include "fboss/agent/platforms/common/morgan800cc/Morgan800ccPlatformMapping.h"
#include "fboss/agent/platforms/common/tahan800bc/Tahan800bcPlatformMapping.h"
#include "fboss/agent/platforms/common/darwin/DarwinPlatformMapping.h"
#include "fboss/agent/platforms/common/glath05a-64o/Glath05a-64oPlatformMapping.h"
>>>>>>> main
#include "fboss/lib/bsp/BspGenericSystemContainer.h"
#include "fboss/lib/bsp/janga800bic/Janga800bicBspPlatformMapping.h"
#include "fboss/lib/bsp/meru400bfu/Meru400bfuBspPlatformMapping.h"
#include "fboss/lib/bsp/meru400bia/Meru400biaBspPlatformMapping.h"
#include "fboss/lib/bsp/meru400biu/Meru400biuBspPlatformMapping.h"
#include "fboss/lib/bsp/meru800bfa/Meru800bfaBspPlatformMapping.h"
#include "fboss/lib/bsp/meru800bia/Meru800biaBspPlatformMapping.h"
#include "fboss/lib/bsp/minipack3n/Minipack3NBspPlatformMapping.h"
#include "fboss/lib/bsp/montblanc/MontblancBspPlatformMapping.h"
#include "fboss/lib/bsp/morgan800cc/Morgan800ccBspPlatformMapping.h"
#include "fboss/lib/bsp/tahan800bc/Tahan800bcBspPlatformMapping.h"
#include "fboss/lib/bsp/darwin/DarwinBspPlatformMapping.h"
#include "fboss/lib/bsp/glath05a-64o/Glath05a-64oBspPlatformMapping.h"
#include "fboss/lib/platforms/PlatformProductInfo.h"
#include "fboss/qsfp_service/platforms/wedge/BspWedgeManager.h"
#include "fboss/qsfp_service/platforms/wedge/GalaxyManager.h"
#include "fboss/qsfp_service/platforms/wedge/Wedge100Manager.h"
#include "fboss/qsfp_service/platforms/wedge/Wedge400CManager.h"
#include "fboss/qsfp_service/platforms/wedge/Wedge40Manager.h"

#include "fboss/lib/CommonFileUtils.h"

namespace facebook::fboss {

std::unique_ptr<WedgeManager> createWedgeManager() {
  auto productInfo =
      std::make_unique<PlatformProductInfo>(FLAGS_fruid_filepath);
  productInfo->initialize();
  auto mode = productInfo->getType();

  // Only used for platform mapping overrides.
  std::string platformMappingStr;
  if (!FLAGS_platform_mapping_override_path.empty()) {
    if (!folly::readFile(
            FLAGS_platform_mapping_override_path.data(), platformMappingStr)) {
      throw FbossError("unable to read ", FLAGS_platform_mapping_override_path);
    }
    XLOG(INFO) << "Overriding platform mapping from "
               << FLAGS_platform_mapping_override_path;
  }

<<<<<<< srv-fboss-arista-robot.upstream_copy_06-25-2025
  std::shared_ptr<const PlatformMapping> platformMapping =
      utility::initPlatformMapping(mode);
=======
  createDir(FLAGS_qsfp_service_volatile_dir);
  if (mode == PlatformType::PLATFORM_WEDGE100) {
    return std::make_unique<Wedge100Manager>(platformMappingStr);
  } else if (
      mode == PlatformType::PLATFORM_GALAXY_LC ||
      mode == PlatformType::PLATFORM_GALAXY_FC) {
    return std::make_unique<GalaxyManager>(mode, platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_YAMP) {
    return createYampWedgeManager(platformMappingStr);
  } else if (
      mode == PlatformType::PLATFORM_DARWIN ||
      mode == PlatformType::PLATFORM_DARWIN48V) {
    return createDarwinWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_ELBERT) {
    return createElbertWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_MERU400BFU) {
    return createMeru400bfuWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_MERU400BIA) {
    return createMeru400biaWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_MERU400BIU) {
    return createMeru400biuWedgeManager(platformMappingStr);
  } else if (
      mode == PlatformType::PLATFORM_MERU800BIA ||
      mode == PlatformType::PLATFORM_MERU800BIAB) {
    return createMeru800biaWedgeManager(platformMappingStr);
  } else if (
      mode == PlatformType::PLATFORM_MERU800BFA ||
      mode == PlatformType::PLATFORM_MERU800BFA_P1) {
    return createMeru800bfaWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_MONTBLANC) {
    return createMontblancWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_MINIPACK3N) {
    return createMinipack3NWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_MORGAN800CC) {
    return createMorgan800ccWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_WEDGE400C) {
    return std::make_unique<Wedge400CManager>(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_JANGA800BIC) {
    return createJanga800bicWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_TAHAN800BC) {
    return createTahan800bcWedgeManager(platformMappingStr);
  } else if (mode == PlatformType::PLATFORM_GLATH05A_64O) {
    return createGlath05a_64oWedgeManager(platformMappingStr);
  } else if (
      mode == PlatformType::PLATFORM_FUJI ||
      mode == PlatformType::PLATFORM_MINIPACK ||
      mode == PlatformType::PLATFORM_WEDGE400) {
    return createFBWedgeManager(std::move(productInfo), platformMappingStr);
  }
  return std::make_unique<Wedge40Manager>(platformMappingStr);
}

std::unique_ptr<WedgeManager> createDarwinWedgeManager(
    const std::string& platformMappingStr) {
  auto systemContainer =
      BspGenericSystemContainer<DarwinBspPlatformMapping>::getInstance()
          .get();
  return std::make_unique<BspWedgeManager>(
      systemContainer,
      std::make_unique<BspTransceiverApi>(systemContainer),
      platformMappingStr.empty()
          ? std::make_unique<DarwinPlatformMapping>()
          : std::make_unique<DarwinPlatformMapping>(platformMappingStr),
      PlatformType::PLATFORM_DARWIN);
}

std::unique_ptr<WedgeManager> createGlath05a_64oWedgeManager(
  const std::string& platformMappingStr) {
auto systemContainer =
    BspGenericSystemContainer<Glath05a_64oBspPlatformMapping>::getInstance()
        .get();
return std::make_unique<BspWedgeManager>(
    systemContainer,
    std::make_unique<BspTransceiverApi>(systemContainer),
    platformMappingStr.empty()
        ? std::make_unique<Glath05a_64oPlatformMapping>()
        : std::make_unique<Glath05a_64oPlatformMapping>(platformMappingStr),
    PlatformType::PLATFORM_GLATH05A_64O);
}

std::unique_ptr<WedgeManager> createMeru400bfuWedgeManager(
    const std::string& platformMappingStr) {
  auto systemContainer =
      BspGenericSystemContainer<Meru400bfuBspPlatformMapping>::getInstance()
          .get();
  return std::make_unique<BspWedgeManager>(
      systemContainer,
      std::make_unique<BspTransceiverApi>(systemContainer),
      platformMappingStr.empty()
          ? std::make_unique<Meru400bfuPlatformMapping>()
          : std::make_unique<Meru400bfuPlatformMapping>(platformMappingStr),
      PlatformType::PLATFORM_MERU400BFU);
}
>>>>>>> main

  const auto threads =
      std::make_shared<std::unordered_map<TransceiverID, SlotThreadHelper>>();
  for (const auto& tcvrID :
       utility::getTransceiverIds(platformMapping->getChips())) {
    threads->emplace(tcvrID, SlotThreadHelper(tcvrID));
  }

  createDir(FLAGS_qsfp_service_volatile_dir);
  switch (mode) {
    case PlatformType::PLATFORM_WEDGE100:
      return std::make_unique<Wedge100Manager>(platformMapping, threads);
    case PlatformType::PLATFORM_GALAXY_LC:
    case PlatformType::PLATFORM_GALAXY_FC:
      return std::make_unique<GalaxyManager>(mode, platformMapping, threads);
    case PlatformType::PLATFORM_YAMP:
      return createYampWedgeManager(platformMapping, threads);
    case PlatformType::PLATFORM_DARWIN:
    case PlatformType::PLATFORM_DARWIN48V:
      return createDarwinWedgeManager(platformMapping, threads);
    case PlatformType::PLATFORM_ELBERT:
      return createElbertWedgeManager(platformMapping, threads);
    case PlatformType::PLATFORM_MERU400BFU:
      return createBspWedgeManager<
          Meru400bfuBspPlatformMapping,
          PlatformType::PLATFORM_MERU400BFU>(platformMapping, threads);
    case PlatformType::PLATFORM_MERU400BIA:
      return createBspWedgeManager<
          Meru400biaBspPlatformMapping,
          PlatformType::PLATFORM_MERU400BIA>(platformMapping, threads);
    case PlatformType::PLATFORM_MERU400BIU:
      return createBspWedgeManager<
          Meru400biuBspPlatformMapping,
          PlatformType::PLATFORM_MERU400BIU>(platformMapping, threads);
    case PlatformType::PLATFORM_MERU800BIA:
    case PlatformType::PLATFORM_MERU800BIAB:
      return createBspWedgeManager<
          Meru800biaBspPlatformMapping,
          PlatformType::PLATFORM_MERU800BIA>(platformMapping, threads);
    case PlatformType::PLATFORM_MERU800BFA:
    case PlatformType::PLATFORM_MERU800BFA_P1:
      return createBspWedgeManager<
          Meru800bfaBspPlatformMapping,
          PlatformType::PLATFORM_MERU800BFA>(platformMapping, threads);
    case PlatformType::PLATFORM_MONTBLANC:
      return createBspWedgeManager<
          MontblancBspPlatformMapping,
          PlatformType::PLATFORM_MONTBLANC>(platformMapping, threads);
    case PlatformType::PLATFORM_MINIPACK3N:
      return createBspWedgeManager<
          Minipack3NBspPlatformMapping,
          PlatformType::PLATFORM_MINIPACK3N>(platformMapping, threads);
    case PlatformType::PLATFORM_MORGAN800CC:
      return createBspWedgeManager<
          Morgan800ccBspPlatformMapping,
          PlatformType::PLATFORM_MORGAN800CC>(platformMapping, threads);
    case PlatformType::PLATFORM_WEDGE400C:
      return std::make_unique<Wedge400CManager>(platformMapping, threads);
    case PlatformType::PLATFORM_JANGA800BIC:
      return createBspWedgeManager<
          Janga800bicBspPlatformMapping,
          PlatformType::PLATFORM_JANGA800BIC>(platformMapping, threads);
    case PlatformType::PLATFORM_TAHAN800BC:
      return createBspWedgeManager<
          Tahan800bcBspPlatformMapping,
          PlatformType::PLATFORM_TAHAN800BC>(platformMapping, threads);
    case PlatformType::PLATFORM_FUJI:
    case PlatformType::PLATFORM_MINIPACK:
    case PlatformType::PLATFORM_WEDGE400:
      return createFBWedgeManager(
          std::move(productInfo), platformMapping, threads);
    default:
      return std::make_unique<Wedge40Manager>(platformMapping, threads);
  }
}

template <typename BspPlatformMapping, PlatformType platformType>
std::unique_ptr<WedgeManager> createBspWedgeManager(
    const std::shared_ptr<const PlatformMapping> platformMapping,
    const std::shared_ptr<std::unordered_map<TransceiverID, SlotThreadHelper>>
        threads) {
  auto systemContainer =
      BspGenericSystemContainer<BspPlatformMapping>::getInstance().get();
  return std::make_unique<BspWedgeManager>(
      systemContainer,
      std::make_unique<BspTransceiverApi>(systemContainer),
      platformMapping,
      platformType,
      threads);
}

} // namespace facebook::fboss
