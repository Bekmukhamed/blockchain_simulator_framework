import argparse
from config.loader import get_defaults
import block_check

def parse_args():
    p = argparse.ArgumentParser()
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
    p.add_argument("--print", dest="print_int", type=int, default=144)
    p.add_argument("--debug", action="store_true")
    p.add_argument("--reward", dest="init_reward", type=float, default=50)
    p.add_argument("--halving", dest="halving_interval", type=int, default=210000)
    p.add_argument("--chain", type=str)
    p.add_argument("--workload", type=str)
    args = p.parse_args()

    merged = get_defaults(args)
    args.__dict__.update(merged)

    # Blocks limit logic
    YEAR = 365 * 24 * 3600
    if args.blocks_limit is None and args.years:
        args.blocks_limit = int(args.years * YEAR / args.blocktime)

    # Workload check
    if args.transactions > 0:
        total_tx = args.wallets * args.transactions
        est_blocks = block_check.validate_blocks_count(total_tx, args.blocksize, args.blocks_limit)
        if args.blocks_limit is None:
            args.blocks_limit = est_blocks
            print(f"Auto-setting blocks to {est_blocks} based on workload")
        elif est_blocks < args.blocks_limit:
            print(f"Limiting blocks to {est_blocks} (workload-based) instead of {args.blocks_limit} (time-based)")
            args.blocks_limit = est_blocks

    return args
