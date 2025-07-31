import simulation.globals as sim_globals
import random
import json
import os
from simulation.utils.distance import calculate_distance
from ..network.message import AnnouncementMessage, RequestMessage, BlockMessage
from ..network.latency import calculate_network_latency, calculate_transmission_time

def load_locations():
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'network', 'locations.json')
    with open(config_path, 'r') as f:
        return json.load(f)

locations_data = load_locations()

class Node:
    def __init__(self, env, i, location=None, bandwidth_mbps=None, blocktime=600):
        self.env = env
        self.id = i
        self.blocks = set()
        self.neighbors = []
        self.blocktime = blocktime
    
        if location is None:
            location = random.choice(list(locations_data.keys()))
        self.location = location
        self.coordinates = (locations_data[location]["latitude"], locations_data[location]["longitude"])
        
        if bandwidth_mbps is None:
            bandwidth_mbps = random.uniform(50, 200)
        self.bandwidth_mbps = bandwidth_mbps
        self.bandwidth_bps = bandwidth_mbps * 1024 * 1024  # b/s
    
    def send_message(self, message, target_node):
        if target_node is not None:
            latency = calculate_network_latency(self, target_node)
            transmission_time = calculate_transmission_time(message.size, self.bandwidth_bps)
            
            total_delay = latency + transmission_time
            max_network_delay = self.blocktime * 0.5  # 50% blocktime
            if total_delay > max_network_delay:
                total_delay = max_network_delay
                
        else:
            total_delay = 0.001
        
        # Network metrics
        sim_globals.io_requests += 1
        sim_globals.network_data += message.size
        
        yield self.env.timeout(total_delay)
        return message
    
    def receive(self, b, sender_node=None):
        if sender_node is not None:
            announce_msg = AnnouncementMessage(sender_node.id, b.id)
            yield self.env.process(self.send_message(announce_msg, None))

            request_msg = RequestMessage(self.id, b.id)
            yield self.env.process(self.send_message(request_msg, sender_node))
        
            block_msg = BlockMessage(sender_node.id, b)
            yield self.env.process(self.send_message(block_msg, None))
        else:

            total_delay = 0.001
            yield self.env.timeout(total_delay)
        
        if b.id in self.blocks:
            return
        self.blocks.add(b.id)
        
        for n in self.neighbors:
            self.env.process(n.receive(b, sender_node=self))
