# CMake to build libraries and binaries in fboss/agent/platforms/common/meru800ba

# In general, libraries and binaries in fboss/foo/bar are built by
# cmake/FooBar.cmake

add_library(meru800ba_platform_mapping
  fboss/agent/platforms/common/meru800ba/Meru800baPlatformMapping.cpp
)

target_link_libraries(meru800ba_platform_mapping
  platform_mapping
)
