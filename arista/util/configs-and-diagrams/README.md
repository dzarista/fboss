# FBOSS Platform Configuration Tools

Python tools for generating FBOSS platform configurations and L1 vendor mappings.

## Tools

- **Configuration Generator**: General platform configs (Platform manager, sensor service, BSP, fan/LED configs) & diagrams
  📖 [Documentation](docs/configs_generator.md)

- **Vendor Mapping Generator**: L1 static mappings, SI settings, port profiles
  📖 [Documentation](docs/vendor_mapping_generator.md)

## Usage

```bash
# Generate all configs for a platform (not including l1 vendor mappings)
python3 generate.py --update_all_configs

# Generate specific config type
python3 generate.py --platform <PlatformName> --output <config-type>

# Generate vendor mappings
python3 generate.py --platform <PlatformName> --output vendor-mappings
```

See detailed documentation in `docs/` for complete instructions.