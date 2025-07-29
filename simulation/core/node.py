from simulation.core.utils import pool, io_requests, network_data

class Node:
    def __init__(self, env, i):
        self.env = env; self.id = i; self.blocks = set(); self.neighbors = []
    def receive(self, b):
        yield self.env.timeout(0)
        global network_data, io_requests
        if b.id in self.blocks:
            return
        self.blocks.add(b.id)
        for n in self.neighbors:
            io_requests += 1
            network_data += b.size
            self.env.process(n.receive(b))