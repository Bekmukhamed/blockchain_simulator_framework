#!/bin/bash

# Configuration
EXPERIMENT_DIR="danksharding_experiments"
RESULTS_DIR="danksharding_results"
BASE_DIR="$(pwd)"

# Create directories
mkdir -p $EXPERIMENT_DIR $RESULTS_DIR

echo "Setting up Danksharding experiments"
echo "============================================================"

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "Error: tmux is required for parallel execution"
    echo "Install with: sudo apt install tmux  (or brew install tmux on macOS)"
    exit 1
fi

# Generate all experiment scripts
echo "Generating experiment scripts..."

# 1. Danksharding vs Baseline Comparison
cat > $EXPERIMENT_DIR/run_danksharding_comparison.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
RESULTS_DIR="danksharding_results/comparison"
mkdir -p $RESULTS_DIR

echo "Starting Danksharding vs Baseline Comparison..."
echo "==============================================="

CHAINS=("btc" "bch" "ltc" "doge" "memo")
NODES=(1000 2500 5000)
SHARD_CONFIGS=(1 4 8 16 32)
RUNS=3

for chain in "${CHAINS[@]}"; do
    for nodes in "${NODES[@]}"; do
        for run in $(seq 1 $RUNS); do
            echo "Run $run/$RUNS: $chain baseline with $nodes nodes"

            # Baseline (no Danksharding)
            python3 sim-blockchain.py \
                --chain $chain \
                --nodes $nodes --neighbors $((nodes/4)) \
                --miners $nodes --hashrate 1e6 \
                --wallets 1000 --transactions 500 --interval 0.01 \
                --print 50 \
                > $RESULTS_DIR/baseline_${chain}_${nodes}nodes_run${run}.log 2>&1

            echo "Completed baseline: $chain $nodes nodes run $run"
        done

        # Danksharding tests with different shard configurations
        for shards in "${SHARD_CONFIGS[@]}"; do
            for run in $(seq 1 $RUNS); do
                echo "Run $run/$RUNS: $chain Danksharding ($shards shards) with $nodes nodes"

                python3 sim-blockchain.py \
                    --chain $chain \
                    --nodes $nodes --neighbors $((nodes/4)) \
                    --miners $nodes --hashrate 1e6 \
                    --wallets 1000 --transactions 500 --interval 0.01 \
                    --print 50 \
                    --danksharding --parallel-shards $shards --tx-optimization 0.8 \
                    > $RESULTS_DIR/danksharding_${chain}_${nodes}nodes_${shards}shards_run${run}.log 2>&1

                echo "Completed Danksharding: $chain $nodes nodes $shards shards run $run"
            done
        done
    done
done

echo "Danksharding comparison tests completed. Results in $RESULTS_DIR"
EOF

# 3. Cross-Chain Danksharding Performance
cat > $EXPERIMENT_DIR/run_chain_btc_tests.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
RESULTS_DIR="danksharding_results/chains"
mkdir -p $RESULTS_DIR

echo "Starting BTC Chain Danksharding Tests..."
echo "========================================"

NODES=(1000 2500 5000)
SHARD_CONFIGS=(1 4 8 16 32)
TX_OPTIMIZATIONS=(0.5 0.7 0.9)
RUNS=3

for nodes in "${NODES[@]}"; do
    for shards in "${SHARD_CONFIGS[@]}"; do
        for opt in "${TX_OPTIMIZATIONS[@]}"; do
            for run in $(seq 1 $RUNS); do
                echo "Run $run/$RUNS: BTC $nodes nodes, $shards shards, optimization $opt"

                python3 sim-blockchain.py \
                    --chain btc \
                    --nodes $nodes --neighbors $((nodes/4)) \
                    --miners $nodes --hashrate 1e6 \
                    --wallets 1000 --transactions 500 --interval 0.01 \
                    --print 50 \
                    --danksharding --parallel-shards $shards --tx-optimization $opt \
                    > $RESULTS_DIR/btc_${nodes}nodes_${shards}shards_opt${opt}_run${run}.log 2>&1

                echo "Completed: BTC $nodes nodes $shards shards optimization $opt run $run"
            done
        done
    done
