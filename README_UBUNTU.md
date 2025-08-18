# DANKSHARDING BLOCKCHAIN SIMULATION - UBUNTU DEPLOYMENT

## Quick Setup on Ubuntu Server

### 1. Clone and Setup
```bash
git clone <your-repo-url> blockchain_simulator_framework
cd blockchain_simulator_framework

# Make scripts executable
chmod +x *.sh
chmod +x *.py
```

### 2. Install Dependencies
```bash
# Install Python dependencies
pip3 install simpy numpy

# Install tmux for parallel experiments
sudo apt-get update
sudo apt-get install tmux
```

### 2.5. Hardware Optimization (RECOMMENDED)
```bash
# Automatically detect your hardware and optimize parallel settings
./auto_configure_hardware.sh

# Or manually configure for specific hardware:
# ./configure_machine1.sh  # For 16-64 core servers (Xeon Silver class)
# ./configure_machine2.sh  # For 200+ core servers (Xeon Platinum class)
```

**Hardware Performance Guide:**
- **16-32 cores**: ~16 parallel jobs, 4-8 hours for 95 experiments
- **64-128 cores**: ~32 parallel jobs, 2-4 hours for 95 experiments  
- **200+ cores**: ~80 parallel jobs, 1-2 hours for 95 experiments
- **384 cores** (Xeon Platinum): ~80 parallel jobs, ~1.5 hours (!)

### 3. Quick Validation (RECOMMENDED FIRST!)
```bash
# Test that everything works before running expensive experiments
./quick_validation.sh
```

### 4. Run Full Experiment Suite (PARALLEL)
```bash
# Launch ALL experiments in parallel tmux sessions
./run_danksharding_experiments.sh
```

**Parallel Execution Features:**
- **12 experiments run simultaneously** (configurable based on your server)
- **Automatic resource management** - waits for slots when max reached
- **System monitoring** - tracks CPU, memory, disk usage
- **Progressive launching** - 5-second delays between launches to prevent overload

### 5. Monitor Parallel Progress
```bash
# Quick status check
./manage_experiments.sh status

# Continuous monitoring (auto-refresh every 30s)
./manage_experiments.sh monitor

# List active experiment sessions
./manage_experiments.sh list

# Attach to specific experiment
./manage_experiments.sh attach danksharding_btc_shards8_txopt70

# View recent logs
./manage_experiments.sh logs btc_shards8_txopt70

# System resource usage
./manage_experiments.sh resources
```

### 6. Emergency Management
```bash
# Kill all experiments (if needed)
./manage_experiments.sh kill-all

# Clean up completed sessions
./manage_experiments.sh cleanup
```

### 7. Generate Results
```bash
# After experiments complete, generate comparison CSV
python3 generate_comparison_csv.py danksharding_results/experiment_*

# Find fastest configurations
grep "TPS" danksharding_results/summary_all_chains.csv | sort -t',' -k4 -nr | head -10

# Compare with baseline
cat danksharding_results/baseline_comparison.csv
```

### Performance Benefits Summary
- **4.15x faster blockchain processing** (525s vs 2183s simulation time)
- **Parallel execution scaling**:
  - **Xeon Silver (32 cores)**: 95 experiments in ~6-8 hours (16 parallel)
  - **Xeon Platinum (384 cores)**: 95 experiments in ~1.5-2 hours (80 parallel)
- **Auto-optimization**: Hardware detection and optimal parallel configuration
- **Resource management**: Smart CPU/RAM utilization with safety monitoring
- **Cross-chain testing**: 5 different blockchain configurations with authentic parameters

## Experiment Configuration

The script tests:
- **Chains**: BTC, BCH, LTC, DOGE, MEMO (each with chain-specific parameters)
- **Shard configurations**: 1, 4, 8, 16, 32, 64
- **Transaction optimization**: 50%, 70%, 90%
- **Node count**: 1000 (configurable in script)

Total experiments: **5 chains × 6 shard configs × 3 optimization levels = 90 Danksharding experiments + 5 baseline = 95 total**

### Chain-Specific Parameters
- **Bitcoin (BTC)**: 50 BTC reward, 600s blocks, 4KB blocks
- **Bitcoin Cash (BCH)**: 12.5 BCH reward, 600s blocks, 128KB blocks  
- **Litecoin (LTC)**: 50 LTC reward, 150s blocks, 4KB blocks
- **Dogecoin (DOGE)**: 10K DOGE reward, 60s blocks, 4KB blocks
- **MemoCoin (MEMO)**: 51.85 MEMO reward, 3.27s blocks, 32KB blocks

## Results Structure
```
danksharding_results/
├── experiment_YYYYMMDD_HHMMSS/
│   ├── raw_outputs/           # Individual experiment logs
│   ├── csv_results/           # Processed CSV data
│   ├── comprehensive_results.csv
│   ├── comprehensive_results_summary.csv
│   ├── check_experiments.sh
│   ├── run_analysis.sh
│   └── analyze_results.py
```

## Key Files for Research

- `comprehensive_results_summary.csv` - Main results for paper
- `DANKSHARDING_READINESS_REPORT.md` - Performance validation report
- Individual experiment logs in `raw_outputs/`

## Expected Performance

Based on validation testing:
- **Baseline**: ~150 TPS
- **Danksharding**: ~600+ TPS (4x improvement)
- **Best configuration**: 8-16 shards typically optimal

## Troubleshooting

### If experiments fail:
1. Check `quick_validation.sh` output
2. Verify dependencies: `python3 -c "import simpy; print('OK')"`
3. Check disk space: `df -h`
4. Review logs in `raw_outputs/`

### If running slow:
- Normal for 1000-node simulations
- Monitor CPU/memory: `htop`
- Consider reducing nodes in script for testing

## Research Paper Data

The generated CSV files provide:
- TPS comparisons vs baseline
- Scalability analysis across shard counts
- Performance vs teammate's "multiple winners" approach
- Comprehensive metrics for IEEE/ACM submission

## Contact

- Issues with Danksharding implementation
- Questions about experiment configuration
- Results interpretation

---
**Status**: ✅ Ready for production experiments
**Target Performance**: 4x improvement over baseline
**Estimated Runtime**: 2-8 hours per experiment (depending on server)
