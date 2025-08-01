import random
class Miner:
    def __init__(self, i, h):
        self.id = i
        self.h = h

    def mine(self, env, d, ev):
        t = random.expovariate(self.h / d)
        tm = env.timeout(t)
        r = yield env.any_of([tm, ev])
        if tm in r and not ev.triggered:
            ev.succeed(self)
        yield ev
