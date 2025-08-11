#!/usr/bin/env python3
import simpy
import random
import os
import sys
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import simulation.globals as sim_globals
from simulation.core import Node, Miner, wallet
from simulation.coordinator import coord
from simulation.cli.parser import parse_args  # Use existing parser
from config.loader import get_defaults


def reset_globals():
    sim_globals.network_data = 0
    sim_globals.io_requests = 0
    sim_globals.total_tx = 0
    sim_globals.total_coins = 0
    sim_globals.pool = []
    sim_globals.start_time = __import__('time').time()


def load_config(path):
    """Load default configuration from JSON file"""
    with open(path, 'r') as f:
        return json.load(f)


def main():
    # Use the centralized parser
    args = parse_args()

    reset_globals()
    
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    defaults_path = os.path.join(config_dir, 'defaults.json')
    
    try:
        config = load_config(defaults_path)
    except FileNotFoundError:
        # Use basic defaults if file not found
        config = {
            'simulation': {
                'nodes': 10, 'neighbors': 3, 'blocksize': 4096, 'blocktime': 600,
                'miners': 5, 'hashrate': 1e6, 'wallets': 10, 'transactions': 0,
                'interval': 10.0, 'print': 144, 'debug': False, 'reward': 50,
                'halving': 210000
            }
        }
    
    sim_config = config['simulation']
    
    if args.nodes is not None:
        sim_config['nodes'] = args.nodes
    if args.neighbors is not None:
        sim_config['neighbors'] = args.neighbors
    if args.blocksize is not None:
        sim_config['blocksize'] = args.blocksize
    if args.blocktime is not None:
        sim_config['blocktime'] = args.blocktime
    if args.miners is not None:
        sim_config['miners'] = args.miners
    if args.hashrate is not None:
        sim_config['hashrate'] = args.hashrate
    if args.blocks_limit is not None:
        sim_config['blocks'] = args.blocks_limit
    if args.wallets is not None:
        sim_config['wallets'] = args.wallets
    if args.transactions is not None:
        sim_config['transactions'] = args.transactions
    if args.interval is not None:
        sim_config['interval'] = args.interval
    if args.print_int is not None:
        sim_config['print'] = args.print_int
    if args.debug is not None:
        sim_config['debug'] = args.debug
    if args.init_reward is not None:
        sim_config['reward'] = args.init_reward
    if args.halving_interval is not None:
        sim_config['halving'] = args.halving_interval
    



    blocks_limit = sim_config.get('blocks')
    if blocks_limit is None and args.years:
        blocks_limit = int(args.years * sim_globals.YEAR / sim_config['blocktime'])

    if sim_config['transactions'] > 0:
        total_tx = sim_config['wallets'] * sim_config['transactions']

        expected_blocks = (total_tx + sim_config['blocksize'] - 1) // sim_config['blocksize']
        if blocks_limit is None:
            blocks_limit = expected_blocks
            print(f"Auto-setting blocks to {expected_blocks} based on workload")
        elif expected_blocks < blocks_limit:
            print(f"Limiting blocks to {expected_blocks} (workload-based) instead of {blocks_limit} (time-based)")
            blocks_limit = expected_blocks
    

    env = simpy.Environment()

    for i in range(sim_config['wallets']):
        env.process(wallet(env, i, sim_config['transactions'], sim_config['interval']))
    

    nodes = [Node(env, i, blocktime=sim_config['blocktime']) for i in range(sim_config['nodes'])]
    for n in nodes:
        n.neighbors = random.sample([x for x in nodes if x != n], sim_config['neighbors'])

    miners = [Miner(i, sim_config['hashrate']) for i in range(sim_config['miners'])]

    # Sharding setup
    shard_manager = None
    if args.shards:
        from simulation.sharding.sharding import DynamicShardManager
        
        shard_manager = DynamicShardManager(
            initial_shard_count=args.shards,
            max_shards=args.max_shards or 16
        )
        
        # Apply speed optimizations based on command line flags or node count
        if args.turbo or sim_config['nodes'] >= 200:
            shard_manager.enable_turbo_mode(True)
            print("Turbo mode enabled for maximum speed")
        elif args.fast or sim_config['nodes'] >= 100:
            shard_manager.enable_fast_mode(True)
            print("Fast mode enabled for improved performance")
        
        if args.load_threshold:
            shard_manager.load_threshold_high = args.load_threshold
            
        shard_manager.assign_nodes_to_shards(nodes)
        print(f"Sharding enabled: {args.shards} initial shards")

    coord_proc = env.process(coord(
        env, nodes, miners,
        sim_config['blocktime'], args.diff0,
        blocks_limit, sim_config['blocksize'],
        sim_config['print'], sim_config['debug'],
        sim_config['wallets'], sim_config['transactions'],
        sim_config['reward'], sim_config['halving'],
        shard_manager
    ))

    env.run(until=coord_proc)
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("Simulation interrupted by user")
        
        sys.exit(130)