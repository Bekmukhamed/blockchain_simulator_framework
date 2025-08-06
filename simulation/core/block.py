import simulation.globals as sim_globals

class Block:
    def __init__(self, block_id, tx_count, dt, shard_id=None, timestamp=None, tx_list=None, prev_hash=None):
        self.id = block_id                       # Block height or sequential ID
        self.tx = tx_count                       # Number of transactions
        self.dt = dt                             # Delay (block mining time)
        self.shard_id = shard_id                 # Shard that mined this block
        self.timestamp = timestamp               # Simulated time of block mining
        self.tx_list = tx_list or []             # Optional: actual transactions
        self.prev_hash = prev_hash               # Optional: previous block reference

        self.size = sim_globals.HEADER_SIZE + tx_count * 256
