config-generator.py
-------------------

Generates json config for FBOSS.

Sample usage:

```
./config-generator.py dsf302 -s wlr101 -l vpr107 vpr108
```

This creates a directory called dsf302 and generates
- dsf302/wlr101.conf
- dsf302/vpr107.conf
- dsf302/vpr108.conf

Based on the specification above, it assumes a 1 spine, 2 leaf cluster.

The script also has the `--copy` option to copy the cluster configs to /tmp. `ssh-keygen` + `ssh-copy-id` makes the workflow easier.
