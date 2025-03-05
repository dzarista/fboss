## Instructions

This tool is a wrapper around the bspMapping genration tool located under `fboss/lib/bsp/bspmapping`.

Prior to using this tool, ensure that you have added the csv file representation of the mapping under `fboss/lib/bsp/bspmapping/input` and add references to `Main.cpp` and `Parser.h`. A new fboss build is required after adding those changes.

To use the tool, run the following under the arista directory.
```shell
$ ./fbossctl bsp_mapping_gen
```

This will write the configs for each platform to `tmp/generated_configs`. You will need to copy and paste the generated JSON configuration from those files to the C++ files located in `fboss/lib/bsp/`. The subdirectory names for each platform should match the JSON files, see reference below:

| JSON File Name                     | C++ File Location                                           |
|------------------------------------|-------------------------------------------------------------|
| generated_configs/janga800bic.json | fboss/lib/bsp/janga800bic/Janga800bicBspPlatformMapping.cpp |
| generated_configs/meru400bfu.json  | fboss/lib/bsp/meru400bfu/Meru400bfuBspPlatformMapping.cpp   |
| generated_configs/meru400biu.json  | fboss/lib/bsp/meru400biu/Meru400biuBspPlatformMapping.cpp   |
| generated_configs/meru800bfa.json  | fboss/lib/bsp/meru800bfa/Meru800bfaBspPlatformMapping.cpp   |
| generated_configs/meru800bia.json  | fboss/lib/bsp/meru800bia/Meru800biaBspPlatformMapping.cpp   |
| generated_configs/montblanc.json   | fboss/lib/bsp/montblanc/MontblancBspPlatformMapping.cpp     |
| generated_configs/morgan800cc.json | fboss/lib/bsp/morgan800cc/Morgan800ccBspPlatformMapping.cpp |
| generated_configs/tahan800bc.json  | fboss/lib/bsp/tahan800bc/Tahan800bcBspPlatformMapping.cpp   |
