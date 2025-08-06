import random
import time
from simulation.core.block import Block
from simulation.core.utils import (
    pool, human, YEAR, network_data, io_requests,
    total_tx, total_coins
)

def coord_sharded(env, shards, bt, diff0, blocks_limit, blk_sz, print_int, dbg,
                  wallets, tx_per_wallet, init_reward, halving_interval, start_time,
                  use_fees=False, wallet_balances=None, fee_per_tx=0.1):

    global network_data, io_requests, total_tx, total_coins, pool

    max_halvings = 35
    blocks_global = 0

    last_t = last_b = last_tx = last_coins = 0
    last_infl = 0

    # Per-shard stats
    shard_stats = {
        sid: {
            "bc": 0, "lt": 0, "ba": 0, "la": 0,
            "reward": init_reward, "halvings": 0,
            "diff": diff0 if diff0 else bt * sum(m.h for m in shard["miners"]),
            "hashrate": sum(m.h for m in shard["miners"]),
        }
        for sid, shard in shards.items()
    }

    while blocks_global < blocks_limit:
        for sid, shard in shards.items():
            stats = shard_stats[sid]

            if stats["bc"] >= blocks_limit // len(shards):
                continue

            # Difficulty adjustment
            if diff0 is None and stats["ba"] >= 2016:
                elapsed = env.now - stats["la"]
                actual_avg = elapsed / stats["ba"] if stats["ba"] else bt
                stats["diff"] *= bt / actual_avg if actual_avg > 0 else 1
                stats["la"] = env.now
                stats["ba"] = 0
                if dbg:
                    print(f"[{env.now:.2f}] Shard {sid} Diff:{human(stats['diff'])} H:{human(stats['hashrate'])} "
                          f"Tx:{total_tx} C:{human(total_coins)} Pool:{len(pool)} "
                          f"infl:N/A NMB:{network_data/1e6:.2f} IO:{io_requests}")

            # Mining
            ev = env.event()
            for m in shard["miners"]:
                env.process(m.mine(env, stats["diff"], ev))
            winner = yield ev

            dt = env.now - stats["lt"]
            stats["lt"] = env.now
            stats["bc"] += 1
            stats["ba"] += 1
            blocks_global += 1

            # Transactions
            avail = len(pool)
            take = min(avail, blk_sz)
            fee = 0
            for _ in range(take):
                _, tx = pool.pop(0)
                if use_fees:
                    fee += tx.get("fee", 0)

            txs = take + 1
            b = Block(stats["bc"], txs, dt, shard_id=sid, timestamp=env.now)
            shard["chain"].append(b)
            total_tx += txs

            if stats["halvings"] < max_halvings:
                total_coins += stats["reward"]

            if halving_interval > 0 and stats["bc"] % halving_interval == 0:
                stats["halvings"] += 1
                stats["reward"] = stats["reward"] / 2 if stats["halvings"] < max_halvings else 0

            if wallet_balances:
                wallet_balances[winner.id] = wallet_balances.get(winner.id, 0.0) + stats["reward"] + fee

            env.process(random.choice(shard["nodes"]).receive(b))

            if dbg:
                print(f"[{env.now:.2f}] Shard {sid} B{b.id} by M{winner.id} dt:{b.dt:.2f}s "
                      f"Diff:{human(stats['diff'])} H:{human(stats['hashrate'])} "
                      f"Tx:{total_tx} C:{human(total_coins)} Pool:{len(pool)} "
                      f"infl:N/A NMB:{network_data/1e6:.2f} IO:{io_requests}")

        # Global logging every `print_int` blocks
        if print_int > 0 and blocks_global % print_int == 0:
            pct = (blocks_global / blocks_limit) * 100
            ti = env.now - last_t
            dtx = total_tx - last_tx
            dcoins = total_coins - last_coins
            abt = ti / (blocks_global - last_b) if (blocks_global - last_b) else 0
            tps = dtx / ti if ti > 0 else 0
            infl = (dcoins / last_coins) * (YEAR / ti) * 100 if last_coins > 0 else 0
            eta = (blocks_limit - blocks_global) * abt
            avg_diff = sum(stats["diff"] for stats in shard_stats.values()) / len(shards)
            avg_hash = sum(stats["hashrate"] for stats in shard_stats.values()) / len(shards)

            print(f"[{env.now:.2f}] Sum B:{blocks_global}/{blocks_limit} {pct:.1f}% abt:{abt:.2f}s "
                f"tps:{tps:.2f} infl:{infl:.2f}% ETA:{eta:.2f}s "
                f"Diff:{human(avg_diff)} H:{human(avg_hash)} Tx:{total_tx} "
                f"C:{human(total_coins)} Pool:{len(pool)} "
                f"NMB:{network_data/1e6:.2f} IO:{io_requests}")

            last_t, last_b, last_tx, last_coins = env.now, blocks_global, total_tx, total_coins
            last_infl = infl

    # Final summary
    sim_time = time.time() - start_time
    total_time = env.now
    abt = total_time / blocks_global if blocks_global else 0
    tps_total = total_tx / total_time if total_time > 0 else 0
    avg_diff = sum(stats["diff"] for stats in shard_stats.values()) / len(shards)
    avg_hash = sum(stats["hashrate"] for stats in shard_stats.values()) / len(shards)

    print(f"\n[******] End B:{blocks_global}/{blocks_limit} 100.0% abt:{abt:.2f}s "
          f"tps:{tps_total:.2f} infl:{last_infl:.2f}% Diff:{avg_diff/1e9:.1f}B H:{avg_hash/1e6:.0f}M "
          f"Tx:{total_tx} C:{total_coins/1e6:.1f}M Pool:{len(pool)} "
          f"NMB:{io_requests/1024:.2f} IO:{network_data}")
    print(f"Simulated blockchain time: {env.now:.2f}s | Wall time: {sim_time:.2f}s")

    if wallet_balances:
        print("\n[***] Final Wallet Balances:")
        for wid in sorted(wallet_balances):
            print(f"Wallet {wid}: {wallet_balances[wid]:.2f}")