done

echo "BTC chain tests completed. Results in $RESULTS_DIR"
EOF

cat > $EXPERIMENT_DIR/run_chain_eth_tests.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
RESULTS_DIR="danksharding_results/chains"
mkdir -p $RESULTS_DIR

echo "Starting ETH-style Chain Tests (BCH, LTC, DOGE, MEMO)..."
echo "======================================================"

CHAINS=("bch" "ltc" "doge" "memo")
NODES=(1000 2500 5000)
SHARD_CONFIGS=(4 8 16)
TX_OPTIMIZATIONS=(0.7 0.9)
RUNS=3

for chain in "${CHAINS[@]}"; do
    for nodes in "${NODES[@]}"; do
        for shards in "${SHARD_CONFIGS[@]}"; do
            for opt in "${TX_OPTIMIZATIONS[@]}"; do
                for run in $(seq 1 $RUNS); do
                    echo "Run $run/$RUNS: $chain $nodes nodes, $shards shards, optimization $opt"

                    python3 sim-blockchain.py \
                        --chain $chain \
                        --nodes $nodes --neighbors $((nodes/4)) \
                        --miners $nodes --hashrate 1e6 \
                        --wallets 1000 --transactions 500 --interval 0.01 \
                        --print 50 \
                        --danksharding --parallel-shards $shards --tx-optimization $opt \
                        > $RESULTS_DIR/${chain}_${nodes}nodes_${shards}shards_opt${opt}_run${run}.log 2>&1

                    echo "Completed: $chain $nodes nodes $shards shards optimization $opt run $run"
                done
            done
        done
    done
done

echo "ETH-style chain tests completed. Results in $RESULTS_DIR"
EOF
cat > $EXPERIMENT_DIR/run_crosschain_danksharding.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
RESULTS_DIR="danksharding_results/crosschain"
mkdir -p $RESULTS_DIR

echo "Starting Cross-Chain Danksharding Performance Tests..."
echo "====================================================="

CHAINS=("btc" "bch" "ltc" "doge" "memo")
NODES=(1000 2500 5000)
OPTIMIZATION_LEVELS=(0.5 0.7 0.9)
RUNS=3

for chain in "${CHAINS[@]}"; do
    for nodes in "${NODES[@]}"; do
        for opt_level in "${OPTIMIZATION_LEVELS[@]}"; do
            for run in $(seq 1 $RUNS); do
                echo "Run $run/$RUNS: $chain with $nodes nodes, optimization $opt_level"

                python3 sim-blockchain.py \
                    --chain $chain \
                    --nodes $nodes --neighbors $((nodes/4)) \
                    --miners $nodes --hashrate 1e6 \
                    --wallets 1000 --transactions 500 --interval 0.01 \
                    --print 50 \
                    --danksharding --parallel-shards 8 --tx-optimization $opt_level \
                    > $RESULTS_DIR/crosschain_${chain}_${nodes}nodes_opt${opt_level}_run${run}.log 2>&1

                echo "Completed: $chain $nodes nodes optimization $opt_level run $run"
            done
        done
    done
done

echo "Cross-chain Danksharding tests completed. Results in $RESULTS_DIR"
EOF

# 4. Scalability and Stress Testing
cat > $EXPERIMENT_DIR/run_scalability_stress.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
RESULTS_DIR="danksharding_results/scalability"
mkdir -p $RESULTS_DIR

echo "Starting Scalability Stress Tests with Danksharding..."
echo "===================================================="

NODES=(5000 7500 10000)
ARCHITECTURES=("baseline" "danksharding-moderate" "danksharding-aggressive")
RUNS=3

