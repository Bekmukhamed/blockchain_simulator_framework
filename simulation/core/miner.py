import random

<<<<<<< HEAD
=======

>>>>>>> 54adcc3f4b790c924bff49b0e700965b2eef3270
class Miner:
    def __init__(self, i, h):
        self.id = i
        self.h = h
<<<<<<< HEAD
=======
    
>>>>>>> 54adcc3f4b790c924bff49b0e700965b2eef3270
    def mine(self, env, d, ev):
        t = random.expovariate(self.h / d)
        tm = env.timeout(t)
        r = yield env.any_of([tm, ev])
        if tm in r and not ev.triggered:
            ev.succeed(self)
<<<<<<< HEAD
        yield ev
=======
        yield ev
>>>>>>> 54adcc3f4b790c924bff49b0e700965b2eef3270
