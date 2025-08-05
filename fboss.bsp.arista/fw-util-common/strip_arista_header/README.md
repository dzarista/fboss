# strip_arista_header

**Usage: strip_arista_header input_file(.abit) output_file output_size(in MB)**

This utility strips the Arista-specific header from a provided SPI image (.abit),
producing a .bin image padded with NULL bytes to the given output file size so
that the image may be used with flashrom durin fw_util programming.
