import os
import json
import simpy
import random
from simulation.core.node import Node
from simulation.core.miner import Miner
import simulation.globals as sim_globals


def load_latency_bandwidth():
    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go from core/ → simulation/ → root/
    latency_path = os.path.join(base, "config", "network", "latency.json")
    bandwidth_path = os.path.join(base, "config", "network", "bandwith.json")

    with open(latency_path) as f:
        sim_globals.LATENCY = json.load(f)

    with open(bandwidth_path) as f:
        sim_globals.BANDWIDTH = json.load(f)

    print("LATENCY keys loaded:", sim_globals.LATENCY.keys())



def shard_by_latency(nodes, max_latency=100):
    """Group nodes into shards based on inter-region latency."""
    shards = []
    unassigned = set(nodes)

    while unassigned:
        seed = unassigned.pop()
        shard = [seed]
        for n in list(unassigned):
            if sim_globals.LATENCY[seed.region][n.region] <= max_latency:
                shard.append(n)
                unassigned.remove(n)
        for n in shard:
            n.shard_id = len(shards)
        shards.append(shard)

    return shards


def setup_simulation(args, config):
    env = simpy.Environment()
    load_latency_bandwidth()

    regions = list(sim_globals.LATENCY.keys())
    num_nodes = args.nodes if args.nodes is not None else config['simulation']['nodes']
    num_neighbors = args.neighbors if args.neighbors is not None else config['simulation']['neighbors']
    num_miners = args.miners if args.miners is not None else config['simulation']['miners']
    hashrate = args.hashrate if args.hashrate is not None else config['simulation']['hashrate']

    # Create nodes and assign random regions
    nodes = [Node(env, i, region=random.choice(regions)) for i in range(num_nodes)]

    # Shard nodes by latency
    shards_list = shard_by_latency(nodes, max_latency=100)
    print(f"Formed {len(shards_list)} shards")

    # Assign neighbors within each shard
    for shard in shards_list:
        for n in shard:
            n.neighbors = random.sample(
                [x for x in shard if x != n],
                min(num_neighbors, len(shard) - 1)
            )

    # Assign at least one miner per shard, then fill remaining
    miners = []
    for sid, shard in enumerate(shards_list):
        miners.append(Miner(len(miners), hashrate, shard_id=sid))  # one per shard

    for i in range(len(miners), num_miners):
        sid = random.randint(0, len(shards_list) - 1)
        miners.append(Miner(len(miners), hashrate, shard_id=sid))

    # Format shards into dict format
    shards = {
        sid: {
            "nodes": shards_list[sid],
            "miners": [m for m in miners if m.shard_id == sid],
            "chain": []
        }
        for sid in range(len(shards_list))
    }

    return env, shards, miners
