import random
from simulation.utils.distance import calculate_distance

def calculate_network_latency(node1, node2):
    base_latency = 0.001

    distance_km = calculate_distance(node1, node2)

    light_speed_fiber_km_s = 200000
    propagation_delay = distance_km / light_speed_fiber_km_s  # seconds

    jitter = random.uniform(0, 0.01)
    
    congestion_factor = random.uniform(1.0, 3.0)
    
    total_latency = (base_latency + propagation_delay + jitter) * congestion_factor
    
    return max(total_latency, 0.001)

def calculate_transmission_time(block_size, bandwidth_bps):
    tcp_overhead = 1.2
    effective_size = block_size * tcp_overhead
    
    transmission_time = effective_size / bandwidth_bps
    
    variation = random.uniform(0.8, 1.2)
    return transmission_time * variation