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
from simulation.utils import (
    load_config, load_chain_config, load_workload_config,
    merge_configs, apply_workload_config
)
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
    p.add_argument("--chain", type=str)
    p.add_argument("--workload", type=str)
    p.add_argument("--nodes", type=int)
    p.add_argument("--neighbors", type=int)
    p.add_argument("--blocksize", type=int)
    p.add_argument("--blocktime", type=float)
    p.add_argument("--miners", type=int)
    p.add_argument("--hashrate", type=float)
    p.add_argument("--difficulty", dest="diff0", type=float)
    p.add_argument("--blocks", dest="blocks_limit", type=int)
    p.add_argument("--years", dest="years", type=float)
    p.add_argument("--wallets", type=int)
    p.add_argument("--transactions", type=int)
    p.add_argument("--interval", type=float)
    p.add_argument("--print", dest="print_int", type=int)
    p.add_argument("--debug", action="store_true")
    p.add_argument("--reward", dest="init_reward", type=float)
    p.add_argument("--halving", dest="halving_interval", type=int)

    args = p.parse_args()
    reset_globals()

    config_dir = os.path.join(os.path.dirname(__file__), 'config')
    config = load_config(os.path.join(config_dir, 'defaults.json'))

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
    # Override config with CLI args
    for key, val in [
        ('nodes', args.nodes),
        ('neighbors', args.neighbors),
        ('blocksize', args.blocksize),
        ('blocktime', args.blocktime),
        ('miners', args.miners),
        ('hashrate', args.hashrate),
        ('blocks', args.blocks_limit),
        ('wallets', args.wallets),
        ('transactions', args.transactions),
        ('interval', args.interval),
        ('print', args.print_int),
        ('debug', args.debug),
        ('reward', args.init_reward),
        ('halving', args.halving_interval)
    ]:
        if val is not None:
            sim_config[key] = val

    # Auto-calculate blocks if years are specified
    blocks_limit = sim_config.get('blocks')
    if blocks_limit is None and args.years:
        blocks_limit = int(args.years * sim_globals.YEAR / sim_config['blocktime'])

    # Adjust for transaction workload
    if sim_config['transactions'] > 0:
        total_tx = sim_config['wallets'] * sim_config['transactions']
        expected_blocks = block_check.validate_blocks_count(total_tx, sim_config['blocksize'], blocks_limit)
        if blocks_limit is None:
            blocks_limit = expected_blocks
            print(f"Auto-setting blocks to {expected_blocks} based on workload")
        elif expected_blocks < blocks_limit:
            print(f"Limiting blocks to {expected_blocks} (workload-based)")
            blocks_limit = expected_blocks

    env = simpy.Environment()

    # Wallets
    for i in range(sim_config['wallets']):
        env.process(wallet(env, i, sim_config['transactions'], sim_config['interval']))

    # Nodes
    nodes = [Node(env, i, blocktime=sim_config['blocktime']) for i in range(sim_config['nodes'])]
    for n in nodes:
        n.neighbors = random.sample([x for x in nodes if x != n], sim_config['neighbors'])

    # Miners
    miners = [Miner(i, sim_config['hashrate']) for i in range(sim_config['miners'])]
    # Force debug mode ON regardless of --debug flag
    sim_config['debug'] = True
    # Coordinator
    coord_proc = env.process(coord(
        env, nodes, miners,
        sim_config['blocktime'], args.diff0,
        blocks_limit, sim_config['blocksize'],
        sim_config['print'], sim_config['debug'],
        sim_config['wallets'], sim_config['transactions'],
        sim_config['reward'], sim_config['halving']
    ))
    print(f"Miners: {len(miners)}, Nodes: {len(nodes)}, Wallets: {sim_config['wallets']}")
    print(f"Simulating {blocks_limit} blocks at {sim_config['blocktime']}s block time")

    env.run(until=coord_proc)
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("Simulation interrupted by user")
        sys.exit(130)
