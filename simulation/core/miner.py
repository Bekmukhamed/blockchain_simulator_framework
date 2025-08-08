import random

class Miner:
    def __init__(self, i, h):
        self.id = i       # Miner ID
        self.h = h        # Miner hashrate

    def mine_until(self, bt, difficulty, winners):
        """Simulate whether this miner wins a block within the block time."""
        # Simulate mining delay: expected time = difficulty / hashrate
        delay = random.expovariate(self.h / difficulty)

        if delay <= bt:
            winners.append(self)
