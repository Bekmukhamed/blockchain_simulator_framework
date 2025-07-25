#!/usr/bin/env python3
import simpy, argparse, random, time

# Globals
network_data = io_requests = total_tx = total_coins = 0
pool = []
HEADER_SIZE = 1024
YEAR = 365 * 24 * 3600
start_time = time.time()
# Format large numbers
def human(n):
    a = abs(n)
    if a >= 1e9:
        v, s = n / 1e9, 'B'
    elif a >= 1e6:
        v, s = n / 1e6, 'M'
    elif a >= 1e3:
        v, s = n / 1e3, 'K'
    else:
        return str(int(n))
    return f"{int(v) if v.is_integer() else f'{v:.1f}'}{s}"

class Block:
    def __init__(self, i, tx, dt):
        self.id = i
        self.tx = tx
        self.size = HEADER_SIZE + tx * 256
        self.dt = dt

class Node:
    def __init__(self, env, i):
        self.env = env; self.id = i; self.blocks = set(); self.neighbors = []
    def receive(self, b):
        yield self.env.timeout(0)
        global network_data, io_requests
        if b.id in self.blocks:
            return
        self.blocks.add(b.id)
        for n in self.neighbors:
            io_requests += 1
            network_data += b.size
            self.env.process(n.receive(b))

class Miner:
    def __init__(self, i, h):
        self.id = i
        self.h = h
    def mine(self, env, d, ev):
        t = random.expovariate(self.h / d)
        tm = env.timeout(t)
        r = yield env.any_of([tm, ev])
        if tm in r and not ev.triggered:
            ev.succeed(self)
        yield ev

# Wallet sends transactions into pool
def wallet(env, wid, count, interval):
    for _ in range(count):
        yield env.timeout(interval)
        pool.append((wid, env.now))

