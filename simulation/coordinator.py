import random
import time
import simulation.globals as sim_globals
from .core.block import Block, BlockShard
from .utils.formatter import human

def coord(env, nodes, miners, bt, diff0, blocks_limit, blk_sz, print_int, dbg,
          wallets, tx_per_wallet, init_reward, halving_interval):

    bc = lt = la = ba = 0
    last_t = last_b = last_tx = last_coins = 0
    last_infl = 0
    initial_coins = sim_globals.total_coins

    reward = init_reward
    halvings = 0
    max_halvings = 35
    th = sum(m.h for m in miners)

    # Automatically calculate difficulty if not provided
    diff = diff0 if diff0 is not None else bt * th
    if diff0 is None and dbg:
        print(f"[{env.now:.2f}] Auto-difficulty: {human(diff)} (bt={bt}, total_hashrate={th})")

    has_tx = tx_per_wallet > 0
    total_needed = wallets * tx_per_wallet if has_tx else None
    pool_processed = 0

    try:
        while True:
            if blocks_limit is not None and bc >= blocks_limit:
                break
            if has_tx and pool_processed >= total_needed:
                break

            # Retarget difficulty every 2016 blocks
            if diff0 is None and ba >= 2016:
                elapsed = env.now - la
                actual_avg = elapsed / ba if ba else bt
                factor = bt / actual_avg if actual_avg > 0 else 1
                diff *= factor
                la = env.now
                ba = 0
                if dbg:
                    print(f"[{env.now:.2f}] Diff adjusted: {human(diff)}")

            # Wait for blocktime
            yield env.timeout(bt)
            ba += 1
            bc += 1

            # Mining Phase — each miner attempts to mine
            results = []
            for m in miners:
                m.mine_until(bt, diff, results)

            if not results:
                print(f"[{env.now:.2f}] No winners this round")
                continue

            # Sort winners by ID and select finalizer (lowest ID)
            winners_sorted = sorted(results, key=lambda m: m.id)
            finalizer = winners_sorted[0]

            print(f"[{env.now:.2f}] Block {bc} Winners: {[m.id for m in winners_sorted]}, Finalizer: M{finalizer.id}")

            # Determine tx per shard
            if has_tx:
                avail = len(sim_globals.pool)
                take = min(avail, blk_sz)
                txs_per_shard = max(take // len(winners_sorted), 1)
                pool_processed += txs_per_shard * len(winners_sorted)
                for _ in range(txs_per_shard * len(winners_sorted)):
                    if sim_globals.pool:
                        sim_globals.pool.pop(0)
            else:
                txs_per_shard = 1

            # Create BlockShards
            shards = []
            for winner in winners_sorted:
                shards.append(BlockShard(miner_id=winner.id, tx_count=txs_per_shard))

            # Create final Block
            b = Block(bc, shards, bt, finalizer.id)
            sim_globals.total_tx += b.tx

            # Reward and halving logic
            if halvings < max_halvings:
                sim_globals.total_coins += reward
            if halving_interval > 0 and bc % halving_interval == 0 and halvings < max_halvings:
                halvings += 1
                reward = reward / 2 if halvings < max_halvings else 0

            # Broadcast the block
            env.process(random.choice(nodes).receive(b, sender_node=None))

            # Logging
            if dbg:
                print(f"[{env.now:.2f}] B{b.id} by M{finalizer.id} (shards:{len(shards)}) dt:{bt:.2f}s "
                      f"Diff:{human(diff)} H:{human(th)} Tx:{sim_globals.total_tx} "
                      f"C:{human(sim_globals.total_coins)} Pool:{len(sim_globals.pool)} "
                      f"infl:N/A NMB:{sim_globals.network_data/1e6:.2f} IO:{sim_globals.io_requests}")
            elif bc % print_int == 0:
                pct = (bc / blocks_limit) * 100 if blocks_limit else 0
                ti = env.now - last_t
                dtx = sim_globals.total_tx - last_tx
                dcoins = sim_globals.total_coins - last_coins
                abt = ti / (bc - last_b) if bc - last_b else 0
                tps = dtx / ti if ti > 0 else 0
                infl = (dcoins / last_coins) * (sim_globals.YEAR / ti) * 100 if last_coins > 0 else 0
                eta = (blocks_limit - bc) * abt if blocks_limit else 0
                print(f"[{env.now:.2f}] Sum B:{bc}/{blocks_limit} {pct:.1f}% abt:{abt:.2f}s "
                      f"tps:{tps:.2f} infl:{infl:.2f}% ETA:{eta:.2f}s "
                      f"Diff:{human(diff)} H:{human(th)} Tx:{sim_globals.total_tx} "
                      f"C:{human(sim_globals.total_coins)} Pool:{len(sim_globals.pool)} "
                      f"NMB:{sim_globals.network_data/1e6:.2f} IO:{sim_globals.io_requests}")
                last_t, last_b, last_tx, last_coins = env.now, bc, sim_globals.total_tx, sim_globals.total_coins
                last_infl = infl

    finally:
        # Final Summary
        total_time = env.now
        abt = total_time / bc if bc else 0
        tps_total = sim_globals.total_tx / total_time if total_time > 0 else 0
        infl_final = last_infl
        simulation_time = time.time() - sim_globals.start_time

        print(f"\n[******] End B:{bc}/{blocks_limit or '∞'} abt:{abt:.2f}s tps:{tps_total:.2f} "
              f"infl:{infl_final:.2f}% Diff:{human(diff)} H:{human(th)} "
              f"Tx:{sim_globals.total_tx} C:{human(sim_globals.total_coins)} Pool:{len(sim_globals.pool)} "
              f"NMB:{sim_globals.network_data/1e6:.2f} IO:{sim_globals.io_requests}")
        print(f"Simulation completed in {simulation_time:.2f} real seconds")
        print(f"Simulated blockchain time: {env.now:.2f} seconds")
