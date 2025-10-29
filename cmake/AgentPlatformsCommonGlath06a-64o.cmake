# CMake to build libraries and binaries in fboss/agent/platforms/common/glath05a-64o

# In general, libraries and binaries in fboss/foo/bar are built by
# cmake/FooBar.cmake

add_library(glath06a-64o_platform_mapping
  fboss/agent/platforms/common/glath06a-64o/Glath06a-64oPlatformMapping.cpp
)

target_link_libraries(glath06a-64o_platform_mapping
  platform_mapping
)
