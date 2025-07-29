<<<<<<< HEAD
from simulation.core.utils import pool

def wallet(env, wid, count, interval):
    for _ in range(count):
        yield env.timeout(interval)
        pool.append((wid, env.now))
=======
import simulation.globals as sim_globals


# Wallet sends transactions into pool
def wallet(env, wid, count, interval):
    for _ in range(count):
        yield env.timeout(interval)
        sim_globals.pool.append((wid, env.now))
>>>>>>> 54adcc3f4b790c924bff49b0e700965b2eef3270
