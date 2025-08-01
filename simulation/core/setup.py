import simpy
import random
from simulation.core.node import Node
from simulation.core.miner import Miner

def setup_simulation(args):
    env = simpy.Environment()

    nodes = [Node(env, i) for i in range(args.nodes)]
    for n in nodes:
        n.neighbors = random.sample([x for x in nodes if x != n], args.neighbors)

    miners_list = [Miner(i, args.hashrate) for i in range(args.miners)]
    return env, nodes, miners_list
