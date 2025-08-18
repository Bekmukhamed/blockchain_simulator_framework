import random
import simulation.globals as sim_globals

class Miner:
    def __init__(self, i, h):
        self.id = i
        self.h = h

    def mine(self, env, d, ev):
        t = random.expovariate(self.h / d)
        tm = env.timeout(t)
        r = yield env.any_of([tm, ev])
        if tm in r and not ev.triggered:
            ev.succeed(self)
        yield ev
    
    def create_blob_data(self, size=None):
        """
        Create sample blob data for testing Danksharding.
        In practice, this would be actual application data.
        """
        if not sim_globals.danksharding_enabled:
            return None
            
        if size is None:
            size = random.randint(1024, 32768)  # Random size between 1KB and 32KB
        
        # Generate random data for simulation
        return b'x' * size
    
    def should_include_blobs(self):
        """Determine if this miner should include blobs in the next block"""
        if not sim_globals.danksharding_enabled:
            return False
        # 80% chance to include blobs for better optimization (was 30%)
        return random.random() < 0.8
