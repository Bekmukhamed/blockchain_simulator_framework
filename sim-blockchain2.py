from simulation.cli.parser import parse_args
from simulation.core.setup import setup_simulation
from simulation.core.wallet import wallet
from simulation.core.coordinator import coord
import time

def main():
    args = parse_args()
    env, nodes, miners = setup_simulation(args)

    for i in range(args.wallets):
        env.process(wallet(env, i, args.transactions, args.interval))

    start = time.time()
    coord_proc = env.process(coord(env, nodes, miners,
                                   args.blocktime, args.diff0,
                                   args.blocks_limit, args.blocksize,
                                   args.print_int, args.debug,
                                   args.wallets, args.transactions,
                                   args.init_reward, args.halving_interval,
                                   start))
    env.run(until=coord_proc)

if __name__ == "__main__":
    main()
