import simulation.globals as sim_globals

class Block:
    def __init__(self, i, tx, dt):
        self.id = i
        self.tx = tx
        self.size = sim_globals.HEADER_SIZE + tx * 256
        self.dt = dt
