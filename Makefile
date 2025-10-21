# Default variables
kdir = /kernel-6.4
scratch-dir = /var/FBOSS/tmp_build_dir
sai = $(error Please pass sai version/arch with sai=<sai> Refer to `./build.sh --help` for options)
cmake-target = install
pmapping-dest = $(scratch-dir)
pmapping-src = \
	fboss/agent/platforms/common/meru800bia/Meru800biaPlatformMapping.cpp \
	fboss/agent/platforms/common/meru800bfa/Meru800bfaP2PlatformMapping.h \
	fboss/agent/platforms/common/meru800bfa/Meru800bfaProdPlatformMapping.h \
	fboss/agent/platforms/common/meru800bfa/Meru800bfaP1PlatformMapping.cpp \
	fboss/agent/platforms/common/darwin/DarwinPlatformMapping.cpp \
	fboss/agent/platforms/common/glath05a-64o/Glath05a-64oPlatformMapping.cpp
thrifts = \
   fboss/agent/if/ctrl.thrift \
   fboss/agent/if/hw_ctrl.thrift \
   fboss/qsfp_service/if/qsfp.thrift \
   fboss/platform/fan_service/if/fan_service.thrift \
   fboss/platform/rackmon/if/rackmonsvc.thrift \
   fboss/platform/sensor_service/if/sensor_service.thrift
thrift-targets := $(patsubst %.thrift,thrift-lib/%.thrift,$(thrifts))

.PHONY: fboss extract_platform_mappings bsp_kmods showtech rebuild-all clean

# Default target
all: fboss bsp_kmods showtech psu-upgrade platform_mappings
rebuild-all: clean all
barney_core: fboss thrift-libs
barney_platform: platform_mappings showtech psu-upgrade

fboss:
	@./build.sh --sai $(sai) --scratch-dir $(scratch-dir) --cmake-target $(cmake-target) $(fboss-flags)

bsp_kmods:
	@echo "==== Building bsp-kmods ===="
	$(MAKE) -C $(kdir) M=$(PWD)/fboss.bsp.arista/bsp-kmods modules

showtech:
	@echo "==== Building showtech ===="
	$(MAKE) -C fboss.bsp.arista/showtech

psu-upgrade:
	@echo "==== Building psu-upgrade ===="
	$(MAKE) -C arista/psu-upgrade

thrift-lib/%.thrift: %.thrift
	@echo "==== Generating python thrift libraries for $< ===="
	@$(scratch-dir)/installed/fbthrift/bin/thrift1 -r --gen py -o $(scratch-dir) -I $(PWD) \
	-I $(scratch-dir)/repos/github.com-facebook-fbthrift.git $<

thrift-libs: $(thrift-targets)

platform_mappings:
	@echo "==== Extracting platform mappings ===="
	@arista/build-utils/ExtractMappings.py -d $(pmapping-dest)/PlatformMappings $(pmapping-src)

swtest:
	@arista/core/scripts/run_sw_tests.sh

clean:
	$(MAKE) -C $(kdir) M=$(PWD)/fboss.bsp.arista/bsp-kmods clean
	$(MAKE) -C fboss.bsp.arista/showtech clean
	$(MAKE) -C arista/psu-upgrade clean
	build/fbcode_builder/getdeps.py clean --scratch-path $(scratch-dir)
