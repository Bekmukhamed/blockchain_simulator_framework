import random
from simulation.utils.distance import calculate_distance

_distance_cache = {}

def calculate_network_latency(node1, node2):
    cache_key = (node1.id, node2.id) if node1.id < node2.id else (node2.id, node1.id)
    
    if cache_key not in _distance_cache:
        distance_km = calculate_distance(node1, node2)
        _distance_cache[cache_key] = distance_km
    else:
        distance_km = _distance_cache[cache_key]

    
    base_latency = 0.001
    light_speed_fiber_km_s = 200000
    propagation_delay = distance_km / light_speed_fiber_km_s
    
    jitter = random.uniform(0, 0.002)  # 0-2m
    
    congestion_factor = random.uniform(1.0, 1.5)  # More stable network
    
    total_latency = (base_latency + propagation_delay + jitter) * congestion_factor
    
    return max(total_latency, 0.001)

def calculate_transmission_time(block_size, bandwidth_bps):
    tcp_overhead = 1.1
    effective_size = block_size * tcp_overhead
    
    transmission_time = effective_size / bandwidth_bps
    
    variation = random.uniform(0.9, 1.1)
    return transmission_time * variation