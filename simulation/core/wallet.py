import random
import simulation.globals as sim_globals

def wallet(env, wid, count, interval, use_fees=False):
    # Initialize balance if fee logic is on
    if use_fees:
        sim_globals.wallet_balances[wid] = 6000  # starting balance in satoshis

    for _ in range(count):
        yield env.timeout(interval)

        # Simulate transaction size and fee rate
        tx_size = random.randint(200, 400)  # in bytes
        fee_rate = random.uniform(1.0, 10.0)  # sat/vB
        fee = int(fee_rate * tx_size)

        if use_fees:
            if sim_globals.wallet_balances.get(wid, 0) < fee:
                continue  # Skip if insufficient balance
            sim_globals.wallet_balances[wid] -= fee

        # Construct transaction entry
        tx = {
            "wid": wid,
            "time": env.now,
            "size": tx_size,
            "fee": fee,
            "rate": fee_rate,
        }

        # Insert into sorted mempool (descending by fee/vbyte)
        sim_globals.pool.add((fee_rate, tx))
