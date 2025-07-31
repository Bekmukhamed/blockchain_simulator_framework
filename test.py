#!/usr/bin/env python3

import sys
import os
import json

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from simulation.network.latency import calculate_network_latency, calculate_transmission_time

def test_transmission_times():
    print("Transmission Time================")
    
    bandwidths = [50, 100, 200]
    sizes = [37, 250, 1000000]  # announcement, transaction, 1MB block
    size_names = ["Announcement", "Transaction", "1MB Block"]
    
    print("Message Type ==== Bandwidth (Mbps) ======= Time (seconds) ===== Time (ms)")
    print("====================================")
    
    for i, size in enumerate(sizes):
        for bandwidth_mbps in bandwidths:
            bandwidth_bps = bandwidth_mbps * 1024 * 1024
            transmission_time = calculate_transmission_time(size, bandwidth_bps)
            print(f"{size_names[i]:<12} | {bandwidth_mbps:>12} | {transmission_time:>10.6f} | {transmission_time*1000:>7.2f}")
    
    print()

def test_latency_simple():
    print("Network Latency==================")
    
    class Node:
        def __init__(self, lat, lon):
            self.coordinates = (lat, lon)
    
    node_ny = Node(40.7128, -74.0060)
    node_london = Node(51.5074, -0.1278)
    node_tokyo = Node(35.6828, 139.7595)

    pairs = [
        ("New York", node_ny, "London", node_london),
        ("New York", node_ny, "Tokyo", node_tokyo),
        ("London", node_london, "Tokyo", node_tokyo)
    ]
    
    for i in range(5):
        print(f"{i + 1}:")

        for name1, node1, name2, node2 in pairs:
            latency = calculate_network_latency(node1, node2)
            print(f"  {name1} to {name2}: {latency:.6f} seconds ({latency*1000:.2f} ms)")
    
    print()

if __name__ == "__main__":
    test_transmission_times() 
    test_latency_simple()