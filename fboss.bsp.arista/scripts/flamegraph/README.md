# FlameGraph Profiling for FBOSS

## Prerequisites

### Build FBOSS with Debug Symbols

**IMPORTANT**: To gain clear visibility into function names during profiling, what is being profiled must be built with debug symbols:

```bash
--build-type debug
```

### Install FlameGraph Dependencies

Run the setup script to install required dependencies:

```bash
./setup_flamegraph.sh
```

This installs:
- `perf` - Linux performance monitoring tool
- `perl` and `perl-open` - Required for FlameGraph scripts
- Clones FlameGraph repository to `/opt/FlameGraph`

## Permissions

**IMPORTANT**: `perf` requires elevated privileges to collect performance data.

**Option 1: Run with sudo (recommended for one-time profiling)**
```bash
sudo /path/to/scripts/flamegraph.sh fboss2 show port
```

**Option 2: Grant CAP_PERFMON capability (Linux 5.8+)**
```bash
sudo setcap cap_perfmon=ep /usr/bin/perf
```

**Option 3: Adjust kernel parameter (temporary, less secure)**
```bash
sudo sysctl -w kernel.perf_event_paranoid=-1
```

## Start Profiling

### Profile Command

**Basic usage:**
```bash
# Profile fboss2 commands
/path/to/scripts/flamegraph.sh fboss2 show port
```

**With options:**
```bash
# High-frequency sampling for more detail
/path/to/scripts/flamegraph.sh --freq 999 fboss2 show port

# Custom output directory
/path/to/scripts/flamegraph.sh --output /var/log/flamegraph fboss2 show port

# Custom base name
/path/to/scripts/flamegraph.sh --name port_test fboss2 show port
```

### Profile Running Process (by PID)

**Profile existing process:**
```bash
PID=$(pgrep qsfp_service)

# Profile qsfp_service for 60 seconds (default)
/path/to/scripts/flamegraph.sh --pid $PID

# Profile for 30 seconds
/path/to/scripts/flamegraph.sh --pid $PID --duration 30 --name qsfp_snapshot

# Profile with high frequency
/path/to/scripts/flamegraph.sh --pid $PID --freq 999 --duration 60 --name qsfp_detailed
```

**Getting the generated flamegraph:**
The generated flamegraphs can be found under `/tmp/flamegraph`. The flamegraph is an SVG, to view it, copy the SVG to your local machine and open it in a web browser.

## Understanding FlameGraphs

### Reading FlameGraphs

- **X-axis**: Alphabetical order of function names (NOT time sequence!)
- **Y-axis**: Stack depth (call hierarchy)
- **Width**: Proportion of CPU time spent in that function
- **Color**: Random (for visual differentiation only)

## References

- [FlameGraph GitHub](https://github.com/brendangregg/FlameGraph) - Official FlameGraph repository
- [Brendan Gregg's FlameGraph Guide](http://www.brendangregg.com/flamegraphs.html) - Comprehensive guide
- [Linux perf Examples](http://www.brendangregg.com/perf.html) - perf tool documentation
- [CPU Flame Graphs](http://www.brendangregg.com/FlameGraphs/cpuflamegraphs.html) - CPU profiling guide
