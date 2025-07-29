import simulation.globals as sim_globals


# Wallet sends transactions into pool
def wallet(env, wid, count, interval):
    for _ in range(count):
        yield env.timeout(interval)
        sim_globals.pool.append((wid, env.now))
