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
        yield self.env.timeout(delay)
        yield self.env.process(target_node.receive(block, sender_node=self))
    
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
