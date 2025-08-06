import random, time
from simulation.core.block import Block
from simulation.core.utils import (
    pool, human, YEAR, network_data, io_requests, total_tx, total_coins
)

def coord_flat(env, nodes, miners, bt, diff0, blocks_limit, blk_sz, print_int, dbg,
               wallets, tx_per_wallet, init_reward, halving_interval, start_time,
               use_fees=False, wallet_balances=None, fee_per_tx=0.1):
    global network_data, io_requests, total_tx, total_coins, pool

    bc = lt = la = ba = 0
    last_t = last_b = last_tx = last_coins = 0
    reward = init_reward
    halvings = 0
    max_halvings = 35
    th = sum(m.h for m in miners)
    diff = diff0 if diff0 else bt * th

    has_tx = tx_per_wallet > 0
    total_needed = wallets * tx_per_wallet if has_tx else None
    pool_processed = 0

    while True:
        if blocks_limit is not None and bc >= blocks_limit:
            break
        if has_tx and pool_processed >= total_needed:
            break

        if diff0 is None and ba >= 2016:
            elapsed = env.now - la
            actual_avg = elapsed / ba if ba else bt
            factor = bt / actual_avg if actual_avg > 0 else 1
            diff *= factor
            la = env.now
            ba = 0

        # Mining
        ev = env.event()
        for m in miners:
            env.process(m.mine(env, diff, ev))
        winner = yield ev

        dt = env.now - lt
        lt = env.now
        bc += 1
        ba += 1

        # Transactions
        if has_tx:
            avail = len(pool)
            take = min(avail, blk_sz)
            txs = take + 1
            fee = 0
            for _ in range(take):
                _, tx = pool.pop(0)
                pool_processed += 1
                if use_fees:
                    fee += tx.get("fee", 0)
        else:
            txs = 1
            fee = 0

        b = Block(bc, txs, dt)
        total_tx += txs
        if halvings < max_halvings:
            total_coins += reward
        if halving_interval > 0 and bc % halving_interval == 0:
            halvings += 1
            reward = reward / 2 if halvings < max_halvings else 0

        if wallet_balances is not None:
            wallet_balances[winner.id] = wallet_balances.get(winner.id, 0.0) + reward + fee

        env.process(random.choice(nodes).receive(b, flat=True))  # <== flat=True

        if dbg:
            print(f"[{env.now:.2f}] B{b.id} by M{winner.id} dt:{b.dt:.2f}s Diff:{human(diff)} H:{human(th)} "
                  f"Tx:{total_tx} C:{human(total_coins)} Pool:{len(pool)}")
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
                  f"Diff:{human(diff)} H:{human(th)} Tx:{total_tx} C:{human(total_coins)} "
                  f"Pool:{len(pool)} NMB:{network_data / 1e6:.2f} IO:{io_requests}")
            last_t, last_b, last_tx, last_coins = env.now, bc, total_tx, total_coins

    # Final summary
    sim_time = time.time() - start_time
    abt = env.now / bc if bc else 0
    tps_final = total_tx / env.now if env.now > 0 else 0
    print(f"\n[******] End B:{bc}/{blocks_limit} 100.0% abt:{abt:.2f}s tps:{tps_final:.2f} "
          f"Diff:{human(diff)} H:{human(th)} Tx:{total_tx} C:{human(total_coins)} "
          f"Pool:{len(pool)} NMB:{network_data / 1e6:.2f} IO:{io_requests}")
    print(f"\nSimulation completed in {sim_time:.2f} seconds")
    print(f"Simulated blockchain time: {env.now:.2f} seconds")
