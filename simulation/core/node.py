import simulation.globals as sim_globals
import random
import json
import os
from simulation.utils.distance import calculate_distance
from ..network.message import BlockMessage
from ..network.latency import calculate_network_latency, calculate_transmission_time

def load_locations():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'network', 'locations.json')
    with open(config_path, 'r') as f:
        return json.load(f)

_locations_data = load_locations()

class Node:
    def __init__(self, env, i, location=None, bandwidth_mbps=None, blocktime=600):
        self.env = env
        self.id = i
        self.blocks = set()
        self.neighbors = []
        self.blocktime = blocktime
        self._delay_cache = {}  # Cache for network delays
    
        if location is None:
            location = random.choice(list(_locations_data.keys()))
        self.location = location
        self.coordinates = (_locations_data[location]["latitude"], _locations_data[location]["longitude"])
        
        if bandwidth_mbps is None:
            bandwidth_mbps = random.uniform(50, 200)
        self.bandwidth_mbps = bandwidth_mbps
        self.bandwidth_bps = bandwidth_mbps * 1024 * 1024  # b/s
    
    def _calculate_network_delay(self, target_node, message_size):

        if target_node is None:
            return 0.001
            
        cache_key = (target_node.id, message_size)
        if cache_key in self._delay_cache:
            return self._delay_cache[cache_key]
            
        latency = calculate_network_latency(self, target_node)
        transmission_time = calculate_transmission_time(message_size, self.bandwidth_bps)
        
        total_delay = latency + transmission_time
        
        max_network_delay = min(self.blocktime * 0.01, 5.0)  # 1% of blocktime or 5 seconds max
        if total_delay > max_network_delay:
            total_delay = max_network_delay
            
        if self.blocktime < 300:
            total_delay = total_delay * 0.1
        
        # Ensure delay is always positive (Danksharding can cause timing issues)
        total_delay = max(0.001, total_delay)
            
        self._delay_cache[cache_key] = total_delay
        return total_delay
    
    def send_message(self, message, target_node):
        total_delay = self._calculate_network_delay(target_node, message.size)
        
        # Network metrics
        sim_globals.io_requests += 1
        sim_globals.network_data += message.size
        
        yield self.env.timeout(total_delay)
        return message
    
    def receive(self, b, sender_node=None):

        yield self.env.timeout(0)
        
        # Danksharding: Handle blocks with blobs
        if hasattr(b, 'blobs') and b.blobs:
            self._process_blobs(b)
        
        if b.id in self.blocks:
            return
            
        self.blocks.add(b.id)
        
        if sender_node is not None:
            block_msg = BlockMessage(sender_node.id, b)
            sim_globals.io_requests += 1
            sim_globals.network_data += block_msg.size
        else:
            sim_globals.io_requests += 1
            sim_globals.network_data += b.size
        
        for neighbor in self.neighbors:
            if sender_node is not None:
                network_delay = self._calculate_network_delay(neighbor, b.size)
                self.env.process(self._delayed_propagation(neighbor, b, network_delay))
            else:
            
                self.env.process(neighbor.receive(b, sender_node=self))
    
    def _delayed_propagation(self, target_node, block, delay):
        # Ensure delay is always positive to prevent SimPy errors
        safe_delay = max(0.001, delay)  # Minimum 1ms delay
        yield self.env.timeout(safe_delay)
        yield self.env.process(target_node.receive(block, sender_node=self))
    
    def _process_blobs(self, block):
        """Process blobs in a received block for Danksharding"""
        if not sim_globals.danksharding_enabled:
            return 0
            
        blob_count = len(block.blobs)
        total_blob_size = sum(blob.size for blob in block.blobs)
        
        # Update global blob metrics
        sim_globals.total_blobs_processed += blob_count
        sim_globals.total_blob_data += total_blob_size
        
        # Optimized blob processing: much faster than regular transactions
        # Since blob data is separate from execution, processing is parallelizable
        verification_delay = blob_count * 0.0001  # 0.1ms per blob (10x faster than before)
        
        # If block has optimized transactions, they process faster too
        if hasattr(block, 'optimized_txs') and block.optimized_txs > 0:
            # Optimized transactions process 5x faster
            verification_delay += block.optimized_txs * 0.0002  # 0.2ms per optimized tx
        
        return verification_delay
    
    def get_network_delay_to(self, target_node, message_size):
        if target_node is None:
            return 0.001
        return self._calculate_network_delay(target_node, message_size)
    
    def get_network_info(self):
        return {
            'id': self.id,
            'location': self.location,
            'coordinates': self.coordinates,
            'bandwidth_mbps': self.bandwidth_mbps
        }
