from simulation.core.utils import pool

def wallet(env, wid, count, interval):
    for _ in range(count):
        yield env.timeout(interval)
        pool.append((wid, env.now))