def coord(env, nodes, miners, bt, diff0, blocks_limit, blk_sz, print_int, dbg,
          wallets, tx_per_wallet, init_reward, halving_interval):
    global network_data, io_requests, total_tx, total_coins, pool
    bc = lt = la = ba = 0
    last_t = last_b = last_tx = last_coins = 0

    diff = diff0 if diff0 is not None else bt * sum(m.h for m in miners)
    th = sum(m.h for m in miners)

    reward = init_reward
    halvings = 0
    max_halvings = 35

    has_tx = tx_per_wallet > 0
    total_needed = wallets * tx_per_wallet if has_tx else None
    pool_processed = 0

    while True:
        if blocks_limit is not None and bc >= blocks_limit:
            break
        if has_tx and pool_processed >= total_needed:
            break

        # Difficulty retarget every 2016 blocks
        if diff0 is None and ba >= 2016:
            elapsed = env.now - la
            actual_avg = elapsed / ba if ba else bt
            factor = bt / actual_avg if actual_avg > 0 else 1
            diff *= factor
            la = env.now
            ba = 0
            if dbg:
                print(f"[{env.now:.2f}] Diff:{human(diff)} H:{human(th)} "
                      f"Tx:{total_tx} C:{human(total_coins)} Pool:{len(pool)} "
                      f"infl:N/A NMB:{network_data/1e6:.2f} IO:{io_requests}")

        # Mining round
        ev = env.event()
        for m in miners:
            env.process(m.mine(env, diff, ev))
        winner = yield ev

        # New block
        dt = env.now - lt
        lt = env.now
        bc += 1
        ba += 1

        if has_tx:
            avail = len(pool)
            take = min(avail, blk_sz)
            pool_processed += take
            for _ in range(take):
                pool.pop(0)
            txs = take + 1
        else:
            txs = 1

        b = Block(bc, txs, dt)
        total_tx += txs

        # Mint reward and halving
        if halvings < max_halvings:
            total_coins += reward
        if halving_interval > 0 and bc % halving_interval == 0 and halvings < max_halvings:
            halvings += 1
            reward = reward / 2 if halvings < max_halvings else 0

        env.process(random.choice(nodes).receive(b))

        # Logging / summary
        if dbg:
            print(f"[{env.now:.2f}] B{b.id} by M{winner.id} dt:{b.dt:.2f}s "
                  f"Diff:{human(diff)} H:{human(th)} Tx:{total_tx} "
                  f"C:{human(total_coins)} Pool:{len(pool)} "
                  f"infl:N/A NMB:{network_data/1e6:.2f} IO:{io_requests}")
        elif bc % print_int == 0:
            pct = (bc / blocks_limit) * 100 if blocks_limit else 0
            ti = env.now - last_t
            dtx = total_tx - last_tx
            dcoins = total_coins - last_coins
            abt = ti / (bc - last_b) if bc - last_b else 0
            tps = dtx / ti if ti > 0 else 0
            infl = (dcoins / last_coins) * (YEAR / ti) * 100 if last_coins > 0 else 0
            eta = (blocks_limit - bc) * abt if blocks_limit else 0
            print(f"[{env.now:.2f}] Sum B:{bc}/{blocks_limit} {pct:.1f}% abt:{abt:.2f}s "
                  f"tps:{tps:.2f} infl:{infl:.2f}% ETA:{eta:.2f}s "
                  f"Diff:{human(diff)} H:{human(th)} Tx:{total_tx} "
                  f"C:{human(total_coins)} Pool:{len(pool)} "
                  f"NMB:{network_data/1e6:.2f} IO:{io_requests}")
            last_t, last_b, last_tx, last_coins = env.now, bc, total_tx, total_coins

    # Final summary
    total_time = env.now
    abt = total_time / bc if bc else 0
    tps_total = total_tx / total_time if total_time > 0 else 0
    infl_total = (total_coins - last_coins) / last_coins * (YEAR / total_time) * 100 if last_coins > 0 else 0
    simulation_time = time.time() - start_time
    if blocks_limit:
        print(f"[******] End B:{bc}/{blocks_limit} 100.0% abt:{abt:.2f}s tps:{tps_total:.2f} "
              f"infl:{infl_total:.2f}% Diff:{human(diff)} H:{human(th)} "
              f"Tx:{total_tx} C:{human(total_coins)} Pool:{len(pool)} "
              f"NMB:{network_data/1e6:.2f} IO:{io_requests}")
        print(f"\nSimulation completed in {simulation_time:.2f} seconds")
    else:
        print(f"[******] End B:{bc} abt:{abt:.2f}s tps:{tps_total:.2f} "
              f"infl:{infl_total:.2f}% Diff:{human(diff)} H:{human(th)} "
              f"Tx:{total_tx} C:{human(total_coins)} Pool:{len(pool)} "
              f"NMB:{network_data/1e6:.2f} IO:{io_requests}")
        print(f"\nSimulation completed in {simulation_time:.2f} seconds")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--nodes",       type=int,   required=True)
    p.add_argument("--neighbors",   type=int,   required=True)
    p.add_argument("--blocksize",   type=int,   required=True)
    p.add_argument("--blocktime",   type=float, required=True)
    p.add_argument("--miners",      type=int,   required=True)
    p.add_argument("--hashrate",    type=float, required=True)
    p.add_argument("--difficulty",  dest="diff0", type=float)
    p.add_argument("--blocks",      dest="blocks_limit", type=int,
                     help="max number of blocks (optional)")
    p.add_argument("--years",       dest="years", type=float,
                     help="run sim for this many years if --blocks omitted")
    p.add_argument("--wallets",     type=int,   required=True)
    p.add_argument("--transactions",type=int,   required=True)
    p.add_argument("--interval",    type=float, required=True)
    p.add_argument("--print",       dest="print_int", type=int, default=144,
                     help="blocks interval for summary (default 144)")
    p.add_argument("--debug",       action="store_true")
    p.add_argument("--reward",      dest="init_reward", type=float, default=50,
                     help="initial coinbase reward (default 50)")
    p.add_argument("--halving",     dest="halving_interval", type=int, default=210000,
                     help="blocks between reward halving (default 210000; 0 disables halving)")
    args = p.parse_args()

    blocks_limit = args.blocks_limit
    if blocks_limit is None and args.years:
        blocks_limit = int(args.years * YEAR / args.blocktime)

    env = simpy.Environment()
    for i in range(args.wallets):
        env.process(wallet(env, i, args.transactions, args.interval))
    nodes = [Node(env, i) for i in range(args.nodes)]
    for n in nodes:
        n.neighbors = random.sample([x for x in nodes if x != n], args.neighbors)
    miners = [Miner(i, args.hashrate) for i in range(args.miners)]

    coord_proc = env.process(coord(env, nodes, miners,
                     args.blocktime, args.diff0,
                     blocks_limit, args.blocksize,
                     args.print_int, args.debug,
                     args.wallets, args.transactions,
                     args.init_reward, args.halving_interval))
    env.run(until=coord_proc)

if __name__ == "__main__":
    main()