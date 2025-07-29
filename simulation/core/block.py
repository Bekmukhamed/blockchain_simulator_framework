HEADER_SIZE = 1024

class Block:
    def __init__(self, i, tx, dt):
        self.id = i
        self.tx = tx
        self.size = HEADER_SIZE + tx * 256
        self.dt = dt