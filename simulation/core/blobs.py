import random
import hashlib

class Blob:
    def __init__(self, blob_id, data, commitment=None):
        self.blob_id = blob_id
        self.data = data
        self.size = len(data)
        self.commitment = commitment or self._generate_commitment()
        
    def _generate_commitment(self):
        return hashlib.sha256(self.data.encode() if isinstance(self.data, str) else self.data).hexdigest()

class LightweightTransaction:
    def __init__(self, tx_id, blob_commitment=None, reduced_size_factor=0.1):
        self.tx_id = tx_id
        self.blob_commitment = blob_commitment  # Reference to blob data
        self.reduced_size_factor = reduced_size_factor  # How much smaller the tx becomes
        self.is_optimized = blob_commitment is not None

class ShardBlock:
    def __init__(self, shard_id, blobs, block_time):
        self.shard_id = shard_id
        self.blobs = blobs if blobs else []
        self.block_time = block_time
        self.blob_count = len(self.blobs)
        self.total_blob_size = sum(blob.size for blob in self.blobs)

class DankShardConfig:
    def __init__(self):
        self.enabled = False  # Start disabled to maintain compatibility
        self.max_blobs_per_block = 6  # EIP-4844 target
        self.max_blob_size = 128 * 1024  # 128KB per blob
        self.blob_base_fee = 1  # Base fee for blob inclusion
        self.shard_count = 64  # Number of shards in the network
        
        # Performance optimization settings
        self.tx_optimization_rate = 0.7  # 70% of transactions can be optimized
        self.tx_size_reduction = 0.9    # Optimized transactions are 90% smaller
        self.blob_processing_speedup = 2.0  # Blob processing is 2x faster than normal tx

# Global Danksharding configuration
danksharding_config = DankShardConfig()
