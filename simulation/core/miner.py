import random

class Miner:
    def __init__(self, i, h, shard_id=None):
        self.id = i
        self.h = h
        self.shard_id = shard_id
        self.mined_blocks = 0

    def mine(self, env, difficulty, event):
        # Mining delay ~ Exponential(h / d)
        t = random.expovariate(self.h / difficulty)
        timeout_event = env.timeout(t)
        result = yield env.any_of([timeout_event, event])

        if timeout_event in result and not event.triggered:
            event.succeed(self)
            self.mined_blocks += 1  # Track mining success

        yield event
