import simulation.globals as sim_globals
import simpy

class Node:
    def __init__(self, env, i, region=None):
        self.env = env
        self.id = i
        self.region = region      # e.g., "US", "EU", "Asia" or None for flat mode
        self.blocks = set()
        self.neighbors = []       # Filled later
        self.shard_id = None      # Assigned in sharding

    def receive(self, b, sender_node=None, flat=False):
        if b.id in self.blocks:
            return self.env.timeout(0)  # dummy yield

        self.blocks.add(b.id)

        events = []
        for neighbor in self.neighbors:
            sim_globals.io_requests += 1
            sim_globals.network_data += b.size

            if flat:
                delay = 0
            else:
                # Must have sender and neighbor regions defined
                if self.region is None or neighbor.region is None:
                    raise ValueError("Region must be defined for latency-based simulation.")

                latency_ms = sim_globals.LATENCY[self.region][neighbor.region]
                latency_sec = latency_ms / 1000.0
                bandwidth_mbps = sim_globals.BANDWIDTH[self.region]
                tx_bits = b.size * 8
                bandwidth_delay = tx_bits / (bandwidth_mbps * 1e6)

                delay = latency_sec + bandwidth_delay

            events.append(self.env.process(self.propagate(neighbor, b, delay, flat)))

        yield simpy.events.AllOf(self.env, events)

    def propagate(self, neighbor, b, delay, flat=False):
        yield self.env.timeout(delay)
        yield self.env.process(neighbor.receive(b, sender_node=self, flat=flat))
