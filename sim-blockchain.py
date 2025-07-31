#!/usr/bin/env python3
import simpy
import argparse
import random
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import simulation.globals as sim_globals
from simulation.core import Node, Miner, wallet
from simulation.coordinator import coord
from simulation.utils import load_config, load_chain_config, load_workload_config, merge_configs, apply_workload_config
import simulation.utils.block_check as block_check


def reset_globals():
    sim_globals.network_data = 0
    sim_globals.io_requests = 0
    sim_globals.total_tx = 0
    sim_globals.total_coins = 0
    sim_globals.pool = []
    sim_globals.start_time = __import__('time').time()


def main():
    p = argparse.ArgumentParser(description='Blockchain Simulator')
    p.add_argument("--chain", type=str, help="Use predefined chain configuration (btc, bch, ltc, doge, memo)")
    p.add_argument("--workload", type=str, help="Use predefined workload configuration (small, medium, large)")
    p.add_argument("--nodes", type=int, help="Number of nodes")
    p.add_argument("--neighbors", type=int, help="Number of neighbors per node")
    p.add_argument("--blocksize", type=int, help="Block size in transactions")
    p.add_argument("--blocktime", type=float, help="Target block time in seconds")
    p.add_argument("--miners", type=int, help="Number of miners")
    p.add_argument("--hashrate", type=float, help="Hash rate per miner")
    p.add_argument("--difficulty", dest="diff0", type=float, help="Initial difficulty")
    p.add_argument("--blocks", dest="blocks_limit", type=int, help="Max number of blocks (optional)")
    p.add_argument("--years", dest="years", type=float, help="Run sim for this many years if --blocks omitted")
    p.add_argument("--wallets", type=int, help="Number of wallets")
    p.add_argument("--transactions", type=int, help="Transactions per wallet")
    p.add_argument("--interval", type=float, help="Transaction interval")
    p.add_argument("--print", dest="print_int", type=int, help="Blocks interval for summary (default 144)")
    p.add_argument("--debug", action="store_true", help="Enable debug output")
    p.add_argument("--reward", dest="init_reward", type=float, help="Initial coinbase reward (default 50)")
    p.add_argument("--halving", dest="halving_interval", type=int, help="Blocks between reward halving (default 210000; 0 disables halving)")

    args = p.parse_args()

    reset_globals()
    
    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    defaults_path = os.path.join(config_dir, 'defaults.json')
    
    config = load_config(defaults_path)
    
    if args.chain:
        try:
            chain_config = load_chain_config(args.chain, config_dir)
            config = merge_configs(config, chain_config)
            print(f"Using {chain_config['name']} ({chain_config['symbol']}) configuration")
        except ValueError as e:
            print(f"Error: {e}")
            return 1
    
    if args.workload:
        try:
            workload_config = load_workload_config(args.workload, config_dir)
            config = apply_workload_config(config, workload_config)
            print(f"Using {workload_config['name']}: {workload_config['description']}")
        except ValueError as e:
            print(f"Error: {e}")
            return 1

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
        expected_blocks = block_check.validate_blocks_count(total_tx, sim_config['blocksize'], blocks_limit)
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


    coord_proc = env.process(coord(
        env, nodes, miners,
        sim_config['blocktime'], args.diff0,
        blocks_limit, sim_config['blocksize'],
        sim_config['print'], sim_config['debug'],
        sim_config['wallets'], sim_config['transactions'],
        sim_config['reward'], sim_config['halving']
    ))

    env.run(until=coord_proc)
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("Simulation interrupted by user")
        
        sys.exit(130)