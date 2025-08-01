#!/usr/bin/env python3
import simpy
import argparse
import random
import os
import sys
from sortedcontainers import SortedList  # NEW: for fee-prioritized mempool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import simulation.globals as sim_globals
from simulation.core import Node, Miner, wallet
from simulation.coordinator import coord
from simulation.utils import (
    load_config,
    load_chain_config,
    load_workload_config,
    merge_configs,
    apply_workload_config
)
import block_check


def reset_globals():
    sim_globals.network_data = 0
    sim_globals.io_requests = 0
    sim_globals.total_tx = 0
    sim_globals.total_coins = 0
    sim_globals.wallet_balances = {}
    sim_globals.start_time = __import__('time').time()
    sim_globals.FEE_PER_TX = 1000  # Default fallback for fixed fees
    sim_globals.pool = SortedList(key=lambda x: -x[0])  # Sorted by fee/vB descending


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
    p.add_argument("--fees", action="store_true", help="Enable fee logic and wallet balances")

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

    # Override from CLI args
    overrides = {
        "nodes": args.nodes,
        "neighbors": args.neighbors,
        "blocksize": args.blocksize,
        "blocktime": args.blocktime,
        "miners": args.miners,
        "hashrate": args.hashrate,
        "blocks": args.blocks_limit,
        "wallets": args.wallets,
        "transactions": args.transactions,
        "interval": args.interval,
        "print": args.print_int,
        "debug": args.debug,
        "reward": args.init_reward,
        "halving": args.halving_interval,
    }
    for k, v in overrides.items():
        if v is not None:
            sim_config[k] = v

    # Determine block count if not fixed
    blocks_limit = sim_config.get('blocks')
    if blocks_limit is None and args.years:
        blocks_limit = int(args.years * sim_globals.YEAR / sim_config['blocktime'])

    # Auto-adjust blocks if necessary based on tx count
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

    # Launch wallets
    for i in range(sim_config['wallets']):
        env.process(wallet(env, i, sim_config['transactions'], sim_config['interval'], use_fees=args.fees))

    # Set up nodes and neighbors
    nodes = [Node(env, i) for i in range(sim_config['nodes'])]
    for n in nodes:
        n.neighbors = random.sample([x for x in nodes if x != n], sim_config['neighbors'])

    # Initialize miners
    miners = [Miner(i, sim_config['hashrate']) for i in range(sim_config['miners'])]
    if args.fees:
        for m in miners:
            sim_globals.wallet_balances[m.id] = 0.0

    # Run simulation
    coord_proc = env.process(coord(
        env, nodes, miners,
        sim_config['blocktime'], args.diff0,
        blocks_limit, sim_config['blocksize'],
        sim_config['print'], sim_config['debug'],
        sim_config['wallets'], sim_config['transactions'],
        sim_config['reward'], sim_config['halving'],
        sim_globals.start_time,
        use_fees=args.fees,
        wallet_balances=sim_globals.wallet_balances,
        fee_per_tx=sim_globals.FEE_PER_TX
    ))

    env.run(until=coord_proc)
    return 0


if __name__ == "__main__":
    exit(main())
