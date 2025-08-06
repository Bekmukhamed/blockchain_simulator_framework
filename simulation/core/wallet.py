import random
import simulation.globals as sim_globals

def wallet(env, wid, count, interval, use_fees=False, region=None, shard_id=None):
    # Initialize balance
    if use_fees:
        sim_globals.wallet_balances[wid] = 6000  # satoshis

    for _ in range(count):
        yield env.timeout(interval)

        tx_size = random.randint(200, 400)         # bytes
        fee_rate = random.uniform(1.0, 10.0)        # sat/vB
        fee = int(fee_rate * tx_size)

        if use_fees:
            if sim_globals.wallet_balances.get(wid, 0) < fee:
                continue
            sim_globals.wallet_balances[wid] -= fee

        tx = {
            "wid": wid,
            "time": env.now,
            "size": tx_size,
            "fee": fee,
            "rate": fee_rate,
            "region": region,
            "shard_id": shard_id,
        }

        sim_globals.pool.add((fee_rate, tx))
