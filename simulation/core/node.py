import simulation.globals as sim_globals


class Node:
    def __init__(self, env, i):
        self.env = env
        self.id = i
        self.blocks = set()
        self.neighbors = []
    
    def receive(self, b):
        yield self.env.timeout(0)
        
        if b.id in self.blocks:
            return
        self.blocks.add(b.id)
        
        for n in self.neighbors:
            sim_globals.io_requests += 1
            sim_globals.network_data += b.size
            self.env.process(n.receive(b))
