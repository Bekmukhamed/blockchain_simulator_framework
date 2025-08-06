import time
from sortedcontainers import SortedList

# Blockchain-wide constants
HEADER_SIZE = 1024         # Block header size in bytes
YEAR = 365 * 24 * 3600     # Seconds in one year

# Global statistics (reset per simulation)
network_data = 0           # Total bytes transferred
io_requests = 0            # Number of inter-node message sends
total_tx = 0               # Total transactions included
total_coins = 0            # Total coins minted
start_time = time.time()   # Simulation wall clock

# Global transaction pool (sorted by priority/fee/etc.)
pool = SortedList(key=lambda x: -x[0])  # e.g., (priority, tx)

# Region-based network data (to be populated in main)
LATENCY = {}               # region -> region -> ms latency
BANDWIDTH = {}             # region -> Mbps

# Optional: Wallet balances if fee simulation is enabled
wallet_balances = {}
FEE_PER_TX = 0.1
