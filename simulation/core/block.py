import simulation.globals as sim_globals

class BlockShard:
    def __init__(self, miner_id, tx_count):
        self.miner_id = miner_id
        self.tx_count = tx_count
        self.size = sim_globals.HEADER_SIZE + tx_count * 256  # Assume 256 bytes per tx

class Block:
    def __init__(self, block_id, shards, dt, leader_id):
        self.id = block_id                      # Block number
        self.shards = shards                    # List of BlockShard
        self.dt = dt                            # Time duration since last block
        self.leader_id = leader_id              # Miner ID who finalized this block
        self.tx = sum(shard.tx_count for shard in shards)  # Total txs
        self.size = sim_globals.HEADER_SIZE + self.tx * 256
