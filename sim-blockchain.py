#!/usr/bin/env python3
import simpy
import argparse
import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import simulation.globals as sim_globals
from simulation.core import Node, Miner
from simulation.core.wallet import wallet
from simulation.coordinator import coord
from simulation.utils import load_config, load_chain_config, load_workload_config, merge_configs, apply_workload_config
import simulation.utils.block_check as block_check
from simulation.cli.parser import parse_args

# Danksharding imports
from simulation.utils.danksharding_utils import enable_danksharding, disable_danksharding, load_danksharding_config


def reset_globals():
    sim_globals.network_data = 0
    sim_globals.io_requests = 0
    sim_globals.total_tx = 0
    sim_globals.total_coins = 0
    sim_globals.pool = []
    sim_globals.start_time = __import__('time').time()
    # Reset Danksharding globals
    sim_globals.total_blobs_processed = 0
    sim_globals.total_blob_data = 0
    sim_globals.parallel_speedup = 1.0


def main():
    args = parse_args()
    
    reset_globals()
    
    # Configure Danksharding
    if args.danksharding:
        enable_danksharding()
        from simulation.core.blobs import danksharding_config
        from simulation.core.parallel_shards import parallel_processor
        
        if hasattr(args, 'max_blobs') and args.max_blobs:
            danksharding_config.max_blobs_per_block = args.max_blobs
        if hasattr(args, 'tx_optimization') and args.tx_optimization:
            danksharding_config.tx_optimization_rate = args.tx_optimization
        if hasattr(args, 'parallel_shards') and args.parallel_shards:
            parallel_processor.num_shards = args.parallel_shards
            
        print(f"Danksharding enabled: max_blobs={danksharding_config.max_blobs_per_block}, tx_optimization={danksharding_config.tx_optimization_rate}, parallel_shards={parallel_processor.num_shards}")
    else:
        disable_danksharding()
    
    # Print configuration info
    if hasattr(args, 'chain') and args.chain:
        print(f"Using chain configuration: {args.chain}")
    if hasattr(args, 'workload') and args.workload:
        print(f"Using workload configuration: {args.workload}")
    
    # Apply fallback defaults for critical parameters
    args.neighbors = args.neighbors or 5
    args.interval = args.interval or 1.0
    args.blocksize = args.blocksize or 4096
    args.blocktime = args.blocktime or 600
    args.hashrate = args.hashrate or 1000000
    args.print_int = args.print_int or 144
    args.init_reward = args.init_reward or 50
    args.halving_interval = args.halving_interval or 210000
    args.diff0 = args.diff0 or 0.0001
    
    # Initialize simulation environment
    env = simpy.Environment()
    
    # Initialize simulation globals
    sim_globals.total_nodes = args.nodes
    sim_globals.total_miners = args.miners
    
    # Create wallets and transactions first
    if args.wallets > 0 and args.transactions > 0:
        for i in range(args.wallets):
            # Generate transactions using wallet function
            env.process(wallet(env, i, args.transactions, args.interval))
    
    # Create nodes
    nodes = []
    for i in range(args.nodes):
        node = Node(env, i, blocktime=args.blocktime)
        nodes.append(node)
    
    # Set up node neighbors
    for n in nodes:
        available_nodes = [x for x in nodes if x != n]
        neighbor_count = min(args.neighbors or 5, len(available_nodes))  # Default to 5 if None
        if neighbor_count > 0:
            n.neighbors = random.sample(available_nodes, neighbor_count)
        else:
            n.neighbors = []
    
    # Create miners
    miners = []
    for i in range(args.miners):
        miner = Miner(args.nodes + i, args.hashrate)
        miners.append(miner)
    
    # Start coordinator process
    coord_proc = env.process(coord(
        env, nodes, miners,
        args.blocktime, args.diff0,
        args.blocks_limit, args.blocksize,
        args.print_int, args.debug,
        args.wallets, args.transactions,
        args.init_reward, args.halving_interval
    ))

    # Run simulation
    env.run(until=coord_proc)
    
    # Print Danksharding results if enabled
    if args.danksharding and sim_globals.danksharding_enabled:
        print("\n" + "="*60)
        print("DANKSHARDING PERFORMANCE RESULTS:")
        print(f"Parallel shards used: {args.parallel_shards}")
        print(f"Parallel speedup achieved: {sim_globals.parallel_speedup:.1f}x")
        print(f"Total blobs processed: {sim_globals.total_blobs_processed:,}")
        print(f"Total blob data: {sim_globals.total_blob_data:,} bytes ({sim_globals.total_blob_data/1024/1024:.2f} MB)")
        if sim_globals.total_blobs_processed > 0:
            print(f"Average blob size: {sim_globals.total_blob_data/sim_globals.total_blobs_processed:.0f} bytes")
        
        # Calculate performance improvements
        from simulation.core.blobs import danksharding_config
        optimized_tx_ratio = danksharding_config.tx_optimization_rate
        print(f"Transaction optimization rate: {optimized_tx_ratio:.1%}")
        theoretical_speedup = sim_globals.parallel_speedup * (1/(1-optimized_tx_ratio*0.9))
        print(f"Theoretical TPS improvement: {theoretical_speedup:.1f}x")
        print("="*60)
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("Simulation interrupted by user")
        
        sys.exit(130)