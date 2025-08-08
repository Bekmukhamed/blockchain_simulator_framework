import simulation.globals as sim_globals
import random

def wallet(env, wid, count, interval, fee_enabled=False, min_fee=0.1, max_fee=1.0):
    for _ in range(count):
        yield env.timeout(interval)
        tx = {
            "sender": wid,
            "timestamp": env.now,
        }
        if fee_enabled:
            tx["fee"] = round(random.uniform(min_fee, max_fee), 3)
        sim_globals.pool.append((wid, tx))
