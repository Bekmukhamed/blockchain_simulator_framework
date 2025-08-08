class NetworkMessage:
    
    def __init__(self, msg_type, sender_id, data=None):
        self.msg_type = msg_type
        self.sender_id = sender_id
        self.data = data
        self.size = self._calculate_size()
    
    def _calculate_size(self):
        sizes = {
            'announce': 37,     # I have a new block message 36 bytes hash + 1 byte type
            'request': 37,      # Send request message for block
            'block': getattr(self.data, 'size', 1000000),  # Block sending
            'transaction': 250, # Transaction
            'peers': 30,        # Address sharing
            'ping': 8,          # Connection test
            'pong': 8           # Ping response
        }
        return sizes.get(self.msg_type, 100)  # Default 100 bytes

class AnnouncementMessage(NetworkMessage):    
    def __init__(self, sender_id, block_id):
        super().__init__('announce', sender_id)
        self.block_id = block_id
        self.size = 37

class RequestMessage(NetworkMessage):
    def __init__(self, sender_id, block_id):
        super().__init__('request', sender_id)
        self.block_id = block_id
        self.size = 37

class BlockMessage(NetworkMessage):
    def __init__(self, sender_id, block):
        super().__init__('block', sender_id, block)
        self.block = block
        self.size = block.size
