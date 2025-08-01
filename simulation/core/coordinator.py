import random, time
from simulation.core.block import Block
from simulation.core.utils import pool, human, YEAR, network_data, io_requests, total_tx, total_coins

def coord(env, nodes, miners, bt, diff0, blocks_limit, blk_sz, print_int, dbg,
          wallets, tx_per_wallet, init_reward, halving_interval, start_time):
    
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

        if dbg:
            print(f"[{env.now:.2f}] B{b.id} by M{winner.id} dt:{b.dt:.2f}s "
                  f"Diff:{human(diff)} H:{human(th)} Tx:{total_tx} "
                  f"C:{human(total_coins)} Pool:{len(pool)} "
                  f"NMB:{network_data/1e6:.2f} IO:{io_requests}")
        elif bc % print_int == 0:
            ti = env.now - last_t
            dtx = total_tx - last_tx
            dcoins = total_coins - last_coins
            abt = ti / (bc - last_b)
            tps = dtx / ti if ti > 0 else 0
            infl = (dcoins / last_coins) * (YEAR / ti) * 100 if last_coins else 0
            eta = (blocks_limit - bc) * abt
            print(f"[{env.now:.2f}] Sum B:{bc}/{blocks_limit} {100*bc/blocks_limit:.1f}% abt:{abt:.2f}s "
                  f"tps:{tps:.2f} infl:{infl:.2f}% ETA:{eta:.2f}s")

            last_t, last_b, last_tx, last_coins = env.now, bc, total_tx, total_coins

    # Final report
    # total_time = env.now
    # abt = total_time / bc if bc else 0
    # tps = total_tx / total_time if total_time else 0
    # infl = (total_coins - last_coins) / last_coins * (YEAR / total_time) * 100 if last_coins else 0
    # print(f"\n[******] Final B:{bc}/{blocks_limit} abt:{abt:.2f}s tps:{tps:.2f} "
    #       f"infl:{infl:.2f}% Diff:{human(diff)} H:{human(th)} "
    #       f"Tx:{total_tx} C:{human(total_coins)} Pool:{len(pool)} "
    #       f"NMB:{network_data/1e6:.2f} IO:{io_requests}")
    # print(f"\nSimulation completed in {time.time() - start_time:.2f} seconds")
    # print(f"Simulated blockchain time: {total_time:.2f} seconds")
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
        print(f"Simulated blockchain time: {env.now:.2f} seconds")
    else:
        print(f"[******] End B:{bc} abt:{abt:.2f}s tps:{tps_total:.2f} "
              f"infl:{infl_total:.2f}% Diff:{human(diff)} H:{human(th)} "
              f"Tx:{total_tx} C:{human(total_coins)} Pool:{len(pool)} "
              f"NMB:{network_data/1e6:.2f} IO:{io_requests}")
        print(f"\nSimulation completed in {simulation_time:.2f} seconds")
        print(f"Simulated blockchain time: {env.now:.2f} seconds")