for nodes in "${NODES[@]}"; do
    for arch in "${ARCHITECTURES[@]}"; do
        for run in $(seq 1 $RUNS); do
            echo "Run $run/$RUNS: $arch with $nodes nodes"

            case $arch in
                "baseline")
                    python3 sim-blockchain.py \
                        --chain btc \
                        --nodes $nodes --neighbors $((nodes/4)) \
                        --miners $nodes --hashrate 1e6 \
                        --wallets 1000 --transactions 1000 --interval 0.01 \
                        --print 50 \
                        > $RESULTS_DIR/${arch}_${nodes}nodes_run${run}.log 2>&1
                    ;;
                "danksharding-moderate")
                    python3 sim-blockchain.py \
                        --chain btc \
                        --nodes $nodes --neighbors $((nodes/4)) \
                        --miners $nodes --hashrate 1e6 \
                        --wallets 1000 --transactions 1000 --interval 0.01 \
                        --print 50 \
                        --danksharding --parallel-shards 8 --tx-optimization 0.7 \
                        > $RESULTS_DIR/${arch}_${nodes}nodes_run${run}.log 2>&1
                    ;;
                "danksharding-aggressive")
                    python3 sim-blockchain.py \
                        --chain btc \
                        --nodes $nodes --neighbors $((nodes/4)) \
                        --miners $nodes --hashrate 1e6 \
                        --wallets 1000 --transactions 1000 --interval 0.01 \
                        --print 50 \
                        --danksharding --parallel-shards 16 --tx-optimization 0.9 \
                        > $RESULTS_DIR/${arch}_${nodes}nodes_run${run}.log 2>&1
                    ;;
            esac

            echo "Completed: $arch $nodes nodes run $run"
        done
    done
done

echo "Scalability stress tests completed. Results in $RESULTS_DIR"
EOF

# 5. Network Topology and Latency Analysis
cat > $EXPERIMENT_DIR/run_topology_impact.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
RESULTS_DIR="danksharding_results/topology"
mkdir -p $RESULTS_DIR

echo "Starting Network Topology Impact Tests..."
echo "========================================"

NODES=(1000 2500 5000)
CONNECTIVITY=(25 50 75)  # Percentage of nodes as neighbors
SHARD_COUNTS=(4 8 16)
RUNS=3

for nodes in "${NODES[@]}"; do
    for conn_pct in "${CONNECTIVITY[@]}"; do
        neighbors=$((nodes * conn_pct / 100))
        for shards in "${SHARD_COUNTS[@]}"; do
            for run in $(seq 1 $RUNS); do
                echo "Run $run/$RUNS: $conn_pct% connectivity, $shards shards, $nodes nodes"

                python3 sim-blockchain.py \
                    --chain btc \
                    --nodes $nodes --neighbors $neighbors \
                    --miners $nodes --hashrate 1e6 \
                    --wallets 1000 --transactions 500 --interval 0.01 \
                    --print 50 \
                    --danksharding --parallel-shards $shards --tx-optimization 0.8 \
                    > $RESULTS_DIR/topology_${nodes}nodes_${conn_pct}pct_${shards}shards_run${run}.log 2>&1

                echo "Completed: $conn_pct% connectivity $shards shards $nodes nodes run $run"
            done
        done
    done
done

echo "Topology impact tests completed. Results in $RESULTS_DIR"
EOF

# 5. Extreme Load Tests with Danksharding
cat > $EXPERIMENT_DIR/run_extreme_load.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
RESULTS_DIR="danksharding_results/extreme"
mkdir -p $RESULTS_DIR

echo "Starting Extreme Load Tests with Danksharding..."
echo "==============================================="

NODES=(2500 5000)
EXTREME_LOADS=(1000 2500 5000)  # transactions per wallet
SHARD_CONFIGS=(16 32 64)
RUNS=3

for nodes in "${NODES[@]}"; do
    for txload in "${EXTREME_LOADS[@]}"; do
        for shards in "${SHARD_CONFIGS[@]}"; do
            for run in $(seq 1 $RUNS); do
                echo "Run $run/$RUNS: $txload tx/wallet, $shards shards, $nodes nodes"

                python3 sim-blockchain.py \
                    --chain btc \
                    --nodes $nodes --neighbors $((nodes/4)) \
                    --miners $nodes --hashrate 1e6 \
                    --wallets 500 --transactions $txload --interval 0.001 \
                    --print 25 \
                    --danksharding --parallel-shards $shards --tx-optimization 0.9 \
                    > $RESULTS_DIR/extreme_${nodes}nodes_${txload}tx_${shards}shards_run${run}.log 2>&1

                echo "Completed: $txload tx/wallet $shards shards $nodes nodes run $run"
            done
        done
    done
