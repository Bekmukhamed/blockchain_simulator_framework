import simulation.globals as sim_globals

class Block:
    def __init__(self, i, tx, dt, blobs=None, shard_id=None, optimized_txs=0):
        self.id = i
        self.tx = tx
        self.dt = dt
        
        # Danksharding extensions (optional, maintains backward compatibility)
        self.blobs = blobs if blobs is not None else []
        self.shard_id = shard_id  # None for regular blocks, shard ID for shard blocks
        self.blob_count = len(self.blobs)
        self.optimized_txs = optimized_txs  # Number of transactions optimized with blobs
        
        # Calculate block size with Danksharding optimizations
        if sim_globals.danksharding_enabled and self.optimized_txs > 0:
            # Optimized transactions are much smaller
            regular_txs = tx - optimized_txs
            regular_size = regular_txs * 256
            optimized_size = optimized_txs * 25  # 90% size reduction (256 -> 25.6 bytes)
            self.size = sim_globals.HEADER_SIZE + regular_size + optimized_size
            
            # Add commitment size (32 bytes per blob commitment)
            if self.blobs:
                self.size += len(self.blobs) * 32
        else:
            # Original size calculation
            self.size = sim_globals.HEADER_SIZE + tx * 256
            
            # Add commitment size for blobs (backward compatibility)
            if self.blobs:
                self.size += len(self.blobs) * 32
