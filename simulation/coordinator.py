import random
import time
import simulation.globals as sim_globals
from .core.block import Block
from .utils.formatter import human

# Import parallel processing for Danksharding
try:
    from .core.parallel_shards import parallel_processor
    PARALLEL_AVAILABLE = True
except ImportError:
    PARALLEL_AVAILABLE = False


def coord(env, nodes, miners, bt, diff0, blocks_limit, blk_sz, print_int, dbg,
          wallets, tx_per_wallet, init_reward, halving_interval):
    bc = lt = la = ba = 0
    last_t = last_b = last_tx = last_coins = 0
    last_infl = 0 

    diff = diff0 if diff0 is not None else bt * sum(m.h for m in miners)
    th = sum(m.h for m in miners)
    
    initial_coins = sim_globals.total_coins

    reward = init_reward
    halvings = 0
    max_halvings = 35

    has_tx = tx_per_wallet > 0
    total_needed = wallets * tx_per_wallet if has_tx else None
    pool_processed = 0

    try:
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
                        f"Tx:{sim_globals.total_tx} C:{human(sim_globals.total_coins)} Pool:{len(sim_globals.pool)} "
                        f"infl:N/A NMB:{sim_globals.network_data/1e6:.2f} IO:{sim_globals.io_requests}")

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
                avail = len(sim_globals.pool)
                take = min(avail, blk_sz)
                
                # Danksharding PARALLEL optimization: Process transactions across shards
                if sim_globals.danksharding_enabled and PARALLEL_AVAILABLE and take > 10:
                    # Use parallel shard processing for any meaningful transaction set
                    parallel_result = parallel_processor.parallel_block_processing(
                        sim_globals.pool[:take], 
                        take,
                        num_workers=min(8, parallel_processor.num_shards)  # Use configured shards
                    )
                    
                    # Remove processed transactions efficiently
                    del sim_globals.pool[:parallel_result.get('total_processed', take)]
                    pool_processed += parallel_result.get('total_processed', take)
                    
                    # Record parallel processing speedup
                    if 'parallel_speedup' in parallel_result:
                        sim_globals.parallel_speedup = parallel_result['parallel_speedup']
                
                elif sim_globals.danksharding_enabled:
                    # Small batch optimization for small transaction sets
                    if take > 0:
                        batch_size = min(take, 1000)
                        if batch_size > 0:
                            for _ in range(0, take, batch_size):
                                batch_take = min(batch_size, take - _)
                                del sim_globals.pool[:batch_take]
                        pool_processed += take
                else:
                    # Original slow processing
                    pool_processed += take
                    for _ in range(take):
                        sim_globals.pool.pop(0)
                
                txs = take + 1
            else:
                txs = 1

            # Create block with Danksharding optimizations
            optimized_txs = 0
            blobs = []
            
            if sim_globals.danksharding_enabled and txs > 1:
                from .core.blobs import Blob, danksharding_config
                
                # Calculate how many transactions can be optimized
                optimized_txs = int(txs * danksharding_config.tx_optimization_rate)
                
                # Create blobs for heavy transaction data
                if winner.should_include_blobs() and optimized_txs > 0:
                    blob_count = min(
                        random.randint(1, danksharding_config.max_blobs_per_block),
                        (optimized_txs // 100) + 1  # Roughly 1 blob per 100 optimized txs
                    )
                    
                    for i in range(blob_count):
                        # Simulate transaction data being moved to blobs
                        blob_data = winner.create_blob_data(size=optimized_txs * 50)  # Data from optimized txs
                        if blob_data:
                            blob = Blob(f"txdata_{bc}_{i}", blob_data)
                            blobs.append(blob)
            
            b = Block(bc, txs, dt, blobs=blobs, optimized_txs=optimized_txs)
            
            sim_globals.total_tx += txs

            # Mint reward and halving
            if halvings < max_halvings:
                sim_globals.total_coins += reward
            if halving_interval > 0 and bc % halving_interval == 0 and halvings < max_halvings:
                halvings += 1
                reward = reward / 2 if halvings < max_halvings else 0

            env.process(random.choice(nodes).receive(b, sender_node=None))

            # Logging / summary
            if dbg:
                print(f"[{env.now:.2f}] B{b.id} by M{winner.id} dt:{b.dt:.2f}s "
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
        # Final summary
        total_time = env.now
        abt = total_time / bc if bc else 0
        tps_total = sim_globals.total_tx / total_time if total_time > 0 else 0
        infl_final = last_infl
        simulation_time = time.time() - sim_globals.start_time
        if blocks_limit:
            print(f"[******] End B:{bc}/{blocks_limit} 100.0% abt:{abt:.2f}s tps:{tps_total:.2f} "
                f"infl:{infl_final:.2f}% Diff:{human(diff)} H:{human(th)} "
                f"Tx:{sim_globals.total_tx} C:{human(sim_globals.total_coins)} Pool:{len(sim_globals.pool)} "
                f"NMB:{sim_globals.network_data/1e6:.2f} IO:{sim_globals.io_requests}")
            print(f"\nSimulation completed in {simulation_time:.2f} seconds")
            print(f"Simulated blockchain time: {env.now:.2f} seconds")
        else:
            print(f"[******] End B:{bc} abt:{abt:.2f}s tps:{tps_total:.2f} "
                f"infl:{infl_final:.2f}% Diff:{human(diff)} H:{human(th)} "
                f"Tx:{sim_globals.total_tx} C:{human(sim_globals.total_coins)} Pool:{len(sim_globals.pool)} "
                f"NMB:{sim_globals.network_data/1e6:.2f} IO:{sim_globals.io_requests}")
            print(f"\nSimulation completed in {simulation_time:.2f} seconds")
            print(f"Simulated blockchain time: {env.now:.2f} seconds")