done

echo "Extreme load tests completed. Results in $RESULTS_DIR"
EOF

# Make all scripts executable
chmod +x $EXPERIMENT_DIR/*.sh

# Create tmux session starter
cat > $EXPERIMENT_DIR/start_all_experiments.sh << 'EOF'
#!/bin/bash
echo "Starting all Danksharding experiments in parallel tmux sessions..."
echo "================================================================"

# Kill any existing sessions
tmux kill-session -t dank-comparison 2>/dev/null || true
tmux kill-session -t dank-crosschain 2>/dev/null || true
tmux kill-session -t dank-scalability 2>/dev/null || true
tmux kill-session -t dank-topology 2>/dev/null || true
tmux kill-session -t dank-extreme 2>/dev/null || true

# Start new sessions
echo "Starting Danksharding comparison tests..."
tmux new-session -d -s dank-comparison 'bash danksharding_experiments/run_danksharding_comparison.sh'

echo "Starting BTC chain-specific tests..."
tmux new-session -d -s dank-btc 'bash danksharding_experiments/run_chain_btc_tests.sh'

echo "Starting ETH-style chain tests..."
tmux new-session -d -s dank-ethchains 'bash danksharding_experiments/run_chain_eth_tests.sh'

echo "Starting cross-chain Danksharding tests..."
tmux new-session -d -s dank-crosschain 'bash danksharding_experiments/run_crosschain_danksharding.sh'

echo "Starting scalability stress tests..."
tmux new-session -d -s dank-scalability 'bash danksharding_experiments/run_scalability_stress.sh'

echo "Starting topology impact tests..."
tmux new-session -d -s dank-topology 'bash danksharding_experiments/run_topology_impact.sh'

echo "Starting extreme load tests..."
tmux new-session -d -s dank-extreme 'bash danksharding_experiments/run_extreme_load.sh'

echo ""
echo "All experiments started! Monitor with:"
echo "  tmux list-sessions"
echo "  tmux attach -t dank-comparison      # Basic Danksharding vs standard comparison"
echo "  tmux attach -t dank-btc             # BTC chain-specific tests"  
echo "  tmux attach -t dank-ethchains       # ETH-style chains (BCH, LTC, DOGE, MEMO)"
echo "  tmux attach -t dank-crosschain      # Cross-chain performance analysis"
echo "  tmux attach -t dank-scalability     # Scalability and stress testing"
echo "  tmux attach -t dank-topology        # Network topology impact"
echo "  tmux attach -t dank-extreme         # Extreme load testing"
echo ""
echo "Results will be saved in danksharding_results/"
EOF

chmod +x $EXPERIMENT_DIR/start_all_experiments.sh

# Create analysis script
cat > $EXPERIMENT_DIR/analyze_results.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
RESULTS_DIR="danksharding_results"

echo "Analyzing Danksharding Experiment Results..."
echo "==========================================="

echo ""
echo "1. DANKSHARDING VS BASELINE COMPARISON:"
echo "----------------------------------------"
if [[ -d "$RESULTS_DIR/comparison" ]]; then
    echo "TPS Results (Top 10):"
    grep -h "TPS:" $RESULTS_DIR/comparison/*.log 2>/dev/null | sort -k2 -nr | head -10 || echo "No TPS results found yet"
    echo ""
    echo "Baseline vs Danksharding comparison:"
    baseline_avg=$(grep -h "TPS:" $RESULTS_DIR/comparison/baseline_*.log 2>/dev/null | awk '{sum+=$2; count++} END {if(count>0) print sum/count; else print "N/A"}')
    danksharding_avg=$(grep -h "TPS:" $RESULTS_DIR/comparison/danksharding_*.log 2>/dev/null | awk '{sum+=$2; count++} END {if(count>0) print sum/count; else print "N/A"}')
    echo "  Average Baseline TPS: $baseline_avg"
    echo "  Average Danksharding TPS: $danksharding_avg"
fi

echo ""
echo "2. CHAIN-SPECIFIC PERFORMANCE:"
echo "------------------------------"
if [[ -d "$RESULTS_DIR/chains" ]]; then
    echo "BTC Chain Results:"
    btc_tps=$(grep -h "TPS:" $RESULTS_DIR/chains/btc_*.log 2>/dev/null | awk '{sum+=$2; count++} END {if(count>0) print sum/count; else print "N/A"}')
    echo "  BTC average TPS: $btc_tps"
    
    echo "ETH-style Chain Results:"
    for chain in bch ltc doge memo; do
        chain_tps=$(grep -h "TPS:" $RESULTS_DIR/chains/${chain}_*.log 2>/dev/null | awk '{sum+=$2; count++} END {if(count>0) print sum/count; else print "N/A"}')
        echo "  $chain average TPS: $chain_tps"
    done
fi

echo ""
echo "3. CROSS-CHAIN PERFORMANCE:"
echo "---------------------------"
if [[ -d "$RESULTS_DIR/crosschain" ]]; then
    for chain in btc bch ltc doge memo; do
        chain_tps=$(grep -h "TPS:" $RESULTS_DIR/crosschain/crosschain_${chain}_*.log 2>/dev/null | awk '{sum+=$2; count++} END {if(count>0) print sum/count; else print "N/A"}')
        echo "  $chain average TPS: $chain_tps"
    done
fi

echo ""
echo "4. SCALABILITY RESULTS:"
echo "----------------------"
if [[ -d "$RESULTS_DIR/scalability" ]]; then
    for arch in baseline danksharding-moderate danksharding-aggressive; do
        arch_tps=$(grep -h "TPS:" $RESULTS_DIR/scalability/${arch}_*.log 2>/dev/null | awk '{sum+=$2; count++} END {if(count>0) print sum/count; else print "N/A"}')
        echo "  $arch average TPS: $arch_tps"
    done
fi

echo ""
echo "5. EXPERIMENT STATUS:"
echo "--------------------"
total_logs=$(find $RESULTS_DIR -name "*.log" 2>/dev/null | wc -l)
completed_logs=$(grep -l "completed\|Simulation completed" $RESULTS_DIR/*/*.log 2>/dev/null | wc -l)
echo "  Total experiments: $total_logs"
echo "  Completed experiments: $completed_logs"
echo "  Progress: $(( completed_logs * 100 / total_logs ))%" 2>/dev/null || echo "  Progress: calculating..."

echo ""
echo "6. CURRENT TMUX SESSIONS:"
echo "------------------------"
tmux list-sessions 2>/dev/null | grep -E "(dank-)" || echo "  No active experiment sessions"

echo ""
echo "Run this script periodically to monitor progress!"
EOF

chmod +x $EXPERIMENT_DIR/analyze_results.sh

echo ""
echo "Danksharding Experiment Setup Complete!"
echo "======================================="
echo ""
echo "Generated experiment scripts:"
echo "  - danksharding_experiments/run_danksharding_comparison.sh"
echo "  - danksharding_experiments/run_chain_btc_tests.sh"
echo "  - danksharding_experiments/run_chain_eth_tests.sh"
echo "  - danksharding_experiments/run_crosschain_danksharding.sh"
echo "  - danksharding_experiments/run_scalability_stress.sh"
echo "  - danksharding_experiments/run_topology_impact.sh"
echo "  - danksharding_experiments/run_extreme_load.sh"
echo ""
echo "To start all experiments in parallel:"
echo "  bash danksharding_experiments/start_all_experiments.sh"
echo ""
echo "To monitor progress:"
echo "  tmux list-sessions"
echo "  tmux attach -t <session-name>"
echo ""
echo "Results will be saved in danksharding_results/ subdirectories"
echo ""
echo "Estimated total runtime: 8-12 hours"

